"""
Unified Image Recognition Service Interface.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import time

from vision.preprocessor import ImageQualityGate
from vision.detector import YOLODetector
from vision.postprocessor import PostProcessor
from vision.config import DEFAULT_CONF_THRESHOLD, MODEL_VERSION


def analyze_image(
    image_path: str | Path,
    crop: Optional[str] = None,
    conf_threshold: float = DEFAULT_CONF_THRESHOLD,
    model_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Perform end-to-end crop disease analysis on an image file.

    Parameters:
        image_path: Path to the image file
        crop: Optional crop name hint provided by farmer
        conf_threshold: Confidence threshold for bounding box filtering
        model_path: Optional custom model weights path

    Returns:
        Structured observation dictionary
    """
    start_time = time.time()

    # Step 1: Image Quality Gate
    is_valid, img_cv2, quality_metrics, error_msg = ImageQualityGate.validate_and_load(image_path)
    if not is_valid:
        return {
            "success": False,
            "error": error_msg or "Image validation failed.",
            "crop": crop or "Unknown",
            "disease": "Uncertain / Poor Image Quality",
            "confidence": 0.0,
            "severity": "Low",
            "detections": [],
            "description": f"Image quality gate check failed: {error_msg}. Please capture a sharp, well-illuminated close-up of the affected foliage.",
            "precautions": [
                {
                    "icon": "📷",
                    "title": "Retake Photo",
                    "text": "Ensure good natural lighting, steady focus, and keep the plant leaf centered."
                }
            ],
            "model_version": MODEL_VERSION,
            "image_quality": quality_metrics,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    # Step 2: YOLO Inference
    try:
        detector = YOLODetector.get_detector(model_path)
        raw_results = detector.predict(img_cv2, conf_threshold=conf_threshold)
    except Exception as e:
        return {
            "success": False,
            "error": f"Inference engine error: {str(e)}",
            "crop": crop or "Unknown",
            "disease": "Inference Error",
            "confidence": 0.0,
            "severity": "Low",
            "detections": [],
            "description": "An unexpected error occurred while executing the YOLO model.",
            "precautions": [],
            "model_version": MODEL_VERSION,
            "image_quality": quality_metrics,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    # Step 3: Post-Processing & Structured Formatting
    result = PostProcessor.process(raw_results, quality_metrics, crop_hint=crop)
    result["success"] = True
    result["latency_ms"] = round((time.time() - start_time) * 1000, 2)

    return result
