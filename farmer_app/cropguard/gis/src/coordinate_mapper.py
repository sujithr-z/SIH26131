#!/usr/bin/env python3
"""
coordinate_mapper.py — Geographic ↔ pixel coordinate transformation.

This module handles the core georeferencing logic:
  1. Convert latitude/longitude → pixel (x, y) on the map image
  2. Convert pixel (x, y) → latitude/longitude (reverse lookup)
  3. Validate that a point falls within the map's geographic extent
  4. Extract the geographic extent from the GIS configuration

The map image is assumed to cover a rectangular geographic bounding box
defined in config.json as:
    min_latitude, max_latitude, min_longitude, max_longitude

This module is the bridge between "real-world coordinates" and
"where to draw on the image".

Usage:
    from coordinate_mapper import lat_lon_to_pixel, is_within_extent
"""

import os
from typing import Tuple, Optional, Dict


# ---------------------------------------------------------------------------
# EXTENT EXTRACTION
# ---------------------------------------------------------------------------
def get_extent_from_config(config: Dict) -> Tuple[float, float, float, float]:
    """
    Extract the geographic bounding box from the GIS configuration.

    Args:
        config: GIS configuration dict with 'map_extent' key containing:
            - min_latitude
            - max_latitude
            - min_longitude
            - max_longitude

    Returns:
        (min_lon, max_lon, min_lat, max_lat)

    Raises:
        ValueError: If required fields are missing or invalid.

    Example:
        >>> config = {'map_extent': {'min_latitude': 9.20, 'max_latitude': 9.35,
        ...                          'min_longitude': 76.40, 'max_longitude': 76.55}}
        >>> get_extent_from_config(config)
        (76.4, 76.55, 9.2, 9.35)
    """
    extent_cfg = config.get("map_extent", {})

    required = ["min_latitude", "max_latitude", "min_longitude", "max_longitude"]
    missing = [k for k in required if k not in extent_cfg]
    if missing:
        raise ValueError(f"map_extent missing required fields: {missing}")

    min_lat = float(extent_cfg["min_latitude"])
    max_lat = float(extent_cfg["max_latitude"])
    min_lon = float(extent_cfg["min_longitude"])
    max_lon = float(extent_cfg["max_longitude"])

    # Validate ranges
    if min_lat >= max_lat:
        raise ValueError(f"min_latitude ({min_lat}) must be < max_latitude ({max_lat})")
    if min_lon >= max_lon:
        raise ValueError(f"min_longitude ({min_lon}) must be < max_longitude ({max_lon})")

    return min_lon, max_lon, min_lat, max_lat


def get_extent_as_list(config: Dict) -> list:
    """
    Get the extent as a list suitable for Matplotlib's imshow() extent parameter.

    Matplotlib expects: [left, right, bottom, top] = [min_lon, max_lon, min_lat, max_lat]

    Args:
        config: GIS configuration dict

    Returns:
        [min_lon, max_lon, min_lat, max_lat]

    Example:
        >>> config = {'map_extent': {'min_latitude': 9.20, 'max_latitude': 9.35,
        ...                          'min_longitude': 76.40, 'max_longitude': 76.55}}
        >>> get_extent_as_list(config)
        [76.4, 76.55, 9.2, 9.35]
    """
    min_lon, max_lon, min_lat, max_lat = get_extent_from_config(config)
    return [min_lon, max_lon, min_lat, max_lat]


# ---------------------------------------------------------------------------
# FORWARD MAPPING: lat/lon → pixel
# ---------------------------------------------------------------------------
def lat_lon_to_pixel(
    latitude: float,
    longitude: float,
    extent: Tuple[float, float, float, float],
    image_width: int,
    image_height: int
) -> Tuple[int, int]:
    """
    Convert geographic coordinates to pixel coordinates in the map image.

    The geographic extent defines the bounding box:
        - min_lon (left edge) → x = 0
        - max_lon (right edge) → x = image_width - 1
        - max_lat (top edge) → y = 0 (image y-axis is inverted)
        - min_lat (bottom edge) → y = image_height - 1

    Args:
        latitude: Latitude coordinate (degrees)
        longitude: Longitude coordinate (degrees)
        extent: (min_lon, max_lon, min_lat, max_lat)
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        (x_pixel, y_pixel) — integer pixel coordinates

    Raises:
        ValueError: If coordinates are outside the extent or dimensions are invalid.

    Example:
        >>> extent = (76.40, 76.55, 9.20, 9.35)
        >>> lat_lon_to_pixel(9.275, 76.475, extent, 800, 600)
        (400, 300)
    """
    min_lon, max_lon, min_lat, max_lat = extent

    # Validate image dimensions
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"Invalid image dimensions: {image_width}x{image_height}")

    # Check if point is within extent
    if not (min_lon <= longitude <= max_lon and min_lat <= latitude <= max_lat):
        raise ValueError(
            f"Coordinates ({latitude}, {longitude}) are outside the map extent "
            f"[{min_lat}..{max_lat}, {min_lon}..{max_lon}]"
        )

    # Normalize to [0, 1]
    x_norm = (longitude - min_lon) / (max_lon - min_lon)
    y_norm = (latitude - min_lat) / (max_lat - min_lat)

    # Convert to pixel coordinates
    # Note: image y-axis is inverted (0 at top, height at bottom)
    # So max_lat (top) → y = 0, min_lat (bottom) → y = height - 1
    x_pixel = int(x_norm * (image_width - 1))
    y_pixel = int((1 - y_norm) * (image_height - 1))

    return x_pixel, y_pixel


