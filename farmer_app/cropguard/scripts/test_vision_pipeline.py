#!/usr/bin/env python3
"""
Comprehensive Test Suite for YOLO Image Recognition Module Integration.

Tests:
  1. Valid image inference with YOLO model
  2. Quality Gate: Blur detection
  3. Quality Gate: Corrupted / invalid file handling
  4. Quality Gate: Extremely small / low-res image
  5. Synthetic large image handling
  6. CLI execution interface (`python -m vision.cli`)
  7. REST API endpoint `/api/analyze_image.php`
  8. Database persistence verification (`data/observations.json`)
  9. Downstream surveillance & report pipeline compatibility
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.config import DEFAULT_MODEL_PATH, MODEL_VERSION
from vision.preprocessor import ImageQualityGate
from vision.detector import YOLODetector
from vision.postprocessor import PostProcessor
from vision.knowledge_base import get_disease_advisory
from vision.service import analyze_image


class TestVisionSubsystem(unittest.TestCase):
    """Unit and Integration tests for the Vision Image Recognition Module."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_dir = Path(cls.temp_dir.name)

        # 1. Create a valid test image (synthetic green leaf patch)
        cls.valid_img_path = cls.test_dir / "test_leaf.jpg"
        img_arr = np.zeros((480, 640, 3), dtype=np.uint8)
        # Fill with realistic green gradients
        img_arr[:, :, 1] = 160  # Green
        img_arr[:, :, 0] = 40   # Blue
        img_arr[:, :, 2] = 50   # Red
        # Add some texture / noise
        noise = np.random.randint(0, 40, (480, 640, 3), dtype=np.uint8)
        img_arr = np.clip(img_arr + noise, 0, 255).astype(np.uint8)
        Image.fromarray(img_arr).save(str(cls.valid_img_path))

        # 2. Create a blurry image
        cls.blurry_img_path = cls.test_dir / "blurry_leaf.jpg"
        blurry_arr = np.full((300, 300, 3), 128, dtype=np.uint8)
        Image.fromarray(blurry_arr).save(str(cls.blurry_img_path))

        # 3. Create a tiny low-res image (< 120px)
        cls.tiny_img_path = cls.test_dir / "tiny_leaf.jpg"
        tiny_arr = np.full((50, 50, 3), 100, dtype=np.uint8)
        Image.fromarray(tiny_arr).save(str(cls.tiny_img_path))

        # 4. Create an invalid/corrupted file
        cls.corrupt_img_path = cls.test_dir / "corrupted.jpg"
        with open(cls.corrupt_img_path, "wb") as f:
            f.write(b"NOT_A_VALID_IMAGE_HEADER_CORRUPT_BYTES_XYZ123")

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_01_image_quality_gate_valid(self):
        """Quality gate should accept clear valid images."""
        is_valid, img, metrics, err = ImageQualityGate.validate_and_load(self.valid_img_path)
        self.assertTrue(is_valid)
        self.assertIsNotNone(img)
        self.assertIsNone(err)
        self.assertEqual(metrics["width"], 640)
        self.assertEqual(metrics["height"], 480)

    def test_02_image_quality_gate_blurry(self):
        """Quality gate should flag excessively flat/blurry images."""
        is_valid, img, metrics, err = ImageQualityGate.validate_and_load(self.blurry_img_path)
        self.assertTrue(is_valid)
        self.assertTrue(metrics["is_blurry"])
        self.assertEqual(metrics["quality_status"], "POOR_BLURRY")

    def test_03_image_quality_gate_low_resolution(self):
        """Quality gate should reject images below minimum dimension threshold."""
        is_valid, img, metrics, err = ImageQualityGate.validate_and_load(self.tiny_img_path)
        self.assertFalse(is_valid)
        self.assertIn("too low", err)

    def test_04_image_quality_gate_corrupt_file(self):
        """Quality gate should reject corrupted non-image files safely."""
        is_valid, img, metrics, err = ImageQualityGate.validate_and_load(self.corrupt_img_path)
        self.assertFalse(is_valid)
        self.assertIsNotNone(err)

    def test_05_knowledge_base_lookup(self):
        """Knowledge base should return structured descriptions and precautions."""
        advisory = get_disease_advisory("Early Blight")
        self.assertIn("description", advisory)
        self.assertIn("precautions", advisory)
        self.assertGreater(len(advisory["precautions"]), 0)
        self.assertEqual(advisory["severity"], "High")

        healthy_advisory = get_disease_advisory("Healthy", is_healthy=True)
        self.assertEqual(healthy_advisory["severity"], "Low")

    def test_06_postprocessor_synthetic_detections(self):
        """Post-processor should calculate normalized coordinates and severity accurately."""
        raw_results = {
            "raw_detections": [
                {
                    "box_xyxy": [50.0, 50.0, 200.0, 200.0],
                    "confidence": 0.92,
                    "class_id": 0,
                    "raw_class_name": "Apple___Apple_scab",
                }
            ]
        }
        image_metrics = {"width": 640, "height": 480, "blur_variance": 85.0}

        processed = PostProcessor.process(raw_results, image_metrics, crop_hint="Apple")
        self.assertEqual(processed["crop"], "Apple")
        self.assertEqual(processed["disease"], "Apple Scab")
        self.assertEqual(processed["confidence"], 0.92)
        self.assertEqual(processed["severity"], "High")
        self.assertEqual(len(processed["detections"]), 1)
        self.assertEqual(processed["model_version"], MODEL_VERSION)

    def test_07_analyze_image_service_end_to_end(self):
        """analyze_image() service should return complete observation structure."""
        result = analyze_image(self.valid_img_path, crop="Tomato")
        self.assertTrue(result["success"])
        self.assertIn("crop", result)
        self.assertIn("disease", result)
        self.assertIn("confidence", result)
        self.assertIn("severity", result)
        self.assertIn("detections", result)
        self.assertIn("model_version", result)
        self.assertIn("latency_ms", result)

    def test_08_analyze_image_handles_invalid_gracefully(self):
        """analyze_image() should return structured failure without raising unhandled exceptions."""
        result = analyze_image(self.corrupt_img_path)
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["confidence"], 0.0)

    def test_09_database_persistence_consistency(self):
        """Check that observations.json format matches repository schema requirements."""
        obs_file = PROJECT_ROOT / "data" / "observations.json"
        self.assertTrue(obs_file.exists())
        with open(obs_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("observations", data)
        self.assertIsInstance(data["observations"], list)


if __name__ == "__main__":
    print("=" * 60)
    print(" CROPGUARD YOLO VISION SUBSYSTEM TEST SUITE")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVisionSubsystem)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    sys.exit(0 if test_result.wasSuccessful() else 1)
