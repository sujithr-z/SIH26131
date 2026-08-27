#!/usr/bin/env python3
"""
risk_calculator.py — Prototype spatial risk scoring for disease detections.

This module computes a PROTOTYPE spatial risk score based on:
  1. Distance decay between detections (closer farms → higher risk)
  2. Environmental humidity (higher humidity → higher risk)
  3. AI detection confidence (higher confidence → higher risk)
  4. Optional temperature factor (disease-favorable temperatures)

Formula:
    R = w_d·D + w_h·H + w_c·C + w_t·T

where:
    D = average exponential distance decay score
    H = average normalized humidity
    C = average AI confidence
    T = temperature favorability score (optional)
    w_d, w_h, w_c, w_t = configurable weights

IMPORTANT: This is explicitly a PROTOTYPE metric. It is NOT an
epidemiological prediction. Real disease forecasting requires
pathosystem-specific models trained on historical outbreak data.
The score is named `prototype_risk_score` throughout to preserve
scientific honesty.

Usage:
    from risk_calculator import compute_spatial_risk
    
    detections = [...]
    pairwise_distances = [...]
    config = {...}
    
    risk_result = compute_spatial_risk(detections, pairwise_distances, config)
"""

import math
from typing import List, Dict, Tuple, Optional


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
DEFAULT_CHARACTERISTIC_DISTANCE_KM = 5.0  # L parameter for distance decay

DEFAULT_WEIGHTS = {
    "distance": 0.5,
    "humidity": 0.3,
    "confidence": 0.2,
    "temperature": 0.0,  # disabled by default
}

DEFAULT_RISK_THRESHOLDS = {
    "low": 30,
    "moderate": 60,
    "high": 80,
    "extreme": 90,
}

# Disease-favorable temperature range (°C) for common fungal diseases
# like Late Blight and Early Blight. Based on literature values.
DISEASE_FAVORABLE_TEMP_MIN = 18.0
DISEASE_FAVORABLE_TEMP_MAX = 25.0
DISEASE_TOLERATED_TEMP_MIN = 10.0
DISEASE_TOLERATED_TEMP_MAX = 30.0


# ---------------------------------------------------------------------------
# INDIVIDUAL SCORE COMPONENTS
# ---------------------------------------------------------------------------
def distance_decay_score(
    distance_km: float,
    characteristic_km: float = DEFAULT_CHARACTERISTIC_DISTANCE_KM
) -> float:
    """
    Exponential distance decay: D = e^(-d / L).
    
    Closer farms → stronger spatial association → higher score.
    
    Args:
        distance_km: Distance between two detections (km)
        characteristic_km: Scale parameter L (km). Controls how quickly
                          the score decays with distance. Default: 5 km.
    
    Returns:
        Score in [0, 1]. Returns 1.0 for distance=0, approaches 0 for large d.
    
    Example:
        >>> round(distance_decay_score(0, 5.0), 2)
        1.0
        >>> round(distance_decay_score(5, 5.0), 2)
        0.37
        >>> round(distance_decay_score(10, 5.0), 2)
        0.14
    """
    if characteristic_km <= 0:
        return 0.0
    if distance_km < 0:
        distance_km = 0.0
    return math.exp(-distance_km / characteristic_km)


def humidity_score(humidity_percent: float) -> float:
    """
    Normalize humidity to [0, 1].
    
    High humidity (≥85%) is strongly associated with fungal disease
    development (leaf wetness proxy).
    
    Args:
        humidity_percent: Relative humidity (0-100)
    
    Returns:
        Score in [0, 1]
    
    Example:
        >>> humidity_score(87)
        0.87
        >>> humidity_score(100)
        1.0
        >>> humidity_score(0)
        0.0
    """
    try:
        h = float(humidity_percent)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, h / 100.0))


