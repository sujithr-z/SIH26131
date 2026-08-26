#!/usr/bin/env python3
"""
pipeline/build_report.py — Unified Report Builder

Reads:
  - cropguard/data/priority_events.json   (latest surveillance event)
  - cropguard/gis/output/gis_results.json (spatial analysis results)
  - cropguard/data/farmers.json           (farmer contact details)

Writes:
  - cropguard/reports/latest_report.json  (single unified JSON for the dashboard)

This script is called automatically by gis/main.py after each GIS run.
It can also be run standalone: python3 pipeline/build_report.py
"""

import json
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# PATHS — resolved relative to this script
# ---------------------------------------------------------------------------
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR         = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
EVENTS_FILE      = os.path.join(ROOT_DIR, "data", "priority_events.json")
GIS_RESULTS_FILE = os.path.join(ROOT_DIR, "gis", "output", "gis_results.json")
FARMERS_FILE     = os.path.join(ROOT_DIR, "data", "farmers.json")
OUTPUT_FILE      = os.path.join(ROOT_DIR, "reports", "latest_report.json")

# Web-accessible path to the analyzed map (relative to cropguard/ web root)
ANALYZED_MAP_WEB_PATH = "gis/output/analyzed_map.png"


# ---------------------------------------------------------------------------
# LOADERS
# ---------------------------------------------------------------------------
def load_json(path, description):
    """Load a JSON file and return its content, or None on failure."""
    if not os.path.exists(path):
        print(f"  WARNING: {description} not found at: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  WARNING: Could not read {description}: {e}")
        return None


def build_farmer_lookup(farmers_data):
    """Build a dict mapping farmer_id -> farmer record."""
    if not isinstance(farmers_data, list):
        return {}
    return {f.get("farmer_id"): f for f in farmers_data if f.get("farmer_id")}


