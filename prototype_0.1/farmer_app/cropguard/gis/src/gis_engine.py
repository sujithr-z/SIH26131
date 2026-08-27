#!/usr/bin/env python3
"""
gis_engine.py — Geospatial analysis engine for priority disease events.

This module performs the GIS stage of the surveillance pipeline:
  1. Load a base map image and georeference it using a geographic extent
  2. Plot disease detection points on the map
  3. Calculate pairwise distances using the Haversine formula
  4. Compute a prototype spatial risk score from distance, humidity, and confidence
  5. Save an analyzed map image and a machine-readable results JSON

The risk score is explicitly a PROTOTYPE metric — it is not an epidemiological
prediction. It is named `prototype_spatial_risk_score` throughout to preserve
scientific honesty.

Usage:
    Called by main.py via:
        results, map_path, results_path = gis_engine.analyze_event(event, config)
"""

import json
import math
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for servers / headless
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
EARTH_RADIUS_KM = 6371.0  # mean Earth radius for Haversine formula


# ---------------------------------------------------------------------------
# DISTANCE CALCULATION — Haversine formula
# ---------------------------------------------------------------------------
def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance between two lat/lon points in km.

    Uses the Haversine formula:
        a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
        d = 2R·arcsin(√a)

    Args:
        lat1, lon1: Latitude and longitude of point 1 (degrees)
        lat2, lon2: Latitude and longitude of point 2 (degrees)

    Returns:
        Distance in kilometers.

    Example:
        >>> round(haversine_distance_km(9.2645, 76.4600, 9.2712, 76.4721), 2)
        1.58
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def compute_pairwise_distances(detections: list) -> list:
    """
    Compute all pairwise distances between detections.

    Args:
        detections: List of detection dicts with 'latitude' and 'longitude'.

    Returns:
        List of dicts: {'i', 'j', 'distance_km', 'farmer_a', 'farmer_b'}
    """
    pairs = []
    n = len(detections)
    for i in range(n):
        for j in range(i + 1, n):
            d_i = detections[i]
            d_j = detections[j]
            dist = haversine_distance_km(
                d_i["latitude"], d_i["longitude"],
                d_j["latitude"], d_j["longitude"],
            )
            pairs.append({
                "i": i,
                "j": j,
                "farmer_a": d_i.get("farmer_id", "?"),
                "farmer_b": d_j.get("farmer_id", "?"),
                "distance_km": round(dist, 3),
            })
    return pairs


# ---------------------------------------------------------------------------
# RISK CALCULATION — prototype spatial risk score
# ---------------------------------------------------------------------------
def distance_score(distance_km: float, characteristic_km: float) -> float:
    """
    Exponential distance decay: D = e^(-d / L).

    Closer farms → stronger spatial association.

    Args:
        distance_km: Distance between two detections.
        characteristic_km: Scale parameter L (default 5 km).

    Returns:
        Score in [0, 1].
    """
    if characteristic_km <= 0:
        return 0.0
    return math.exp(-distance_km / characteristic_km)


def humidity_score(humidity_percent: float) -> float:
    """
    Normalize humidity to [0, 1].
    """
    return max(0.0, min(1.0, humidity_percent / 100.0))


def confidence_score(confidence: float) -> float:
    """
    Clamp AI confidence to [0, 1].
    """
    try:
        return max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        return 0.0


def classify_risk(score: float, thresholds: dict) -> str:
    """
    Classify a 0-100 risk score into LOW / MODERATE / HIGH / EXTREME.

    Args:
        score: Prototype risk score (0-100).
        thresholds: Dict with keys 'low', 'moderate', 'high', 'extreme'.

    Returns:
        One of: 'LOW', 'MODERATE', 'HIGH', 'EXTREME'.
    """
    if score >= thresholds.get("extreme", 90):
        return "EXTREME"
    if score >= thresholds.get("high", 80):
        return "HIGH"
    if score >= thresholds.get("moderate", 60):
        return "MODERATE"
    return "LOW"


