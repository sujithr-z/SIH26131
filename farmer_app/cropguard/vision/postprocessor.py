"""
Post-processor for YOLO detections: bounding-box filtering, disease classification,
severity estimation, and structured result formatting.
"""

from typing import Dict, Any, List, Optional
from vision.config import (
    PLANTVILLAGE_CLASSES,
    CLASS_NAME_ALIASES,
    MODEL_VERSION,
)
from vision.knowledge_base import get_disease_advisory


class PostProcessor:
    """
    Transforms raw YOLO bounding boxes into structured agricultural observations.
    """

    @classmethod
    def process(
        cls,
        raw_results: Dict[str, Any],
        image_metrics: Dict[str, Any],
        crop_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process detection outputs into a clean agricultural diagnosis.
        """
        raw_detections = raw_results.get("raw_detections", [])
        img_w = image_metrics.get("width", 640)
        img_h = image_metrics.get("height", 640)
        total_img_area = float(max(img_w * img_h, 1))

        if not raw_detections:
            # No disease bounding box detected by YOLO
            fallback_crop = crop_hint if (crop_hint and crop_hint.strip()) else "Crop Foliage"
            advisory = get_disease_advisory("Healthy", is_healthy=True)

            return {
                "crop": fallback_crop,
                "disease": "Healthy / No Disease Detected",
                "is_healthy": True,
                "confidence": 0.95,
                "severity": "Low",
                "affected_area_percentage": 0.0,
                "detections": [],
                "description": advisory["description"],
                "precautions": advisory["precautions"],
                "model_version": MODEL_VERSION,
                "image_quality": image_metrics,
            }

        # Process each bounding box
        processed_boxes = []
        total_box_area = 0.0

        for det in raw_detections:
            box = det["box_xyxy"]
            conf = det["confidence"]
            class_id = det["class_id"]
            raw_name = det.get("raw_class_name", "")

            # Resolve crop & disease label
            crop_name, disease_name, is_healthy = cls._resolve_class(class_id, raw_name, crop_hint)

            # Bounding box metrics
            bw = max(0.0, box[2] - box[0])
            bh = max(0.0, box[3] - box[1])
            box_area = bw * bh
            total_box_area += box_area

            # Normalized coordinates (0.0 to 1.0)
            norm_box = [
                round(box[0] / img_w, 4),
                round(box[1] / img_h, 4),
                round(box[2] / img_w, 4),
                round(box[3] / img_h, 4),
            ]

            processed_boxes.append({
                "crop": crop_name,
                "disease": disease_name,
                "confidence": conf,
                "is_healthy": is_healthy,
                "box_xyxy": box,
                "box_normalized": norm_box,
                "area_fraction": round(box_area / total_img_area, 4),
            })

        # Select primary diagnosis: pick highest confidence non-healthy detection, or highest confidence overall
        non_healthy_boxes = [b for b in processed_boxes if not b["is_healthy"]]
        target_boxes = non_healthy_boxes if non_healthy_boxes else processed_boxes
        primary = max(target_boxes, key=lambda x: x["confidence"])

        # Calculate affected area percentage
        affected_area_pct = min(100.0, round((total_box_area / total_img_area) * 100.0, 2))

        # Severity estimate: combined affected area and pathogen characteristics
        severity = cls._calculate_severity(primary["disease"], affected_area_pct, primary["is_healthy"])

        # Retrieve agronomic advisory
        advisory = get_disease_advisory(primary["disease"], is_healthy=primary["is_healthy"])

        return {
            "crop": primary["crop"],
            "disease": primary["disease"],
            "is_healthy": primary["is_healthy"],
            "confidence": primary["confidence"],
            "severity": severity,
            "affected_area_percentage": affected_area_pct,
            "detections": processed_boxes,
            "description": advisory["description"],
            "precautions": advisory["precautions"],
            "model_version": MODEL_VERSION,
            "image_quality": image_metrics,
        }

    @classmethod
    def _resolve_class(
        cls, class_id: int, raw_name: str, crop_hint: Optional[str]
    ) -> tuple[str, str, bool]:
        """Map class id or string to (Crop, Disease, is_healthy)."""
        raw_lower = str(raw_name).lower().strip()

        # Check alias dictionary
        if raw_lower in CLASS_NAME_ALIASES:
            item = CLASS_NAME_ALIASES[raw_lower]
            return item["crop"], item["disease"], item["is_healthy"]

        # Check integer class table
        if class_id in PLANTVILLAGE_CLASSES:
            item = PLANTVILLAGE_CLASSES[class_id]
            return item["crop"], item["disease"], item["is_healthy"]

        # Parse string like "Tomato___Early_Blight" or "Corn_(maize)___Common_rust_"
        if "___" in raw_name:
            parts = raw_name.split("___", 1)
            crop_part = parts[0].replace("_", " ").replace("(maize)", "").strip().title()
            disease_part = parts[1].replace("_", " ").strip().title()
            is_healthy = "healthy" in disease_part.lower()
            return crop_part, disease_part, is_healthy

        # Fallback
        clean_name = raw_name.replace("_", " ").title()
        is_healthy = "healthy" in clean_name.lower()
        fallback_crop = crop_hint if (crop_hint and crop_hint.strip()) else "Crop"
        return fallback_crop, clean_name, is_healthy

    @staticmethod
    def _calculate_severity(disease_name: str, affected_area_pct: float, is_healthy: bool) -> str:
        """Derive agricultural severity level."""
        if is_healthy:
            return "Low"

        high_risk_diseases = ["late blight", "black rot", "northern leaf blight", "apple scab"]
        d_lower = disease_name.lower()

        if any(hr in d_lower for hr in high_risk_diseases) or affected_area_pct > 25.0:
            return "High"
        elif affected_area_pct > 8.0:
            return "Medium"
        else:
            return "Low"
