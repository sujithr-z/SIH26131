#!/usr/bin/env python3
"""
map_loader.py — Map image loading and validation module.

This module provides functions to:
  1. Load a base map image from disk
  2. Validate the image is readable and has correct dimensions
  3. Provide a fallback placeholder when no map is available
  4. Return image data ready for Matplotlib rendering

Current implementation loads PNG/JPG images from the filesystem.
Later: could load from URLs, cloud storage, or generate dynamic maps.
"""

import os
from typing import Tuple, Optional, Any

import matplotlib.image as mpimg
import numpy as np


# ---------------------------------------------------------------------------
# PATHS — resolved relative to this module
# ---------------------------------------------------------------------------
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAP_PATH = os.path.join(MODULE_DIR, "input", "sample_map.png")


# ---------------------------------------------------------------------------
# MAP LOADING
# ---------------------------------------------------------------------------
def load_map_image(map_path: str = None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Load a map image from disk.
    
    Args:
        map_path: Path to the map image file.
                  Defaults to input/sample_map.png
    
    Returns:
        (image_array, error_message)
        - image_array: NumPy array of the image (RGB or RGBA), or None on failure
        - error_message: None on success, error string on failure
    
    Example:
        >>> img, err = load_map_image("input/sample_map.png")
        >>> if err:
        ...     print(f"Error: {err}")
        >>> else:
        ...     print(f"Loaded image: {img.shape}")
    """
    path = map_path or DEFAULT_MAP_PATH
    
    if not os.path.exists(path):
        return None, "Map image not found: {}".format(path)
    
    try:
        img = mpimg.imread(path)
        
        # Validate it's a valid image array
        if not isinstance(img, np.ndarray):
            return None, "Loaded file is not a valid image array."
        
        if img.ndim not in [2, 3]:
            return None, "Image has unexpected dimensions: {}".format(img.ndim)
        
        return img, None
    
    except Exception as e:
        return None, "Could not load map image: {}".format(e)


def validate_image_dimensions(
    image: Any,
    min_width: int = 100,
    min_height: int = 100
) -> Tuple[bool, str]:
    """
    Validate that an image has acceptable dimensions.
    
    Args:
        image: NumPy array of the image
        min_width: Minimum acceptable width in pixels
        min_height: Minimum acceptable height in pixels
    
    Returns:
        (is_valid, message)
        - is_valid: True if dimensions are acceptable
        - message: Description of the dimensions or error
    
    Example:
        >>> img, _ = load_map_image()
        >>> valid, msg = validate_image_dimensions(img)
        >>> print(msg)
        'Image dimensions: 1920x1080'
    """
    if image is None:
        return False, "Image is None"
    
    try:
        if image.ndim == 2:
            # Grayscale
            height, width = image.shape
        elif image.ndim == 3:
            # RGB or RGBA
            height, width = image.shape[:2]
        else:
            return False, "Unexpected image dimensions"
        
        if width < min_width or height < min_height:
            return False, f"Image too small: {width}x{height} (minimum {min_width}x{min_height})"
        
        return True, f"Image dimensions: {width}x{height}"
    
    except Exception as e:
        return False, f"Could not validate dimensions: {e}"


def get_image_info(image: Any) -> dict:
    """
    Get metadata about a loaded image.
    
    Args:
        image: NumPy array of the image
    
    Returns:
        Dict with image metadata
    
    Example:
        >>> img, _ = load_map_image()
        >>> info = get_image_info(img)
        >>> print(info)
        {'width': 1920, 'height': 1080, 'channels': 3, 'dtype': 'uint8'}
    """
    if image is None:
        return {"error": "Image is None"}
    
    try:
        if image.ndim == 2:
            height, width = image.shape
            channels = 1
        elif image.ndim == 3:
            height, width, channels = image.shape
        else:
            return {"error": "Unexpected dimensions"}
        
        return {
            "width": width,
            "height": height,
            "channels": channels,
            "dtype": str(image.dtype),
            "size_mb": round(image.nbytes / (1024 * 1024), 2),
        }
    
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# FALLBACK MAP GENERATION
# ---------------------------------------------------------------------------
def create_placeholder_map(
    width: int = 800,
    height: int = 600,
    background_color: Tuple[int, int, int] = (232, 240, 232)
) -> np.ndarray:
    """
    Create a simple placeholder map image when no real map is available.
    
    This generates a light green background with a grid pattern,
    suitable for demonstrating the GIS visualization without a real
    satellite/base map.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        background_color: RGB tuple (0-255) for background
    
    Returns:
        NumPy array of the placeholder image (RGB, uint8)
    
    Example:
        >>> placeholder = create_placeholder_map(800, 600)
        >>> placeholder.shape
        (600, 800, 3)
    """
    # Create base color
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = background_color
    
    # Add grid lines
    grid_spacing = 50
    grid_color = (200, 200, 200)
    
    for x in range(0, width, grid_spacing):
        img[:, x] = grid_color
    
    for y in range(0, height, grid_spacing):
        img[y, :] = grid_color
    
    return img


def get_map_with_fallback(map_path: str = None) -> Tuple[Any, bool, str]:
    """
    Load a map image, or create a placeholder if loading fails.
    
    This is the main entry point for most use cases — it ensures
    you always get an image, even if the real map is missing.
    
    Args:
        map_path: Path to the map image file
    
    Returns:
        (image, is_real_map, message)
        - image: NumPy array of the image
        - is_real_map: True if loaded from file, False if placeholder
        - message: Description of what happened
    
    Example:
        >>> img, is_real, msg = get_map_with_fallback()
        >>> if is_real:
        ...     print("Loaded real map")
        >>> else:
        ...     print("Using placeholder")
    """
    img, err = load_map_image(map_path)
    
    if img is not None:
        valid, dim_msg = validate_image_dimensions(img)
        if valid:
            info = get_image_info(img)
            return img, True, f"Loaded real map: {dim_msg}, {info['size_mb']} MB"
        else:
            # Image loaded but dimensions are bad
            placeholder = create_placeholder_map()
            return placeholder, False, f"Map invalid ({dim_msg}), using placeholder"
    
    # Loading failed
    placeholder = create_placeholder_map()
    return placeholder, False, f"Map not available ({err}), using placeholder"


# ---------------------------------------------------------------------------
# COORDINATE MAPPING UTILITIES
# ---------------------------------------------------------------------------
def calculate_extent_from_config(config: dict) -> list:
    """
    Extract the geographic extent from a config dict.
    
    Args:
        config: GIS configuration dict with 'map_extent' key
    
    Returns:
        [min_lon, max_lon, min_lat, max_lat] for Matplotlib extent parameter
    
    Example:
        >>> config = {'map_extent': {'min_latitude': 9.20, 'max_latitude': 9.35, ...}}
        >>> extent = calculate_extent_from_config(config)
        >>> print(extent)
        [76.40, 76.55, 9.20, 9.35]
    """
    extent_cfg = config.get("map_extent", {})
    
    return [
        extent_cfg.get("min_longitude", 76.40),
        extent_cfg.get("max_longitude", 76.55),
        extent_cfg.get("min_latitude", 9.20),
        extent_cfg.get("max_latitude", 9.35),
    ]


def lat_lon_to_pixel(
    latitude: float,
    longitude: float,
    extent: list,
    image_width: int,
    image_height: int
) -> Tuple[int, int]:
    """
    Convert geographic coordinates to pixel coordinates in the image.
    
    This is useful if you need to know exactly where a point falls
    in the image (e.g., for custom annotations).
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        extent: [min_lon, max_lon, min_lat, max_lat]
        image_width: Image width in pixels
        image_height: Image height in pixels
    
    Returns:
        (x_pixel, y_pixel) in image coordinates
    
    Example:
        >>> extent = [76.40, 76.55, 9.20, 9.35]
        >>> x, y = lat_lon_to_pixel(9.275, 76.475, extent, 800, 600)
        >>> print(f"Pixel: ({x}, {y})")
    """
    min_lon, max_lon, min_lat, max_lat = extent
    
    # Normalize to [0, 1]
    x_norm = (longitude - min_lon) / (max_lon - min_lon)
    y_norm = (latitude - min_lat) / (max_lat - min_lat)
    
    # Convert to pixel coordinates
    # Note: image y-axis is inverted (0 at top, height at bottom)
    x_pixel = int(x_norm * image_width)
    y_pixel = int((1 - y_norm) * image_height)
    
    return x_pixel, y_pixel


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing map_loader.py...")
    print()
    
    # Test loading real map
    print("1. Loading map image:")
    img, err = load_map_image()
    if err:
        print(f"   Error: {err}")
    else:
        info = get_image_info(img)
        print(f"   Loaded: {info}")
    
    print()
    
    # Test fallback
    print("2. Testing fallback:")
    img, is_real, msg = get_map_with_fallback()
    print(f"   {msg}")
    print(f"   Is real map: {is_real}")
    print(f"   Image shape: {img.shape}")
    
    print()
    
    # Test coordinate mapping
    print("3. Testing coordinate mapping:")
    extent = [76.40, 76.55, 9.20, 9.35]
    test_coords = [
        (9.2645, 76.4600, "Farm 1"),
        (9.2712, 76.4721, "Farm 2"),
    ]
    for lat, lon, label in test_coords:
        x, y = lat_lon_to_pixel(lat, lon, extent, 800, 600)
        print(f"   {label}: ({lat}, {lon}) → pixel ({x}, {y})")
    
    print()
    print("All tests passed!")