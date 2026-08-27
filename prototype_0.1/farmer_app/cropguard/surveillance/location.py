#!/usr/bin/env python3
"""
location.py — Location data provider for surveillance observations.

This module provides functions to:
  1. Generate or retrieve latitude/longitude coordinates for observations
  2. Start with dummy/mock data for the prototype
  3. Be structured for easy replacement with real GPS/device location APIs later

Current implementation uses a fixed pool of dummy coordinates.
Later: replace generate_dummy_location() with get_real_location(device_id)
       without changing the rest of the architecture.
"""

import random
from typing import Tuple, Optional, Dict, List


# ---------------------------------------------------------------------------
# DUMMY LOCATION POOL — Kerala/India region coordinates
# Replace with real GPS data from devices or farmer profiles later
# ---------------------------------------------------------------------------
DUMMY_LOCATIONS = [
    (9.2645, 76.4600),  # Alappuzha region
    (9.2712, 76.4721),  # Kottayam region
    (9.2801, 76.4815),  # Pathanamthitta region
    (9.2910, 76.4930),  # Idukki region
    (9.3025, 76.5045),  # Ernakulam region
    (9.3150, 76.5160),  # Thrissur region
    (9.3280, 76.5280),  # Palakkad region
    (9.3415, 76.5405),  # Malappuram region
]


# ---------------------------------------------------------------------------
# LOCATION GENERATION
# ---------------------------------------------------------------------------
def generate_dummy_location(index: int = 0) -> Tuple[float, float]:
    """
    Generate a dummy location from the fixed pool.
    
    Args:
        index: Index to select from DUMMY_LOCATIONS pool.
               Cycles through the pool using modulo.
    
    Returns:
        (latitude, longitude) tuple
    
    Example:
        >>> lat, lon = generate_dummy_location(0)
        >>> print(f"Location: {lat}, {lon}")
        Location: 9.2645, 76.46
    """
    return DUMMY_LOCATIONS[index % len(DUMMY_LOCATIONS)]


def generate_random_location() -> Tuple[float, float]:
    """
    Generate a random location from the dummy pool.
    
    Returns:
        (latitude, longitude) tuple
    
    Example:
        >>> lat, lon = generate_random_location()
        >>> 9.0 < lat < 10.0 and 76.0 < lon < 77.0
        True
    """
    return random.choice(DUMMY_LOCATIONS)


def get_location_for_observation(
    observation: Dict,
    index: int = 0
) -> Tuple[float, float]:
    """
    Get location coordinates for an observation.
    
    Current implementation: uses dummy data based on index.
    Future implementation: could read from:
      - observation['latitude'] / observation['longitude'] (if present)
      - Device GPS data linked by device_id
      - Farmer profile location linked by farmer_id
    
    Args:
        observation: Observation dict from observations.json
        index: Index for dummy location selection
    
    Returns:
        (latitude, longitude) tuple
    
    Example:
        >>> obs = {'observation_id': 'OBS-001', 'farmer_id': '001'}
        >>> lat, lon = get_location_for_observation(obs, 0)
        >>> print(f"{lat}, {lon}")
        9.2645, 76.46
    """
    # FUTURE: Check if observation already has location data
    # if 'latitude' in observation and 'longitude' in observation:
    #     return (observation['latitude'], observation['longitude'])
    
    # FUTURE: Look up device GPS or farmer profile
    # device_id = observation.get('device_id')
    # if device_id:
    #     return get_device_location(device_id)
    
    # CURRENT: Use dummy data
    return generate_dummy_location(index)


# ---------------------------------------------------------------------------
# LOCATION FORMATTING
# ---------------------------------------------------------------------------
def format_location(latitude: float, longitude: float, precision: int = 4) -> str:
    """
    Format a location as a human-readable string.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        precision: Number of decimal places (default: 4)
    
    Returns:
        Formatted string like "9.2645, 76.4600"
    
    Example:
        >>> format_location(9.2645, 76.4600)
        '9.2645, 76.4600'
    """
    return f"{latitude:.{precision}f}, {longitude:.{precision}f}"


