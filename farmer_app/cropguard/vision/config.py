"""
Configuration settings for the Vision Image Recognition Module.
"""

import os
from pathlib import Path

# Base paths
MODULE_DIR = Path(__file__).parent.resolve()
APP_ROOT = MODULE_DIR.parent.resolve()
YOLO_REPO_DIR = APP_ROOT / "YOLO-Based-Automatic-Crop-Disease-Detection-for-Smart-Agriculture-main"

# Model weights resolution
# Default trained model
DEFAULT_MODEL_PATH = YOLO_REPO_DIR / "plant_disease" / "exp1" / "weights" / "best.pt"
FALLBACK_MODEL_PATH = YOLO_REPO_DIR / "yolov8s.pt"

# Inference parameters
MODEL_VERSION = "yolo-agri-v1"
DEFAULT_CONF_THRESHOLD = 0.25
DEFAULT_IOU_THRESHOLD = 0.45
DEFAULT_IMG_SIZE = 640

# Image Quality Gate parameters
MIN_IMAGE_DIMENSION = 120      # Minimum width/height in pixels
MAX_IMAGE_DIMENSION = 8192     # Maximum width/height in pixels
BLUR_VARIANCE_THRESHOLD = 30.0 # Laplacian variance below this flags blurry image

# Standardized PlantVillage class mapping
# Maps raw YOLO/PlantVillage class indices or labels to clean (Crop, Disease) pairs
PLANTVILLAGE_CLASSES = {
    0: {"crop": "Apple", "disease": "Apple Scab", "is_healthy": False},
    1: {"crop": "Apple", "disease": "Black Rot", "is_healthy": False},
    2: {"crop": "Apple", "disease": "Cedar Apple Rust", "is_healthy": False},
    3: {"crop": "Apple", "disease": "Healthy", "is_healthy": True},
    4: {"crop": "Blueberry", "disease": "Healthy", "is_healthy": True},
    5: {"crop": "Cherry", "disease": "Powdery Mildew", "is_healthy": False},
    6: {"crop": "Cherry", "disease": "Healthy", "is_healthy": True},
    7: {"crop": "Corn", "disease": "Cercospora Leaf Spot / Gray Leaf Spot", "is_healthy": False},
    8: {"crop": "Corn", "disease": "Common Rust", "is_healthy": False},
    9: {"crop": "Corn", "disease": "Northern Leaf Blight", "is_healthy": False},
}

# String name aliases for flexible mapping
CLASS_NAME_ALIASES = {
    "apple___apple_scab": {"crop": "Apple", "disease": "Apple Scab", "is_healthy": False},
    "apple___black_rot": {"crop": "Apple", "disease": "Black Rot", "is_healthy": False},
    "apple___cedar_apple_rust": {"crop": "Apple", "disease": "Cedar Apple Rust", "is_healthy": False},
    "apple___healthy": {"crop": "Apple", "disease": "Healthy", "is_healthy": True},
    "blueberry___healthy": {"crop": "Blueberry", "disease": "Healthy", "is_healthy": True},
    "cherry_(including_sour)___powdery_mildew": {"crop": "Cherry", "disease": "Powdery Mildew", "is_healthy": False},
    "cherry_(including_sour)___healthy": {"crop": "Cherry", "disease": "Healthy", "is_healthy": True},
    "corn_(maize)___cercospora_leaf_spot gray_leaf_spot": {"crop": "Corn", "disease": "Cercospora Leaf Spot", "is_healthy": False},
    "corn_(maize)___common_rust_": {"crop": "Corn", "disease": "Common Rust", "is_healthy": False},
    "corn_(maize)___northern_leaf_blight": {"crop": "Corn", "disease": "Northern Leaf Blight", "is_healthy": False},
    "tomato___early_blight": {"crop": "Tomato", "disease": "Early Blight", "is_healthy": False},
    "tomato___late_blight": {"crop": "Tomato", "disease": "Late Blight", "is_healthy": False},
    "tomato___bacterial_spot": {"crop": "Tomato", "disease": "Bacterial Spot", "is_healthy": False},
    "tomato___healthy": {"crop": "Tomato", "disease": "Healthy", "is_healthy": True},
}
