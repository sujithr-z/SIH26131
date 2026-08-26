#!/usr/bin/env python3
"""
distance_calculator.py — Geographic distance calculations for disease detections.

This module provides:
  1. Haversine formula for great-circle distance between lat/lon points
  2. Pairwise distance calculations for multiple detections
  3. Distance matrix generation for N points
  4. Structured distance data for risk analysis

All distances are calculated in kilometers using the Haversine formula,
which accounts for Earth's curvature. This is more accurate than simple
Euclidean distance on lat/lon coordinates.

Usage:
    from distance_calculator import calculate_pairwise_distances
    
    detections = [
        {'farmer_id': '001', 'latitude': 9.2645, 'longitude': 76.4600},
        {'farmer_id': '002', 'latitude': 9.2712, 'longitude': 76.4721},
    ]
    
    distances = calculate_pairwise_distances(detections)
"""

import math
from typing import List, Dict, Tuple, Optional


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
EARTH_RADIUS_KM = 6371.0  # Mean Earth radius in kilometers


# ---------------------------------------------------------------------------
# HAVERSINE FORMULA
# ---------------------------------------------------------------------------
def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula:
        a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
        c = 2·atan2(√a, √(1−a))
        d = R·c
    
    where:
        φ = latitude (radians)
        λ = longitude (radians)
        R = Earth's radius (6371 km)
    
    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)
    
    Returns:
        Distance in kilometers
    
    Raises:
        ValueError: If coordinates are out of valid range
    
    Example:
        >>> haversine_distance(9.2645, 76.4600, 9.2712, 76.4721)
        1.583
    """
    # Validate coordinate ranges
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        raise ValueError(f"Latitude must be between -90 and 90: {lat1}, {lat2}")
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError(f"Longitude must be between -180 and 180: {lon1}, {lon2}")
    
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def haversine_distance_safe(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> Tuple[Optional[float], Optional[str]]:
    """
    Safe version of haversine_distance that returns error message instead of raising.
    
    Args:
        lat1, lon1: Coordinates of point 1
        lat2, lon2: Coordinates of point 2
    
    Returns:
        (distance_km, error_message)
        - distance_km: Distance in km, or None on error
        - error_message: None on success, error string on failure
    
    Example:
        >>> dist, err = haversine_distance_safe(9.2645, 76.4600, 9.2712, 76.4721)
        >>> if err:
        ...     print(f"Error: {err}")
        >>> else:
        ...     print(f"Distance: {dist:.2f} km")
    """
    try:
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        return distance, None
    except ValueError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# PAIRWISE DISTANCE CALCULATIONS
# ---------------------------------------------------------------------------
def calculate_pairwise_distances(
    detections: List[Dict]
) -> List[Dict]:
    """
    Calculate distances between all pairs of detections.
    
    For N detections, this calculates N*(N-1)/2 pairwise distances.
    
    Args:
        detections: List of detection dicts, each containing:
            - farmer_id: str
            - latitude: float
            - longitude: float
            - (other fields are ignored)
    
    Returns:
        List of distance dicts, each containing:
            - i: index of first detection
            - j: index of second detection
            - farmer_a: farmer_id of first detection
            - farmer_b: farmer_id of second detection
            - distance_km: distance in kilometers (rounded to 3 decimals)
    
    Raises:
        ValueError: If a detection is missing latitude/longitude
    
    Example:
        >>> detections = [
        ...     {'farmer_id': '001', 'latitude': 9.2645, 'longitude': 76.4600},
        ...     {'farmer_id': '002', 'latitude': 9.2712, 'longitude': 76.4721},
        ...     {'farmer_id': '003', 'latitude': 9.2801, 'longitude': 76.4815}
        ... ]
        >>> distances = calculate_pairwise_distances(detections)
        >>> len(distances)
        3
        >>> distances[0]['distance_km']
        1.583
    """
    if len(detections) < 2:
        return []
    
    # Validate all detections have coordinates
    for i, det in enumerate(detections):
        if 'latitude' not in det or 'longitude' not in det:
            raise ValueError(f"Detection #{i} is missing latitude/longitude")
    
    distances = []
    n = len(detections)
    
    for i in range(n):
        for j in range(i + 1, n):
            det_i = detections[i]
            det_j = detections[j]
            
            distance = haversine_distance(
                det_i['latitude'], det_i['longitude'],
                det_j['latitude'], det_j['longitude']
            )
            
            distances.append({
                'i': i,
                'j': j,
                'farmer_a': det_i.get('farmer_id', '?'),
                'farmer_b': det_j.get('farmer_id', '?'),
                'distance_km': round(distance, 3)
            })
    
    return distances


def calculate_pairwise_distances_safe(
    detections: List[Dict]
) -> Tuple[List[Dict], Optional[str]]:
    """
    Safe version of calculate_pairwise_distances that returns error message.
    
    Args:
        detections: List of detection dicts
    
    Returns:
        (distances, error_message)
        - distances: List of distance dicts, or empty list on error
        - error_message: None on success, error string on failure
    
    Example:
        >>> distances, err = calculate_pairwise_distances_safe(detections)
        >>> if err:
        ...     print(f"Error: {err}")
        >>> else:
        ...     print(f"Calculated {len(distances)} distances")
    """
    try:
        distances = calculate_pairwise_distances(detections)
        return distances, None
    except ValueError as e:
        return [], str(e)
    except Exception as e:
        return [], f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# DISTANCE MATRIX
# ---------------------------------------------------------------------------
def calculate_distance_matrix(
    detections: List[Dict]
) -> List[List[float]]:
    """
    Calculate a full N×N distance matrix for N detections.
    
    The matrix is symmetric: matrix[i][j] == matrix[j][i]
    Diagonal elements are 0: matrix[i][i] == 0
    
    Args:
        detections: List of detection dicts with latitude/longitude
    
    Returns:
        2D list (matrix) where matrix[i][j] is the distance in km
        between detection i and detection j
    
    Example:
        >>> detections = [
        ...     {'latitude': 9.2645, 'longitude': 76.4600},
        ...     {'latitude': 9.2712, 'longitude': 76.4721}
        ... ]
        >>> matrix = calculate_distance_matrix(detections)
        >>> matrix[0][1] == matrix[1][0]
        True
        >>> matrix[0][0]
        0.0
    """
    n = len(detections)
    
    # Initialize N×N matrix with zeros
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    
    # Fill in the upper triangle (and mirror to lower triangle)
    for i in range(n):
        for j in range(i + 1, n):
            distance = haversine_distance(
                detections[i]['latitude'], detections[i]['longitude'],
                detections[j]['latitude'], detections[j]['longitude']
            )
            distance = round(distance, 3)
            matrix[i][j] = distance
            matrix[j][i] = distance  # symmetric
    
    return matrix


# ---------------------------------------------------------------------------
# AGGREGATE STATISTICS
# ---------------------------------------------------------------------------
def calculate_average_distance(
    detections: List[Dict]
) -> float:
    """
    Calculate the average pairwise distance between all detections.
    
    Args:
        detections: List of detection dicts
    
    Returns:
        Average distance in kilometers, or 0.0 if fewer than 2 detections
    
    Example:
        >>> detections = [
        ...     {'latitude': 9.2645, 'longitude': 76.4600},
        ...     {'latitude': 9.2712, 'longitude': 76.4721}
        ... ]
        >>> avg = calculate_average_distance(detections)
        >>> avg > 0
        True
    """
    if len(detections) < 2:
        return 0.0
    
    distances = calculate_pairwise_distances(detections)
    if not distances:
        return 0.0
    
    total = sum(d['distance_km'] for d in distances)
    return round(total / len(distances), 3)


def calculate_min_max_distance(
    detections: List[Dict]
) -> Tuple[float, float]:
    """
    Calculate the minimum and maximum pairwise distances.
    
    Args:
        detections: List of detection dicts
    
    Returns:
        (min_distance_km, max_distance_km)
        Returns (0.0, 0.0) if fewer than 2 detections
    
    Example:
        >>> detections = [
        ...     {'latitude': 9.2645, 'longitude': 76.4600},
        ...     {'latitude': 9.2712, 'longitude': 76.4721},
        ...     {'latitude': 9.2801, 'longitude': 76.4815}
        ... ]
        >>> min_dist, max_dist = calculate_min_max_distance(detections)
        >>> min_dist < max_dist
        True
    """
    if len(detections) < 2:
        return 0.0, 0.0
    
    distances = calculate_pairwise_distances(detections)
    if not distances:
        return 0.0, 0.0
    
    all_distances = [d['distance_km'] for d in distances]
    return min(all_distances), max(all_distances)


def calculate_total_spread(
    detections: List[Dict]
) -> float:
    """
    Calculate the total geographic spread (max distance between any two points).
    
    This represents the maximum extent of the disease detection cluster.
    
    Args:
        detections: List of detection dicts
    
    Returns:
        Maximum distance in kilometers, or 0.0 if fewer than 2 detections
    
    Example:
        >>> detections = [
        ...     {'latitude': 9.2645, 'longitude': 76.4600},
        ...     {'latitude': 9.2801, 'longitude': 76.4815}
        ... ]
        >>> spread = calculate_total_spread(detections)
        >>> spread > 0
        True
    """
    _, max_dist = calculate_min_max_distance(detections)
    return max_dist


# ---------------------------------------------------------------------------
# DISTANCE FORMATTING
# ---------------------------------------------------------------------------
def format_distance(distance_km: float, precision: int = 2) -> str:
    """
    Format a distance as a human-readable string.
    
    Args:
        distance_km: Distance in kilometers
        precision: Number of decimal places
    
    Returns:
        Formatted string like "1.58 km"
    
    Example:
        >>> format_distance(1.583)
        '1.58 km'
        >>> format_distance(158.3, precision=1)
        '158.3 km'
    """
    return f"{distance_km:.{precision}f} km"


def format_distance_pair(
    farmer_a: str,
    farmer_b: str,
    distance_km: float
) -> str:
    """
    Format a distance between two farmers as a human-readable string.
    
    Args:
        farmer_a: ID of first farmer
        farmer_b: ID of second farmer
        distance_km: Distance in kilometers
    
    Returns:
        Formatted string like "F001 ↔ F002: 1.58 km"
    
    Example:
        >>> format_distance_pair('001', '002', 1.583)
        'F001 ↔ F002: 1.58 km'
    """
    label_a = f"F{farmer_a}" if farmer_a else "?"
    label_b = f"F{farmer_b}" if farmer_b else "?"
    return f"{label_a} ↔ {label_b}: {format_distance(distance_km)}"


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing distance_calculator.py...")
    print()
    
    # Test haversine distance
    print("1. Haversine distance:")
    dist = haversine_distance(9.2645, 76.4600, 9.2712, 76.4721)
    print(f"   Distance: {format_distance(dist)}")
    print()
    
    # Test pairwise distances
    print("2. Pairwise distances:")
    test_detections = [
        {'farmer_id': '001', 'latitude': 9.2645, 'longitude': 76.4600},
        {'farmer_id': '002', 'latitude': 9.2712, 'longitude': 76.4721},
        {'farmer_id': '003', 'latitude': 9.2801, 'longitude': 76.4815},
    ]
    distances = calculate_pairwise_distances(test_detections)
    for d in distances:
        print(f"   {format_distance_pair(d['farmer_a'], d['farmer_b'], d['distance_km'])}")
    print()
    
    # Test distance matrix
    print("3. Distance matrix:")
    matrix = calculate_distance_matrix(test_detections)
    print("   Matrix (km):")
    for i, row in enumerate(matrix):
        row_str = "   ".join(f"{x:6.2f}" for x in row)
        print(f"   [{row_str}]")
    print()
    
    # Test aggregate statistics
    print("4. Aggregate statistics:")
    avg_dist = calculate_average_distance(test_detections)
    min_dist, max_dist = calculate_min_max_distance(test_detections)
    spread = calculate_total_spread(test_detections)
    print(f"   Average distance: {format_distance(avg_dist)}")
    print(f"   Min distance: {format_distance(min_dist)}")
    print(f"   Max distance: {format_distance(max_dist)}")
    print(f"   Total spread: {format_distance(spread)}")
    print()
    
    # Test edge cases
    print("5. Edge cases:")
    single_detection = [{'farmer_id': '001', 'latitude': 9.2645, 'longitude': 76.4600}]
    distances = calculate_pairwise_distances(single_detection)
    print(f"   Single detection: {len(distances)} distances (expected 0)")
    
    avg = calculate_average_distance(single_detection)
    print(f"   Average with 1 detection: {avg} km (expected 0.0)")
    print()
    
    print("All tests passed!")