# ---------------------------------------------------------------------------
# REPORT BUILDER
# ---------------------------------------------------------------------------
def build_report():
    """
    Assemble the unified report JSON from all pipeline outputs.

    Returns the report dict on success, None on failure.
    """
    print("Loading pipeline data sources...")

    # --- Load sources ---
    events_data  = load_json(EVENTS_FILE,      "priority_events.json")
    gis_data     = load_json(GIS_RESULTS_FILE, "gis_results.json")
    farmers_data = load_json(FARMERS_FILE,      "farmers.json")

    if events_data is None:
        print("ERROR: Cannot build report — no priority events found.")
        return None

    events = events_data.get("events", [])
    if not events:
        print("ERROR: priority_events.json has no events yet.")
        return None

    # --- Select the latest triggered event ---
    triggered = [e for e in events if e.get("status") == "TRIGGERED"]
    if not triggered:
        print("ERROR: No TRIGGERED events found.")
        return None

    def parse_ts(ev):
        ts = ev.get("generated_at", "")
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.min

    latest_event = sorted(triggered, key=parse_ts, reverse=True)[0]

    # --- Farmer lookup ---
    farmer_map = build_farmer_lookup(farmers_data or [])

    # --- Enrich detections with farmer contact info ---
    detections = latest_event.get("detections", [])
    enriched_detections = []
    for det in detections:
        fid = det.get("farmer_id", "?")
        farmer = farmer_map.get(fid, {})
        enriched_detections.append({
            "observation_id": det.get("observation_id"),
            "farmer_id":      fid,
            "farmer_name":    farmer.get("full_name", "Unknown"),
            "farmer_phone":   farmer.get("phone", ""),
            "crop":           det.get("crop"),
            "image_path":     det.get("image_path"),
            "confidence":     det.get("confidence"),
            "timestamp":      det.get("timestamp"),
            "latitude":       det.get("latitude"),
            "longitude":      det.get("longitude"),
            "weather":        det.get("weather", {}),
        })

    # --- GIS / Spatial data ---
    spatial = {}
    risk_score = None
    risk_status = "UNKNOWN"
    if gis_data:
        spatial_analysis = gis_data.get("spatial_analysis", {})
        analysis         = gis_data.get("analysis", {})
        spatial = {
            "average_distance_km":     spatial_analysis.get("average_distance_km"),
            "pairwise_distances":      spatial_analysis.get("pairwise_distances", []),
            "distance_score":          spatial_analysis.get("distance_score"),
            "humidity_score":          spatial_analysis.get("humidity_score"),
            "confidence_score":        spatial_analysis.get("confidence_score"),
            "weights":                 spatial_analysis.get("weights", {}),
            "prototype_risk_score":    spatial_analysis.get("prototype_risk_score"),
            "prototype_risk_percentage": spatial_analysis.get("prototype_risk_percentage"),
            "average_humidity_percent":  analysis.get("average_humidity_percent"),
            "average_confidence":        analysis.get("average_confidence"),
        }
        risk_score  = spatial_analysis.get("prototype_risk_percentage")
        risk_status = gis_data.get("status", "UNKNOWN")

    # --- Weather summary (average across detections) ---
    weather_values = [d.get("weather", {}) for d in detections]
    def avg_weather_field(field):
        vals = [w.get(field) for w in weather_values if w.get(field) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    weather_summary = {
        "temperature_c":    avg_weather_field("temperature_c"),
        "humidity_percent": avg_weather_field("humidity_percent"),
        "wind_speed_kmh":   avg_weather_field("wind_speed_kmh"),
    }

    # --- Check if analyzed map exists ---
    analyzed_map_abs = os.path.join(ROOT_DIR, "gis", "output", "analyzed_map.png")
    map_available = os.path.exists(analyzed_map_abs)

    # --- Assemble final report ---
    report = {
        "report_id":   "RPT-{}".format(datetime.utcnow().strftime("%Y%m%d-%H%M%S")),
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),

        "event": {
            "event_id":            latest_event.get("event_id"),
            "disease":             latest_event.get("disease"),
            "status":              latest_event.get("status"),
            "generated_at":        latest_event.get("generated_at"),
            "detection_count":     latest_event.get("detection_count"),
            "unique_farmer_count": latest_event.get("unique_farmer_count"),
        },

        "detection_summary": {
            "total_detections":    len(detections),
            "unique_farmers":      latest_event.get("unique_farmer_count"),
            "average_confidence":  round(
                sum(d.get("confidence", 0) for d in detections) / len(detections), 4
            ) if detections else 0,
        },

        "detections": enriched_detections,

        "weather_summary": weather_summary,

        "spatial_analysis": spatial,

        "risk": {
            "prototype_risk_percentage": risk_score,
            "status": risk_status,
            "label":  "{}/100 {}".format(
                round(risk_score) if risk_score is not None else "?",
                risk_status
            ),
        },

        "map": {
            "available":   map_available,
            "web_path":    ANALYZED_MAP_WEB_PATH if map_available else None,
            "absolute_path": analyzed_map_abs if map_available else None,
        },

        "pipeline_status": {
            "farmer_app":       "COMPLETE",
            "data_ingestion":   "COMPLETE",
            "database":         "COMPLETE",
            "priority_analysis":"COMPLETE",
            "gis_analysis":     "COMPLETE" if gis_data else "PENDING",
            "report_builder":   "COMPLETE",
            "dashboard":        "PENDING_DECISION",
            "alert":            "PENDING_DECISION",
        },

        "metadata": {
            "source_event_id":   latest_event.get("event_id"),
            "gis_available":     gis_data is not None,
            "total_events_in_db": len(events),
            "description": (
                "Unified surveillance report generated automatically by the "
                "integration pipeline. Do not edit manually."
            ),
        },
    }

    return report


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print(" REPORT BUILDER — Agricultural Disease Surveillance")
    print("=" * 60)
    print()

    report = build_report()
    if report is None:
        print()
        print("Report builder failed — see warnings above.")
        sys.exit(1)

    # Ensure reports/ directory exists
    reports_dir = os.path.dirname(OUTPUT_FILE)
    os.makedirs(reports_dir, exist_ok=True)

    # Write report (atomic: temp file then rename)
    tmp_path = OUTPUT_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    os.replace(tmp_path, OUTPUT_FILE)

    print()
    print(f"  Report ID      : {report['report_id']}")
    print(f"  Event          : {report['event']['event_id']} — {report['event']['disease']}")
    print(f"  Detections     : {report['detection_summary']['total_detections']}")
    print(f"  Farmers        : {report['detection_summary']['unique_farmers']}")
    print(f"  Risk           : {report['risk']['label']}")
    print(f"  Map available  : {report['map']['available']}")
    print()
    print(f"  Output written : {OUTPUT_FILE}")
    print()
    print("=" * 60)
    print("Report complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
