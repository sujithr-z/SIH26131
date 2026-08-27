"""
YOLO Model Inference Engine using Ultralytics YOLOv8.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch

from vision.config import (
    DEFAULT_MODEL_PATH,
    FALLBACK_MODEL_PATH,
    DEFAULT_CONF_THRESHOLD,
    DEFAULT_IOU_THRESHOLD,
    DEFAULT_IMG_SIZE,
    MODEL_VERSION,
)


class YOLODetector:
    """
    Encapsulates YOLO model loading and raw bounding box / class inference.
    """

    _instance: Optional["YOLODetector"] = None
    _model = None
    _model_path: Optional[Path] = None

    def __init__(self, model_path: Optional[str | Path] = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self._load_model()

    def _load_model(self):
        """Load YOLO model weights cleanly."""
        from ultralytics import YOLO

        target_path = self.model_path
        if not target_path.exists():
            if FALLBACK_MODEL_PATH.exists():
                target_path = FALLBACK_MODEL_PATH
            else:
                raise FileNotFoundError(
                    f"Model weights file not found at {self.model_path} or fallback {FALLBACK_MODEL_PATH}"
                )

        # Determine compute device
        device = "0" if torch.cuda.is_available() else "cpu"
        self.device = device
        self._model = YOLO(str(target_path))
        self.actual_model_path = target_path

    @classmethod
    def get_detector(cls, model_path: Optional[str | Path] = None) -> "YOLODetector":
        """Singleton accessor for efficient reuse."""
        req_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if cls._instance is None or cls._model_path != req_path:
            cls._instance = cls(req_path)
            cls._model_path = req_path
        return cls._instance

    def predict(
        self,
        image_input: Any,
        conf_threshold: float = DEFAULT_CONF_THRESHOLD,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        imgsz: int = DEFAULT_IMG_SIZE,
    ) -> Dict[str, Any]:
        """
        Run inference on an image matrix or path.

        Returns raw detections dictionary:
            - "boxes": list of [x1, y1, x2, y2]
            - "scores": list of confidence floats
            - "class_ids": list of integer class IDs
            - "class_names": list of raw class strings
            - "inference_time_ms": float
        """
        results = self._model.predict(
            source=image_input,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=imgsz,
            device=self.device,
            verbose=False,
        )

        detections = []
        raw_names = self._model.names or {}

        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes

            if boxes is not None and len(boxes) > 0:
                xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                clss = boxes.cls.cpu().numpy()

                for i in range(len(confs)):
                    c_id = int(clss[i])
                    c_name = raw_names.get(c_id, str(c_id))
                    box = [float(round(coord, 2)) for coord in xyxy[i]]
                    conf = float(round(confs[i], 4))

                    detections.append({
                        "box_xyxy": box,
                        "confidence": conf,
                        "class_id": c_id,
                        "raw_class_name": c_name,
                    })

        return {
            "model_path": str(self.actual_model_path),
            "model_version": MODEL_VERSION,
            "device": self.device,
            "detection_count": len(detections),
            "raw_detections": detections,
        }