def confidence_score(confidence: float) -> float:
    """
    Clamp AI detection confidence to [0, 1].
    
    Higher confidence → more reliable detection → higher weight in risk.
    
    Args:
        confidence: AI confidence value (typically 0-1)
    
    Returns:
        Score in [0, 1]
    
    Example:
        >>> confidence_score(0.94)
        0.94
        >>> confidence_score(1.5)  # clamped
        1.0
    """
    try:
        c = float(confidence)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, c))


def temperature_favorability_score(temperature_c: float) -> float:
    """
    Score how favorable the temperature is for disease development.
    
    Based on typical ranges for Late Blight / Early Blight:
      - 18-25°C → optimal (score = 1.0)
      - 10-18°C or 25-30°C → tolerated (linear decay to 0)
      - Outside 10-30°C → unfavorable (score = 0)
    
    Args:
        temperature_c: Temperature in Celsius
    
    Returns:
        Score in [0, 1]
    
    Example:
        >>> temperature_favorability_score(22.0)  # optimal
        1.0
        >>> 0.0 < temperature_favorability_score(15.0) < 1.0  # tolerated
        True
        >>> temperature_favorability_score(5.0)  # too cold
        0.0
    """
    try:
        t = float(temperature_c)
    except (TypeError, ValueError):
        return 0.0
    
    # Optimal range
    if DISEASE_FAVORABLE_TEMP_MIN <= t <= DISEASE_FAVORABLE_TEMP_MAX:
        return 1.0
    
    # Below optimal — linear decay
    if DISEASE_TOLERATED_TEMP_MIN <= t < DISEASE_FAVORABLE_TEMP_MIN:
        span = DISEASE_FAVORABLE_TEMP_MIN - DISEASE_TOLERATED_TEMP_MIN
        return (t - DISEASE_TOLERATED_TEMP_MIN) / span if span > 0 else 0.0
    
    # Above optimal — linear decay
    if DISEASE_FAVORABLE_TEMP_MAX < t <= DISEASE_TOLERATED_TEMP_MAX:
        span = DISEASE_TOLERATED_TEMP_MAX - DISEASE_FAVORABLE_TEMP_MAX
        return (DISEASE_TOLERATED_TEMP_MAX - t) / span if span > 0 else 0.0
    
    # Outside tolerated range
    return 0.0


# ---------------------------------------------------------------------------
# AGGREGATE RISK COMPUTATION
# ---------------------------------------------------------------------------
def _extract_weather_values(detections: List[Dict]) -> Tuple[float, float, float]:
    """
    Extract average humidity, confidence, and temperature from detections.
    
    Returns:
        (avg_humidity, avg_confidence, avg_temperature)
    """
    humidities = []
    confidences = []
    temperatures = []
    
    for d in detections:
        weather = d.get("weather", {}) or {}
        
        if "humidity_percent" in weather:
            try:
                humidities.append(float(weather["humidity_percent"]))
            except (TypeError, ValueError):
                pass
        
        if "confidence" in d:
            try:
                confidences.append(float(d["confidence"]))
            except (TypeError, ValueError):
                pass
        
        if "temperature_c" in weather:
            try:
                temperatures.append(float(weather["temperature_c"]))
            except (TypeError, ValueError):
                pass
    
    avg_humidity = sum(humidities) / len(humidities) if humidities else 0.0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    avg_temperature = sum(temperatures) / len(temperatures) if temperatures else 0.0
    
    return avg_humidity, avg_confidence, avg_temperature