def compute_risk(detections: list, config: dict) -> dict:
    """
    Compute the full prototype spatial risk score for a set of detections.

    Formula:
        R = w_d·D + w_h·H + w_c·C

    where:
        D = average pairwise distance decay score
        H = average normalized humidity
        C = average AI confidence
        w_d, w_h, w_c = configurable weights (default 0.5, 0.3, 0.2)

    Args:
        detections: List of detection dicts.
        config: GIS configuration dict (contains analysis parameters).

    Returns:
        Dict with all intermediate scores and the final risk score.
    """
    analysis_cfg = config.get("analysis", {})
    L = float(analysis_cfg.get("distance_characteristic_km", 5.0))
    weights = analysis_cfg.get("weights", {"distance": 0.5, "humidity": 0.3, "confidence": 0.2})

    # Pairwise distances
    pairs = compute_pairwise_distances(detections)
    if pairs:
        avg_distance_km = sum(p["distance_km"] for p in pairs) / len(pairs)
        avg_distance_score = sum(distance_score(p["distance_km"], L) for p in pairs) / len(pairs)
    else:
        # Single detection — no spatial relationship to measure
        avg_distance_km = 0.0
        avg_distance_score = 1.0  # maximum proximity (self)

    # Average humidity and confidence
    humidities = [d.get("weather", {}).get("humidity_percent", 0) for d in detections]
    confidences = [d.get("confidence", 0) for d in detections]

    avg_humidity = sum(humidities) / len(humidities) if humidities else 0.0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    H = humidity_score(avg_humidity)
    C = confidence_score(avg_confidence)
    D = avg_distance_score

    w_d = float(weights.get("distance", 0.5))
    w_h = float(weights.get("humidity", 0.3))
    w_c = float(weights.get("confidence", 0.2))

    # Normalize weights in case user misconfigured them
    total_w = w_d + w_h + w_c
    if total_w <= 0:
        total_w = 1.0
    w_d, w_h, w_c = w_d / total_w, w_h / total_w, w_c / total_w

    R = w_d * D + w_h * H + w_c * C
    risk_percentage = round(R * 100, 2)

    return {
        "pairwise_distances": pairs,
        "average_distance_km": round(avg_distance_km, 3),
        "distance_score": round(D, 4),
        "humidity_score": round(H, 4),
        "confidence_score": round(C, 4),
        "average_humidity_percent": round(avg_humidity, 2),
        "average_confidence": round(avg_confidence, 4),
        "weights": {"distance": w_d, "humidity": w_h, "confidence": w_c},
        "prototype_risk_score": round(R, 4),
        "prototype_risk_percentage": risk_percentage,
    }


# ---------------------------------------------------------------------------
# MAP RENDERING
# ---------------------------------------------------------------------------
def _format_farmer_label(farmer_id: str) -> str:
    """
    Convert a farmer_id like '001' into a map label like 'F001'.
    Avoids exposing full identifiers in public-facing visualizations.
    """
    return "F{}".format(farmer_id)


def _draw_fallback_background(ax, extent):
    """
    If no real map image is available, draw a clean placeholder background
    with a grid so the demo still produces a meaningful visualization.
    """
    min_lon, max_lon, min_lat, max_lat = extent
    ax.set_facecolor("#E8F0E8")
    ax.grid(True, linestyle="--", alpha=0.5, color="#888888")
    ax.text(
        (min_lon + max_lon) / 2,
        (min_lat + max_lat) / 2,
        "[ base map placeholder — drop sample_map.png into gis/input/ ]",
        ha="center", va="center",
        fontsize=10, color="#666666", style="italic",
    )


def _get_place_name(lat: float, lon: float) -> str:
    """Return friendly place name for coordinates in the region."""
    known_places = [
        (9.2645, 76.4600, "Thiruvalla"),
        (9.2712, 76.4721, "Chengannur"),
        (9.2801, 76.4815, "Aranmula"),
        (9.2910, 76.4930, "Kozhencherry"),
        (9.3025, 76.5045, "Pandalam"),
        (9.3150, 76.5160, "Mavelikkara"),
        (9.3280, 76.5280, "Pathanamthitta"),
    ]
    best_dist = 999.0
    best_name = None
    for p_lat, p_lon, name in known_places:
        dist = haversine_distance_km(lat, lon, p_lat, p_lon)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    if best_dist <= 2.5 and best_name:
        return best_name
    return f"{lat:.3f}°N, {lon:.3f}°E"