def parse_location(location_str: str) -> Optional[Tuple[float, float]]:
    """
    Parse a location string into (latitude, longitude) tuple.
    
    Args:
        location_str: String like "9.2645, 76.4600"
    
    Returns:
        (latitude, longitude) tuple, or None if parsing fails
    
    Example:
        >>> parse_location("9.2645, 76.4600")
        (9.2645, 76.46)
        >>> parse_location("invalid")
        None
    """
    try:
        parts = location_str.split(",")
        if len(parts) != 2:
            return None
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return (lat, lon)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# LOCATION VALIDATION
# ---------------------------------------------------------------------------
def is_valid_location(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are within valid ranges.
    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
    
    Returns:
        True if coordinates are valid, False otherwise
    
    Example:
        >>> is_valid_location(9.2645, 76.4600)
        True
        >>> is_valid_location(100.0, 76.4600)
        False
    """
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def is_in_kerala_region(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are roughly within Kerala, India region.
    
    This is a rough bounding box for the prototype.
    Kerala is approximately:
      - Latitude: 8.17°N to 12.79°N
      - Longitude: 74.85°E to 77.39°E
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        True if coordinates are within Kerala region
    
    Example:
        >>> is_in_kerala_region(9.2645, 76.4600)
        True
        >>> is_in_kerala_region(28.6139, 77.2090)  # Delhi
        False
    """
    return (8.17 <= latitude <= 12.79 and 
            74.85 <= longitude <= 77.39)


# ---------------------------------------------------------------------------
# FUTURE: REAL LOCATION SERVICES
# ---------------------------------------------------------------------------
def get_device_location(device_id: str) -> Optional[Tuple[float, float]]:
    """
    FUTURE: Retrieve real location from device GPS or registration data.
    
    Current implementation: returns None (not implemented).
    Future implementation could:
      - Query a device registry database
      - Call a GPS tracking API
      - Read from farmer profile
    
    Args:
        device_id: Device identifier
    
    Returns:
        (latitude, longitude) tuple, or None if not available
    
    Example:
        >>> location = get_device_location("DEV-001")
        >>> if location:
        ...     lat, lon = location
    """
    # TODO: Implement real device location lookup
    # This is where you'd integrate with:
    # - Device registration database
    # - GPS tracking service
    # - Farmer profile location data
    return None


def get_farmer_location(farmer_id: str) -> Optional[Tuple[float, float]]:
    """
    FUTURE: Retrieve location from farmer profile or registration.
    
    Current implementation: returns None (not implemented).
    Future implementation could:
      - Query farmer database
      - Use farm registration GPS coordinates
      - Geocode farmer address
    
    Args:
        farmer_id: Farmer identifier
    
    Returns:
        (latitude, longitude) tuple, or None if not available
    """
    # TODO: Implement real farmer location lookup
    return None


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing location.py...")
    print()
    
    # Test dummy location generation
    print("Dummy locations:")
    for i in range(5):
        lat, lon = generate_dummy_location(i)
        print(f"  Index {i}: {format_location(lat, lon)}")
    
    print()
    
    # Test random location
    print("Random location:")
    lat, lon = generate_random_location()
    print(f"  {format_location(lat, lon)}")
    
    print()
    
    # Test validation
    print("Location validation:")
    test_coords = [
        (9.2645, 76.4600, "Kerala"),
        (28.6139, 77.2090, "Delhi"),
        (100.0, 76.4600, "Invalid lat"),
    ]
    for lat, lon, desc in test_coords:
        valid = is_valid_location(lat, lon)
        in_kerala = is_in_kerala_region(lat, lon)
        print(f"  {desc}: valid={valid}, in_kerala={in_kerala}")
    
    print()
    
    # Test parsing
    print("Location parsing:")
    test_strings = [
        "9.2645, 76.4600",
        "invalid",
        "9.2645",
    ]
    for s in test_strings:
        result = parse_location(s)
        print(f"  '{s}' → {result}")
    
    print()
    print("All tests passed!")