#!/usr/bin/env python3
"""
End-to-End System Test for Farmer App + YOLO Vision Subsystem.
"""

import sys
import json
import subprocess
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000"
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SAMPLE_IMAGE = PROJECT_ROOT / "uploads" / "farmer002_1787734806.jpg"

def run_tests():
    print("=" * 65)
    print(" CROPGUARD END-TO-END INTEGRATION TEST")
    print("=" * 65)

    session = requests.Session()

    # 1. Test Home Page
    print("\n[Test 1] Checking Home Page (index.php)...")
    res = session.get(f"{BASE_URL}/index.php")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "CropGuard" in res.text
    print("  --> PASS: Home page reachable.")

    # 2. Test Direct REST API /api/analyze_image.php
    print("\n[Test 2] Testing POST /api/analyze_image.php with multipart image...")
    assert SAMPLE_IMAGE.exists(), f"Sample image missing: {SAMPLE_IMAGE}"
    with open(SAMPLE_IMAGE, "rb") as f:
        files = {"image": ("leaf.jpg", f, "image/jpeg")}
        data = {
            "farmer_id": "001",
            "crop": "Apple",
            "latitude": 9.2712,
            "longitude": 76.4721
        }
        res = session.post(f"{BASE_URL}/api/analyze_image.php", files=files, data=data)

    print(f"  HTTP Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    resp_json = res.json()
    print("  API Response:", json.dumps(resp_json, indent=2))
    assert resp_json.get("success") is True
    assert "observation_id" in resp_json
    assert resp_json.get("model_version") == "yolo-agri-v1"
    assert "detections" in resp_json
    obs_id = resp_json["observation_id"]
    print(f"  --> PASS: REST API analyzed image and produced Observation ID: {obs_id}")

    # 3. Verify Observation via /api/get_observations.php
    print("\n[Test 3] Verifying observation persistence in get_observations.php...")
    res = session.get(f"{BASE_URL}/api/get_observations.php")
    assert res.status_code == 200
    all_obs = res.json()
    found = any(o.get("observation_id") == obs_id for o in all_obs.get("observations", []))
    assert found, f"Observation {obs_id} not found in get_observations.php"
    print(f"  --> PASS: Observation {obs_id} persisted in database.")

    # 4. Test In-App Flow (Login -> Diagnose -> Analyze -> Report)
    print("\n[Test 4] Testing in-app Farmer flow (login -> analyze.php -> report.php)...")
    login_res = session.post(
        f"{BASE_URL}/login.php",
        data={"full_name": "John Farmer", "phone": "9876543210"},
        allow_redirects=True
    )
    assert login_res.status_code == 200

    with open(SAMPLE_IMAGE, "rb") as f:
        analyze_res = session.post(
            f"{BASE_URL}/analyze.php",
            files={"crop_image": ("farmer_leaf.jpg", f, "image/jpeg")},
            allow_redirects=True
        )
    assert analyze_res.status_code == 200
    assert "Diagnosis Report" in analyze_res.text
    assert "YOLO-AGRI-V1" in analyze_res.text or "yolo-agri-v1" in analyze_res.text
    print("  --> PASS: Farmer UI flow completed with YOLOv8 live diagnosis.")

    # 5. Test CRUD Consistency
    print("\n[Test 5] Running test_crud_consistency.py...")
    crud_proc = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "test_crud_consistency.py")], capture_output=True, text=True)
    print(crud_proc.stdout)
    assert crud_proc.returncode == 0, f"CRUD consistency test failed: {crud_proc.stderr}"
    print("  --> PASS: CRUD consistency intact.")

    # 6. Test Surveillance / Report Builder
    print("\n[Test 6] Running pipeline/build_report.py...")
    rep_proc = subprocess.run([sys.executable, str(PROJECT_ROOT / "pipeline" / "build_report.py")], capture_output=True, text=True)
    print(rep_proc.stdout)
    assert rep_proc.returncode == 0, f"Report builder failed: {rep_proc.stderr}"
    print("  --> PASS: Downstream report builder executed cleanly.")

    print("\n" + "=" * 65)
    print(" ALL END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