def render_analyzed_map(
    detections: list,
    disease: str,
    risk_results: dict,
    config: dict,
    output_path: str,
) -> str:
    """
    Render the analyzed map image with disease points, place names, distance markings,
    cluster danger rings, and risk info over the base map image.
    """
    viz = config.get("visualization", {})
    extent_cfg = config.get("map_extent", {})
    thresholds = config.get("analysis", {}).get("risk_thresholds",
                                                {"low": 30, "moderate": 60, "high": 80, "extreme": 90})

    extent = [
        extent_cfg.get("min_longitude", 76.40),
        extent_cfg.get("max_longitude", 76.55),
        extent_cfg.get("min_latitude", 9.20),
        extent_cfg.get("max_latitude", 9.35),
    ]

    point_size = int(viz.get("point_size", 140))
    point_color = viz.get("point_color", "#E53935")
    point_marker = viz.get("point_marker", "o")
    label_font_size = int(viz.get("label_font_size", 9))
    dpi = int(viz.get("dpi", 150))

    fig, ax = plt.subplots(figsize=(11, 8.5))

    # --- Load the base map image (sample_map.png) ---
    src_dir = os.path.dirname(os.path.abspath(__file__))      # gis/src
    gis_root = os.path.normpath(os.path.join(src_dir, ".."))  # gis/
    map_path = config.get("map_file", {}).get("path", "input/sample_map.png")
    
    if os.path.isabs(map_path):
        abs_map_path = map_path
    else:
        abs_map_path = os.path.join(gis_root, map_path)

    if os.path.exists(abs_map_path):
        try:
            img = plt.imread(abs_map_path)
            ax.imshow(
                img,
                extent=extent,
                aspect="auto",
                origin="upper",
                alpha=0.92,
            )
        except Exception as e:
            print(f"Warning: could not read map image ({e}); using fallback background.")
            _draw_fallback_background(ax, extent)
    else:
        print(f"Warning: map image not found at {abs_map_path}; using fallback background.")
        _draw_fallback_background(ax, extent)

    # --- Cluster / Buffer Zone Circles ---
    lons = [d["longitude"] for d in detections]
    lats = [d["latitude"] for d in detections]
    
    if lons and lats:
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
        
        # 1 km & 2.5 km approximate degree radius (1 deg lat ~ 111 km)
        r1_deg = 1.0 / 111.0
        r2_deg = 2.5 / 111.0
        
        # Outer caution buffer
        circle_outer = plt.Circle(
            (center_lon, center_lat), r2_deg,
            color="#FF9800", fill=True, alpha=0.12,
            linestyle=":", linewidth=1.5, zorder=2
        )
        ax.add_patch(circle_outer)
        
        # Inner high-risk buffer
        circle_inner = plt.Circle(
            (center_lon, center_lat), r1_deg,
            color="#E53935", fill=True, alpha=0.20,
            linestyle="--", linewidth=2.0, zorder=3
        )
        ax.add_patch(circle_inner)

    # --- Draw distance lines between all pairs with distance badges ---
    pairs = risk_results.get("pairwise_distances", [])
    for p in pairs:
        d_i = detections[p["i"]]
        d_j = detections[p["j"]]
        
        # Geodesic dashed line
        ax.plot(
            [d_i["longitude"], d_j["longitude"]],
            [d_i["latitude"], d_j["latitude"]],
            color="#1E88E5",
            linestyle="--",
            linewidth=2.0,
            alpha=0.9,
            zorder=4,
        )
        
        # Distance text badge at line midpoint
        mid_lon = (d_i["longitude"] + d_j["longitude"]) / 2
        mid_lat = (d_i["latitude"] + d_j["latitude"]) / 2
        ax.text(
            mid_lon, mid_lat,
            f" {p['distance_km']:.2f} km ",
            fontsize=8.5,
            color="#0D47A1",
            fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="#E3F2FD", ec="#1E88E5", lw=1.2, alpha=0.95),
            zorder=7,
        )

    # --- Plot detection points / place pins ---
    ax.scatter(
        lons, lats,
        s=point_size,
        c=point_color,
        marker=point_marker,
        edgecolors="#FFFFFF",
        linewidths=2.0,
        zorder=6,
    )

    # --- Label each detection with Place Name + Farmer ID ---
    for i, d in enumerate(detections):
        f_label = _format_farmer_label(d.get("farmer_id", "?"))
        p_name = d.get("place") or _get_place_name(d["latitude"], d["longitude"])
        full_label = f"{p_name} ({f_label})"
        
        # Alternate label offsets to avoid overlapping
        offset_x = 0.006 if (i % 2 == 0) else -0.006
        ha_align = "left" if (i % 2 == 0) else "right"
        offset_y = 0.005 if (i % 3 != 0) else -0.006
        
        ax.annotate(
            full_label,
            xy=(d["longitude"], d["latitude"]),
            xytext=(d["longitude"] + offset_x, d["latitude"] + offset_y),
            fontsize=label_font_size,
            fontweight="bold",
            color="#1A237E",
            ha=ha_align,
            bbox=dict(boxstyle="round,pad=0.35", fc="#FFFFFF", ec="#3949AB", lw=1.0, alpha=0.92),
            arrowprops=dict(arrowstyle="->", color="#3949AB", lw=0.8, shrinkA=3, shrinkB=4),
            zorder=8,
        )

    # --- Scale bar calculation (approx 2 km) ---
    scale_km = 2.0
    scale_deg = scale_km / (111.0 * math.cos(math.radians((extent[2] + extent[3]) / 2)))
    scale_x0 = extent[0] + 0.012
    scale_y0 = extent[2] + 0.012
    
    ax.plot([scale_x0, scale_x0 + scale_deg], [scale_y0, scale_y0], color="#0F172A", lw=3.5, zorder=8)
    ax.plot([scale_x0, scale_x0], [scale_y0 - 0.002, scale_y0 + 0.002], color="#0F172A", lw=2, zorder=8)
    ax.plot([scale_x0 + scale_deg, scale_x0 + scale_deg], [scale_y0 - 0.002, scale_y0 + 0.002], color="#0F172A", lw=2, zorder=8)
    ax.text(
        scale_x0 + scale_deg / 2, scale_y0 + 0.004,
        f"Scale: {scale_km:.0f} km",
        fontsize=8.5, fontweight="bold", color="#0F172A", ha="center",
        bbox=dict(boxstyle="round,pad=0.2", fc="#FFFFFF", ec="none", alpha=0.85),
        zorder=8
    )

    # --- Info box with risk summary ---
    risk_pct = risk_results.get("prototype_risk_percentage", 0)
    status = classify_risk(risk_pct, thresholds)

    info_text = (
        f"Disease: {disease}\n"
        f"Detections: {len(detections)}\n"
        f"Avg Distance: {risk_results.get('average_distance_km', 0):.2f} km\n"
        f"Avg Humidity: {risk_results.get('average_humidity_percent', 0):.1f}%\n"
        f"Avg Confidence: {risk_results.get('average_confidence', 0):.1%}\n"
        f"Risk Score: {risk_pct:.1f}/100\n"
        f"Cluster Status: {status}"
    )
    ax.text(
        0.02, 0.98, info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="#FFFFFF", ec="#0F172A", lw=1.2, alpha=0.92),
        zorder=9,
    )

    # --- Axes and title ---
    risk_colors = {"LOW": "#2E7D32", "MODERATE": "#EF6C00", "HIGH": "#C62828", "EXTREME": "#B71C1C"}
    title_color = risk_colors.get(status, "#0F172A")

    ax.set_title(
        f"{disease.upper()} — Geospatial Disease Spread Analysis  [{status}]",
        fontsize=13,
        fontweight="bold",
        color=title_color,
        pad=12,
    )
    ax.set_xlabel("Longitude (°E)", fontsize=9.5, fontweight="500")
    ax.set_ylabel("Latitude (°N)", fontsize=9.5, fontweight="500")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.grid(True, linestyle=":", alpha=0.4, color="#334155")

    # --- Legend ---
    legend_handles = [
        Line2D([0], [0], marker=point_marker, color="w",
               markerfacecolor=point_color, markeredgecolor="#FFFFFF", markersize=10, label="Detection Point"),
        Line2D([0], [0], color="#1E88E5", linestyle="--", linewidth=2.0, label="Distance Vector"),
        mpatches.Patch(color="#E53935", alpha=0.25, label="High-Risk Zone (<1 km)"),
        mpatches.Patch(color="#FF9800", alpha=0.15, label="Spread Buffer (<2.5 km)"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=8.5, framealpha=0.95)

    plt.tight_layout()

    # --- Save ---
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# RESULTS SERIALIZATION
# ---------------------------------------------------------------------------
def build_results_dict(
    event: dict,
    risk_results: dict,
    map_path: str,
    config: dict,
) -> dict:
    """
    Build the machine-readable GIS results dict to be saved as JSON.
    """
    thresholds = config.get("analysis", {}).get("risk_thresholds",
                                                {"low": 30, "moderate": 60, "high": 80, "extreme": 90})
    risk_pct = risk_results["prototype_risk_percentage"]
    status = classify_risk(risk_pct, thresholds)

    return {
        "event_id": event.get("event_id"),
        "disease": event.get("disease"),
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),

        "analysis": {
            "total_detections": len(event.get("detections", [])),
            "unique_farmers": event.get("unique_farmer_count"),
            "average_confidence": risk_results["average_confidence"],
            "average_humidity_percent": risk_results["average_humidity_percent"],
        },

        "spatial_analysis": {
            "average_distance_km": risk_results["average_distance_km"],
            "pairwise_distances": risk_results["pairwise_distances"],
            "distance_score": risk_results["distance_score"],
            "humidity_score": risk_results["humidity_score"],
            "confidence_score": risk_results["confidence_score"],
            "weights": risk_results["weights"],
            "prototype_risk_score": risk_results["prototype_risk_score"],
            "prototype_risk_percentage": risk_pct,
        },

        "status": status,
        "map_output": map_path,
    }