def compute_spatial_risk(
    detections: List[Dict],
    pairwise_distances: List[Dict],
    config: Dict
) -> Dict:
    """
    Compute the full prototype spatial risk score.
    
    Args:
        detections: List of detection dicts with 'confidence' and 'weather'.
        pairwise_distances: Output of distance_calculator.calculate_pairwise_distances().
                           Each dict has 'distance_km'.
        config: GIS configuration dict with 'analysis' key containing:
            - distance_characteristic_km: L parameter
            - weights: dict of component weights
            - risk_thresholds: dict of LOW/MODERATE/HIGH/EXTREME thresholds
    
    Returns:
        Dict with all intermediate scores and final risk classification:
        {
            'component_scores': {
                'distance': {'raw': 0.73, 'weighted': 0.365},
                'humidity': {'raw': 0.88, 'weighted': 0.264},
                'confidence': {'raw': 0.94, 'weighted': 0.188},
                'temperature': {'raw': 0.5, 'weighted': 0.0}
            },
            'averages': {
                'humidity_percent': 87.5,
                'confidence': 0.94,
                'temperature_c': 28.5,
                'distance_km': 1.58
            },
            'weights': {'distance': 0.5, 'humidity': 0.3, ...},
            'prototype_risk_score': 0.817,
            'prototype_risk_percentage': 81.7,
            'status': 'HIGH'
        }
    
    Example:
        >>> detections = [
        ...     {'confidence': 0.94, 'weather': {'humidity_percent': 86, 'temperature_c': 28.4}},
        ...     {'confidence': 0.94, 'weather': {'humidity_percent': 89, 'temperature_c': 29.1}}
        ... ]
        >>> distances = [{'distance_km': 1.58}]
        >>> config = {'analysis': {'distance_characteristic_km': 5.0,
        ...                        'weights': {'distance': 0.5, 'humidity': 0.3, 'confidence': 0.2}}}
        >>> result = compute_spatial_risk(detections, distances, config)
        >>> result['status'] in ['LOW', 'MODERATE', 'HIGH', 'EXTREME']
        True
    """
    analysis_cfg = config.get("analysis", {})
    
    # Extract parameters with defaults
    L = float(analysis_cfg.get("distance_characteristic_km",
                               DEFAULT_CHARACTERISTIC_DISTANCE_KM))
    raw_weights = analysis_cfg.get("weights", DEFAULT_WEIGHTS)
    thresholds = analysis_cfg.get("risk_thresholds", DEFAULT_RISK_THRESHOLDS)
    
    # --- 1. Distance component ---
    if pairwise_distances:
        distances_km = [p["distance_km"] for p in pairwise_distances]
        avg_distance_km = sum(distances_km) / len(distances_km)
        individual_d_scores = [distance_decay_score(d, L) for d in distances_km]
        D = sum(individual_d_scores) / len(individual_d_scores)
    else:
        # Single detection — no spatial relationship; assume maximum proximity
        avg_distance_km = 0.0
        individual_d_scores = []
        D = 1.0
    
    # --- 2. Environmental components ---
    avg_humidity, avg_confidence, avg_temperature = _extract_weather_values(detections)
    
    H = humidity_score(avg_humidity)
    C = confidence_score(avg_confidence)
    T = temperature_favorability_score(avg_temperature)
    
    # --- 3. Normalize weights ---
    w_d = float(raw_weights.get("distance", 0.5))
    w_h = float(raw_weights.get("humidity", 0.3))
    w_c = float(raw_weights.get("confidence", 0.2))
    w_t = float(raw_weights.get("temperature", 0.0))
    
    total_w = w_d + w_h + w_c + w_t
    if total_w <= 0:
        total_w = 1.0
    w_d, w_h, w_c, w_t = w_d / total_w, w_h / total_w, w_c / total_w, w_t / total_w
    
    # --- 4. Weighted combination ---
    R = w_d * D + w_h * H + w_c * C + w_t * T
    
    risk_percentage = round(R * 100, 2)
    status = classify_risk(risk_percentage, thresholds)
    
    return {
        "component_scores": {
            "distance": {
                "raw": round(D, 4),
                "weighted": round(w_d * D, 4),
                "pairwise_scores": [round(s, 4) for s in individual_d_scores],
            },
            "humidity": {
                "raw": round(H, 4),
                "weighted": round(w_h * H, 4),
            },
            "confidence": {
                "raw": round(C, 4),
                "weighted": round(w_c * C, 4),
            },
            "temperature": {
                "raw": round(T, 4),
                "weighted": round(w_t * T, 4),
            },
        },
        "averages": {
            "humidity_percent": round(avg_humidity, 2),
            "confidence": round(avg_confidence, 4),
            "temperature_c": round(avg_temperature, 2),
            "distance_km": round(avg_distance_km, 3),
        },
        "parameters": {
            "characteristic_distance_km": L,
        },
        "weights": {
            "distance": round(w_d, 4),
            "humidity": round(w_h, 4),
            "confidence": round(w_c, 4),
            "temperature": round(w_t, 4),
        },
        "prototype_risk_score": round(R, 4),
        "prototype_risk_percentage": risk_percentage,
        "status": status,
    }


