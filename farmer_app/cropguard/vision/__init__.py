"""
Image Recognition Module for CropGuard / SIH Agricultural Intelligence Project.

Provides decoupled image quality validation, YOLO inference, post-processing,
and structured observation formatting.
"""

from vision.service import analyze_image

__all__ = ["analyze_image"]