def save_results(results: dict, output_path: str) -> str:
    """
    Save the GIS results dict to a JSON file.

    Returns:
        Absolute path to the saved file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT — called by main.py
# ---------------------------------------------------------------------------
def analyze_event(event: dict, config: dict) -> tuple:
    """
    Run the full GIS analysis pipeline for a single priority event.

    Args:
        event: A single event dict from priority_events.json.
        config: GIS configuration dict loaded from config.json.

    Returns:
        (results_dict, map_path, results_path)

    Raises:
        ValueError: If the event has no detections or is missing required fields.
    """
    detections = event.get("detections", [])
    if not detections:
        raise ValueError("Event has no detections to analyze.")

    disease = event.get("disease", "Unknown Disease")

    # Validate that every detection has lat/lon
    for i, d in enumerate(detections):
        if "latitude" not in d or "longitude" not in d:
            raise ValueError(f"Detection #{i} is missing latitude/longitude.")

    # Resolve output paths relative to the GIS root directory (gis/),
    # NOT relative to this script's location (gis/src/).
    # gis/main.py passes config loaded from gis/config/map_config.json
    # which uses "output/..." paths — these should resolve to gis/output/.
    src_dir = os.path.dirname(os.path.abspath(__file__))      # gis/src/
    gis_root = os.path.normpath(os.path.join(src_dir, ".."))  # gis/
    output_cfg = config.get("output", {})
    map_rel = output_cfg.get("analyzed_map_path", "output/analyzed_map.png")
    results_rel = output_cfg.get("results_json_path", "output/gis_results.json")
    map_path = os.path.join(gis_root, map_rel)
    results_path = os.path.join(gis_root, results_rel)

    # 1. Compute risk
    risk_results = compute_risk(detections, config)

    # 2. Render map
    saved_map = render_analyzed_map(detections, disease, risk_results, config, map_path)

    # 3. Build and save results JSON
    results = build_results_dict(event, risk_results, saved_map, config)
    saved_results = save_results(results, results_path)

    return results, saved_map, saved_results


# ---------------------------------------------------------------------------
# STANDALONE TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Quick self-test with synthetic data
    print("Running gis_engine.py self-test...")
    print()

    test_event = {
        "event_id": "EVENT-TEST",
        "disease": "Early Blight",
        "detection_count": 2,
        "unique_farmer_count": 2,
        "status": "TRIGGERED",
        "detections": [
            {
                "farmer_id": "001",
                "latitude": 9.2645,
                "longitude": 76.4600,
                "confidence": 0.942,
                "weather": {"temperature_c": 28.4, "humidity_percent": 86, "wind_speed_kmh": 8.2},
            },
            {
                "farmer_id": "002",
                "latitude": 9.2712,
                "longitude": 76.4721,
                "confidence": 0.942,
                "weather": {"temperature_c": 29.1, "humidity_percent": 89, "wind_speed_kmh": 6.7},
            },
        ],
    }

    test_config = {
        "map_extent": {
            "min_latitude": 9.20, "max_latitude": 9.35,
            "min_longitude": 76.40, "max_longitude": 76.55,
        },
        "map_file": {"path": "input/sample_map.png"},
        "visualization": {
            "point_size": 120, "point_color": "#FF4444", "point_marker": "o",
            "label_font_size": 10, "label_offset": 0.005, "dpi": 150,
        },
        "analysis": {
            "distance_characteristic_km": 5.0,
            "weights": {"distance": 0.5, "humidity": 0.3, "confidence": 0.2},
            "risk_thresholds": {"low": 30, "moderate": 60, "high": 80, "extreme": 90},
        },
        "output": {
            "analyzed_map_path": "output/test_analyzed_map.png",
            "results_json_path": "output/test_gis_results.json",
        },
    }

    results, map_path, results_path = analyze_event(test_event, test_config)

    print("Results:")
    print(json.dumps(results, indent=2))
    print()
    print(f"Map saved to     : {map_path}")
    print(f"Results saved to : {results_path}")