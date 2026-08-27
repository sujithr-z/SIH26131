"""
Image Preprocessor and Quality Gate for agricultural leaf image validation.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image

from vision.config import (
    MIN_IMAGE_DIMENSION,
    MAX_IMAGE_DIMENSION,
    BLUR_VARIANCE_THRESHOLD
)


class ImageQualityGate:
    """
    Validates uploaded crop images before passing them to the YOLO inference engine.
    Checks:
      - File existence & readability
      - Image dimension constraints
      - Laplacian variance blur detection
    """

    @staticmethod
    def validate_and_load(image_path: str | Path) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any], Optional[str]]:
        """
        Validate image quality and load cv2 image array.

        Returns:
            (is_valid, cv2_image, quality_metrics, error_message)
        """
        path = Path(image_path)
        if not path.exists():
            return False, None, {}, f"Image file not found at path: {image_path}"

        if path.stat().st_size == 0:
            return False, None, {}, "Image file is empty (0 bytes)."

        # Try reading with OpenCV (supporting UTF-8 paths on Windows)
        try:
            # np.fromfile handles Unicode/Windows path oddities cleanly
            img_bytes = np.fromfile(str(path), dtype=np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        except Exception as e:
            return False, None, {}, f"Failed to decode image data: {str(e)}"

        if img is None:
            # Fallback attempt with PIL
            try:
                with Image.open(str(path)) as pil_img:
                    pil_img.verify()
                with Image.open(str(path)) as pil_img:
                    img = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)
            except Exception as e:
                return False, None, {}, f"Invalid or corrupt image format: {str(e)}"

        if img is None or img.size == 0:
            return False, None, {}, "Decoded image matrix is empty."

        h, w, c = img.shape

        # Dimension constraints
        if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
            return False, None, {
                "width": w,
                "height": h,
                "channels": c,
            }, f"Image resolution too low ({w}x{h}). Minimum required is {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION} pixels."

        if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
            # Downscale if excessively massive to save memory
            scale = MAX_IMAGE_DIMENSION / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w, _ = img.shape

        # Blur analysis via Laplacian variance
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < BLUR_VARIANCE_THRESHOLD

        quality_metrics = {
            "width": int(w),
            "height": int(h),
            "channels": int(c),
            "file_size_bytes": int(path.stat().st_size),
            "blur_variance": round(laplacian_var, 2),
            "is_blurry": is_blurry,
            "quality_status": "POOR_BLURRY" if is_blurry else "ACCEPTABLE",
        }

        return True, img, quality_metrics, None