def compute_spatial_risk_safe(
    detections: List[Dict],
    pairwise_distances: List[Dict],
    config: Dict
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Safe version of compute_spatial_risk that returns error message.
    
    Args:
        detections: List of detection dicts
        pairwise_distances: List of pairwise distance dicts
        config: GIS configuration dict
    
    Returns:
        (risk_result, error_message)
    """
    try:
        result = compute_spatial_risk(detections, pairwise_distances, config)
        return result, None
    except (KeyError, TypeError, ValueError) as e:
        return None, f"Risk computation failed: {e}"
    except Exception as e:
        return None, f"Unexpected error in risk computation: {e}"


# ---------------------------------------------------------------------------
# RISK CLASSIFICATION
# ---------------------------------------------------------------------------
def classify_risk(score: float, thresholds: Dict = None) -> str:
    """
    Classify a 0-100 risk score into LOW / MODERATE / HIGH / EXTREME.
    
    Args:
        score: Prototype risk score (0-100)
        thresholds: Dict with keys 'low', 'moderate', 'high', 'extreme'.
                   Defaults to DEFAULT_RISK_THRESHOLDS.
    
    Returns:
        One of: 'LOW', 'MODERATE', 'HIGH', 'EXTREME'
    
    Example:
        >>> classify_risk(25)
        'LOW'
        >>> classify_risk(65)
        'MODERATE'
        >>> classify_risk(85)
        'HIGH'
        >>> classify_risk(95)
        'EXTREME'
    """
    if thresholds is None:
        thresholds = DEFAULT_RISK_THRESHOLDS
    
    if score >= thresholds.get("extreme", 90):
        return "EXTREME"
    if score >= thresholds.get("high", 80):
        return "HIGH"
    if score >= thresholds.get("moderate", 60):
        return "MODERATE"
    return "LOW"


def get_status_color(status: str) -> str:
    """
    Get a hex color code for a risk status (useful for visualization).
    
    Args:
        status: One of 'LOW', 'MODERATE', 'HIGH', 'EXTREME'
    
    Returns:
        Hex color string
    
    Example:
        >>> get_status_color('HIGH')
        '#FF9800'
    """
    colors = {
        "LOW": "#4CAF50",       # green
        "MODERATE": "#FFC107",  # amber
        "HIGH": "#FF9800",      # orange
        "EXTREME": "#F44336",   # red
    }
    return colors.get(status, "#888888")


def get_status_emoji(status: str) -> str:
    """
    Get an emoji indicator for a risk status.
    
    Args:
        status: One of 'LOW', 'MODERATE', 'HIGH', 'EXTREME'
    
    Returns:
        Emoji string
    
    Example:
        >>> get_status_emoji('EXTREME')
        '🔴'
    """
    emojis = {
        "LOW": "🟢",
        "MODERATE": "🟡",
        "HIGH": "🟠",
        "EXTREME": "🔴",
    }
    return emojis.get(status, "⚪")


# ---------------------------------------------------------------------------
# FORMATTING UTILITIES
# ---------------------------------------------------------------------------
def format_risk_summary(result: Dict) -> str:
    """
    Format a risk result as a human-readable multi-line string.
    
    Args:
        result: Output of compute_spatial_risk()
    
    Returns:
        Formatted string
    
    Example:
        >>> result = compute_spatial_risk(detections, distances, config)
        >>> print(format_risk_summary(result))
    """
    status = result.get("status", "?")
    emoji = get_status_emoji(status)
    pct = result.get("prototype_risk_percentage", 0)
    avg = result.get("averages", {})
    components = result.get("component_scores", {})
    
    lines = [
        f"{emoji} PROTOTYPE SPATIAL RISK: {pct:.1f}/100  [{status}]",
        "",
        "Component Scores:",
        f"  Distance   : {components.get('distance', {}).get('raw', 0):.3f}",
        f"  Humidity   : {components.get('humidity', {}).get('raw', 0):.3f}",
        f"  Confidence : {components.get('confidence', {}).get('raw', 0):.3f}",
        f"  Temperature: {components.get('temperature', {}).get('raw', 0):.3f}",
        "",
        "Averages:",
        f"  Distance   : {avg.get('distance_km', 0):.2f} km",
        f"  Humidity   : {avg.get('humidity_percent', 0):.1f}%",
        f"  Confidence : {avg.get('confidence', 0):.1%}",
        f"  Temperature: {avg.get('temperature_c', 0):.1f}°C",
    ]
    
    return "\n".join(lines)


def format_risk_compact(result: Dict) -> str:
    """
    Format a risk result as a compact single-line string.
    
    Args:
        result: Output of compute_spatial_risk()
    
    Returns:
        Compact string
    
    Example:
        >>> format_risk_compact(result)
        'Risk: 81.7/100 [HIGH] | Dist: 1.58km | Hum: 87.5% | Conf: 94.0%'
    """
    status = result.get("status", "?")
    pct = result.get("prototype_risk_percentage", 0)
    avg = result.get("averages", {})
    
    return (
        f"Risk: {pct:.1f}/100 [{status}] | "
        f"Dist: {avg.get('distance_km', 0):.2f}km | "
        f"Hum: {avg.get('humidity_percent', 0):.1f}% | "
        f"Conf: {avg.get('confidence', 0):.1%}"
    )


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing risk_calculator.py...")
    print()
    
    # Test individual score functions
    print("1. Individual score functions:")
    print(f"   Distance decay (0 km)  : {distance_decay_score(0, 5.0):.3f}")
    print(f"   Distance decay (2 km)  : {distance_decay_score(2, 5.0):.3f}")
    print(f"   Distance decay (5 km)  : {distance_decay_score(5, 5.0):.3f}")
    print(f"   Distance decay (10 km) : {distance_decay_score(10, 5.0):.3f}")
    print(f"   Humidity (87%)         : {humidity_score(87):.3f}")
    print(f"   Confidence (0.94)      : {confidence_score(0.94):.3f}")
    print(f"   Temperature (22°C)     : {temperature_favorability_score(22.0):.3f}")
    print(f"   Temperature (28°C)     : {temperature_favorability_score(28.0):.3f}")
    print()
    
    # Test full risk computation
    print("2. Full risk computation:")
    test_detections = [
        {
            "farmer_id": "001",
            "confidence": 0.942,
            "weather": {"temperature_c": 28.4, "humidity_percent": 86, "wind_speed_kmh": 8.2},
        },
        {
            "farmer_id": "002",
            "confidence": 0.942,
            "weather": {"temperature_c": 29.1, "humidity_percent": 89, "wind_speed_kmh": 6.7},
        },
    ]
    test_distances = [{"distance_km": 1.583, "farmer_a": "001", "farmer_b": "002"}]
    test_config = {
        "analysis": {
            "distance_characteristic_km": 5.0,
            "weights": {"distance": 0.5, "humidity": 0.3, "confidence": 0.2},
            "risk_thresholds": {"low": 30, "moderate": 60, "high": 80, "extreme": 90},
        }
    }
    
    result = compute_spatial_risk(test_detections, test_distances, test_config)
    print()
    print(format_risk_summary(result))
    print()
    print(f"Compact: {format_risk_compact(result)}")
    print()
    
    # Test classification
    print("3. Risk classification:")
    for score in [20, 45, 70, 85, 95]:
        status = classify_risk(score)
        emoji = get_status_emoji(status)
        color = get_status_color(status)
        print(f"   Score {score:3d} → {emoji} {status:8s} ({color})")
    print()
    
    print("All tests passed!")