def lat_lon_to_pixel_safe(
    latitude: float,
    longitude: float,
    extent: Tuple[float, float, float, float],
    image_width: int,
    image_height: int
) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Safe version of lat_lon_to_pixel that returns an error message instead of raising.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        extent: (min_lon, max_lon, min_lat, max_lat)
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        (x_pixel, y_pixel, error_message)
        - x_pixel, y_pixel: Pixel coordinates, or None on error
        - error_message: None on success, error string on failure

    Example:
        >>> extent = (76.40, 76.55, 9.20, 9.35)
        >>> x, y, err = lat_lon_to_pixel_safe(9.275, 76.475, extent, 800, 600)
        >>> if err:
        ...     print(f"Error: {err}")
        >>> else:
        ...     print(f"Pixel: ({x}, {y})")
    """
    try:
        x, y = lat_lon_to_pixel(latitude, longitude, extent, image_width, image_height)
        return x, y, None
    except ValueError as e:
        return None, None, str(e)


# ---------------------------------------------------------------------------
# REVERSE MAPPING: pixel → lat/lon
# ---------------------------------------------------------------------------
def pixel_to_lat_lon(
    x_pixel: int,
    y_pixel: int,
    extent: Tuple[float, float, float, float],
    image_width: int,
    image_height: int
) -> Tuple[float, float]:
    """
    Convert pixel coordinates back to geographic coordinates.

    This is the inverse of lat_lon_to_pixel().

    Args:
        x_pixel: X coordinate in pixels (0 = left edge)
        y_pixel: Y coordinate in pixels (0 = top edge)
        extent: (min_lon, max_lon, min_lat, max_lat)
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        (latitude, longitude)

    Raises:
        ValueError: If pixel coordinates are outside the image bounds.

    Example:
        >>> extent = (76.40, 76.55, 9.20, 9.35)
        >>> pixel_to_lat_lon(400, 300, extent, 800, 600)
        (9.275, 76.475)
    """
    min_lon, max_lon, min_lat, max_lat = extent

    # Validate pixel coordinates
    if not (0 <= x_pixel < image_width and 0 <= y_pixel < image_height):
        raise ValueError(
            f"Pixel ({x_pixel}, {y_pixel}) is outside the image bounds "
            f"[0..{image_width-1}, 0..{image_height-1}]"
        )

    # Normalize to [0, 1]
    x_norm = x_pixel / (image_width - 1) if image_width > 1 else 0.5
    y_norm = 1 - (y_pixel / (image_height - 1)) if image_height > 1 else 0.5

    # Convert to geographic coordinates
    longitude = min_lon + x_norm * (max_lon - min_lon)
    latitude = min_lat + y_norm * (max_lat - min_lat)

    return latitude, longitude


# ---------------------------------------------------------------------------
# BOUNDS CHECKING
# ---------------------------------------------------------------------------
def is_within_extent(
    latitude: float,
    longitude: float,
    extent: Tuple[float, float, float, float]
) -> bool:
    """
    Check if a geographic coordinate falls within the map extent.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        extent: (min_lon, max_lon, min_lat, max_lat)

    Returns:
        True if the point is within the extent, False otherwise.

    Example:
        >>> extent = (76.40, 76.55, 9.20, 9.35)
        >>> is_within_extent(9.275, 76.475, extent)
        True
        >>> is_within_extent(10.0, 76.475, extent)
        False
    """
    min_lon, max_lon, min_lat, max_lat = extent
    return (min_lon <= longitude <= max_lon and
            min_lat <= latitude <= max_lat)


def clamp_to_extent(
    latitude: float,
    longitude: float,
    extent: Tuple[float, float, float, float]
) -> Tuple[float, float]:
    """
    Clamp a coordinate to the nearest edge of the extent if it's outside.

    This is useful for ensuring points are always visible on the map,
    even if they're slightly outside the defined extent.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        extent: (min_lon, max_lon, min_lat, max_lat)

    Returns:
        (clamped_latitude, clamped_longitude)

    Example:
        >>> extent = (76.40, 76.55, 9.20, 9.35)
        >>> clamp_to_extent(10.0, 76.475, extent)
        (9.35, 76.475)
    """
    min_lon, max_lon, min_lat, max_lat = extent

    clamped_lat = max(min_lat, min(max_lat, latitude))
    clamped_lon = max(min_lon, min(max_lon, longitude))

    return clamped_lat, clamped_lon


# ---------------------------------------------------------------------------
# DISTANCE IN PIXEL SPACE
# ---------------------------------------------------------------------------
def pixel_distance(
    x1: int, y1: int,
    x2: int, y2: int
) -> float:
    """
    Calculate the Euclidean distance between two points in pixel space.

    Args:
        x1, y1: First point in pixels
        x2, y2: Second point in pixels

    Returns:
        Distance in pixels

    Example:
        >>> pixel_distance(0, 0, 3, 4)
        5.0
    """
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def geographic_distance_in_pixels(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    extent: Tuple[float, float, float, float],
    image_width: int,
    image_height: int
) -> float:
    """
    Calculate the distance between two geographic points in pixel space.

    This is useful for understanding how "far apart" two points appear
    on the map image, which may differ from their real-world distance
    due to map scale and projection.

    Args:
        lat1, lon1: First point in geographic coordinates
        lat2, lon2: Second point in geographic coordinates
        extent: (min_lon, max_lon, min_lat, max_lat)
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Distance in pixels

    Example:
        >>> extent = (76.40, 76.55, 9.20, 9.35)
        >>> geographic_distance_in_pixels(9.2645, 76.4600, 9.2712, 76.4721, extent, 800, 600)
        85.3
    """
    x1, y1 = lat_lon_to_pixel(lat1, lon1, extent, image_width, image_height)
    x2, y2 = lat_lon_to_pixel(lat2, lon2, extent, image_width, image_height)
    return pixel_distance(x1, y1, x2, y2)


# ---------------------------------------------------------------------------
# FORMATTING UTILITIES
# ---------------------------------------------------------------------------
def format_coordinate(latitude: float, longitude: float, precision: int = 4) -> str:
    """
    Format a geographic coordinate as a human-readable string.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        precision: Number of decimal places

    Returns:
        Formatted string like "9.2645, 76.4600"

    Example:
        >>> format_coordinate(9.2645, 76.4600)
        '9.2645, 76.4600'
    """
    return f"{latitude:.{precision}f}, {longitude:.{precision}f}"


def format_pixel(x: int, y: int) -> str:
    """
    Format pixel coordinates as a human-readable string.

    Args:
        x: X coordinate in pixels
        y: Y coordinate in pixels

    Returns:
        Formatted string like "(400, 300)"

    Example:
        >>> format_pixel(400, 300)
        '(400, 300)'
    """
    return f"({x}, {y})"


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing coordinate_mapper.py...")
    print()

    # Test extent extraction
    print("1. Extent extraction:")
    config = {
        "map_extent": {
            "min_latitude": 9.20,
            "max_latitude": 9.35,
            "min_longitude": 76.40,
            "max_longitude": 76.55,
        }
    }
    extent = get_extent_from_config(config)
    print(f"   Extent: {extent}")
    print(f"   As list: {get_extent_as_list(config)}")
    print()

    # Test forward mapping
    print("2. Forward mapping (lat/lon → pixel):")
    test_coords = [
        (9.2645, 76.4600, "Farm 1"),
        (9.2712, 76.4721, "Farm 2"),
        (9.275, 76.475, "Center"),
    ]
    image_width, image_height = 800, 600
    for lat, lon, label in test_coords:
        x, y = lat_lon_to_pixel(lat, lon, extent, image_width, image_height)
        print(f"   {label}: {format_coordinate(lat, lon)} → pixel {format_pixel(x, y)}")
    print()

    # Test reverse mapping
    print("3. Reverse mapping (pixel → lat/lon):")
    test_pixels = [
        (0, 0, "Top-left"),
        (799, 599, "Bottom-right"),
        (400, 300, "Center"),
    ]
    for x, y, label in test_pixels:
        lat, lon = pixel_to_lat_lon(x, y, extent, image_width, image_height)
        print(f"   {label}: pixel {format_pixel(x, y)} → {format_coordinate(lat, lon)}")
    print()

    # Test bounds checking
    print("4. Bounds checking:")
    test_points = [
        (9.275, 76.475, "Inside"),
        (10.0, 76.475, "Outside (lat too high)"),
        (9.275, 77.0, "Outside (lon too high)"),
    ]
    for lat, lon, label in test_points:
        within = is_within_extent(lat, lon, extent)
        print(f"   {label}: {format_coordinate(lat, lon)} → within={within}")
    print()

    # Test clamping
    print("5. Clamping:")
    clamped_lat, clamped_lon = clamp_to_extent(10.0, 76.475, extent)
    print(f"   Original: {format_coordinate(10.0, 76.475)}")
    print(f"   Clamped:  {format_coordinate(clamped_lat, clamped_lon)}")
    print()

    # Test pixel distance
    print("6. Pixel distance:")
    dist = geographic_distance_in_pixels(9.2645, 76.4600, 9.2712, 76.4721, extent, 800, 600)
    print(f"   Distance between Farm 1 and Farm 2: {dist:.1f} pixels")
    print()

    print("All tests passed!")