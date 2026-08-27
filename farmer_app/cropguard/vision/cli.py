"""
Command-Line Interface for the Image Recognition Module.
Enables execution from PHP backends, CLI tools, and automated pipelines.
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure app root is in python path
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from vision.service import analyze_image


def main():
    parser = argparse.ArgumentParser(description="CropGuard YOLO Image Recognition CLI")
    parser.add_argument("--image", type=str, required=True, help="Path to input crop leaf image")
    parser.add_argument("--crop", type=str, default=None, help="Optional crop name hint")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--weights", type=str, default=None, help="Optional model weights path")

    args = parser.parse_args()

    try:
        result = analyze_image(
            image_path=args.image,
            crop=args.crop,
            conf_threshold=args.conf,
            model_path=args.weights,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("success", False) else 0)
    except Exception as e:
        error_output = {
            "success": False,
            "error": str(e),
            "crop": args.crop or "Unknown",
            "disease": "Error",
            "confidence": 0.0,
            "severity": "Low",
            "detections": [],
            "description": f"CLI execution error: {str(e)}",
            "precautions": [],
            "model_version": "yolo-agri-v1",
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
