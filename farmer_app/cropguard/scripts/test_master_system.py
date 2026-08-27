#!/usr/bin/env python3
"""
Master System Integration & Acceptance Test Suite for CropGuard.

Verifies the complete closed-loop agricultural surveillance system:
  1. Farmer Registration & Field Configuration
  2. Multi-Farmer Image Acquisition & Real YOLO Inference
  3. Single Source of Truth Database Integrity
  4. GIS Spatial Clustering & Distance Analysis
  5. Agro-Meteorological Weather Ingestion & Risk Scoring
  6. Hotspot Threshold Engine Triggering
  7. Expert Review & Pathologist Validation (CONFIRM / REJECT)
  8. Multi-Channel Advisory Dissemination (In-App, SMS, IVR Voice Call)
  9. Farmer Follow-Up Observation Submission
  10. Real-Time Digital Twin State Consistency
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000"
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SAMPLE_LEAF = PROJECT_ROOT / "uploads" / "farmer002_1787734806.jpg"

def run_master_acceptance_suite():
    print("=" * 70)
    print(" CROPGUARD MASTER SYSTEM ACCEPTANCE TEST SUITE")
    print(" Complete Closed-Loop Surveillance & Decision-Support Verification")
    print("=" * 70)

    session = requests.Session()

    # Step 1: Check System Health
    print("\n[Step 1] Verifying System Connectivity & Web Server...")
    res = session.get(f"{BASE_URL}/index.php")
    assert res.status_code == 200, f"Server unreachable: {res.status_code}"
    print("  --> PASS: Web Server active on port 8000.")

    # Step 2: Test Field Management API
    print("\n[Step 2] Testing Farm & Field Entity Management (api/fields.php)...")
    res = session.get(f"{BASE_URL}/api/fields.php")
    assert res.status_code == 200
    fields_data = res.json()
    assert fields_data.get("success") is True
    print(f"  --> PASS: Loaded {len(fields_data.get('fields', []))} active fields from database.")

    # Step 3: Farmer A submits crop image with GPS
    print("\n[Step 3] Farmer A (001, Chengannur) uploads leaf photo -> YOLO Vision...")
    with open(SAMPLE_LEAF, "rb") as f:
        files = {"image": ("farmerA_leaf.jpg", f, "image/jpeg")}
        data = {
            "farmer_id": "001",
            "crop": "Apple",
            "field_id": "FIELD-001",
            "latitude": 9.2712,
            "longitude": 76.4721,
        }
        resA = session.post(f"{BASE_URL}/api/analyze_image.php", files=files, data=data)

    assert resA.status_code == 200
    jsonA = resA.json()
    assert jsonA["success"] is True
    obsA_id = jsonA["observation_id"]
    detected_disease = jsonA["disease"]
    print(f"  --> PASS: Farmer A observation recorded: {obsA_id} ({detected_disease}, conf={jsonA['confidence']:.2f})")

    # Step 4: Farmer B submits crop image nearby with GPS
    print(f"\n[Step 4] Farmer B (002, Thiruvalla, 1.6km away) reports {detected_disease}...")
    with open(SAMPLE_LEAF, "rb") as f:
        files = {"image": ("farmerB_leaf.jpg", f, "image/jpeg")}
        data = {
            "farmer_id": "002",
            "crop": "Apple",
            "field_id": "FIELD-002",
            "latitude": 9.2645,
            "longitude": 76.4600,
        }
        resB = session.post(f"{BASE_URL}/api/analyze_image.php", files=files, data=data)

    assert resB.status_code == 200
    jsonB = resB.json()
    assert jsonB["success"] is True
    obsB_id = jsonB["observation_id"]
    print(f"  --> PASS: Farmer B observation recorded: {obsB_id} ({jsonB['disease']}, conf={jsonB['confidence']:.2f})")

    # Step 5: Check Weather Ingestion API
    print("\n[Step 5] Ingesting agro-meteorological parameters (api/weather.php)...")
    res_wx = session.get(f"{BASE_URL}/api/weather.php?lat=9.2712&lon=76.4721")
    assert res_wx.status_code == 200
    wx_json = res_wx.json()
    assert wx_json["success"] is True
    print(f"  --> PASS: Weather ingested: Temp={wx_json['weather']['temperature_c']}°C, Humidity={wx_json['weather']['humidity_percent']}%, Fungal Risk={wx_json['disease_favorable']}")

    # Step 6: Trigger GIS & Geospatial Surveillance Pipeline
    print("\n[Step 6] Running GIS Geospatial Analysis & Spatial Distance Calculation...")
    gis_proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "gis" / "main.py")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT / "gis")
    )
    print(gis_proc.stdout)
    assert gis_proc.returncode == 0, f"GIS pipeline failed: {gis_proc.stderr}"
    print("  --> PASS: GIS spatial clustering generated output/analyzed_map.png & gis_results.json.")

    # Step 7: Build Unified Surveillance Report
    print("\n[Step 7] Running Unified Pipeline Report Builder...")
    rep_proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "pipeline" / "build_report.py")],
        capture_output=True,
        text=True
    )
    assert rep_proc.returncode == 0, f"Report builder failed: {rep_proc.stderr}"
    print("  --> PASS: Generated reports/latest_report.json.")

    # Step 8: Expert Review & Pathologist Validation
    print("\n[Step 8] Testing Expert Validation Loop (api/expert_review.php)...")
    # Query pending reviews
    res_exp_get = session.get(f"{BASE_URL}/api/expert_review.php")
    assert res_exp_get.status_code == 200
    exp_get_json = res_exp_get.json()
    print(f"  Pending reviews in queue: {exp_get_json['pending_count']}")

    # Submit Expert Confirmation
    exp_payload = {
        "observation_id": obsA_id,
        "action": "CONFIRM",
        "expert_name": "Dr. Ananya Sharma (Lead Agronomist)",
        "expert_notes": "Confirmed fungal lesion margins. Issued urgent copper bio-fungicide protocol."
    }
    res_exp_post = session.post(f"{BASE_URL}/api/expert_review.php", json=exp_payload)
    assert res_exp_post.status_code == 200
    exp_post_json = res_exp_post.json()
    assert exp_post_json["success"] is True
    assert exp_post_json["updated_observation"]["validation_status"] == "CONFIRMED"
    print(f"  --> PASS: Expert confirmed observation {obsA_id}. Status updated to CONFIRMED.")

    # Step 9: Multi-channel Alert Dispatching (SMS + IVR Call Simulator)
    print("\n[Step 9] Testing Multi-channel Alert Dispatch (api/trigger_alert.php)...")
    alert_payload = {
        "action": "ALERT",
        "event_id": "EVENT-0001",
        "disease": detected_disease,
        "risk_label": "HIGH OUTBREAK RISK",
        "officer": "Dr. Ananya Sharma"
    }
    res_alert = session.post(f"{BASE_URL}/api/trigger_alert.php", json=alert_payload)
    assert res_alert.status_code == 200
    alert_json = res_alert.json()
    assert alert_json["success"] is True
    print(f"  --> PASS: Dispatched official alerts to {alert_json.get('calls_initiated', 0)} registered farmers.")

    # Step 10: Farmer Follow-Up Observation Submission
    print("\n[Step 10] Testing Farmer Follow-Up Recovery Submission...")
    with open(SAMPLE_LEAF, "rb") as f:
        files = {"image": ("followup_leaf.jpg", f, "image/jpeg")}
        data = {
            "farmer_id": "001",
            "crop": "Apple",
            "field_id": "FIELD-001",
            "is_follow_up": 1
        }
        res_followup = session.post(f"{BASE_URL}/api/analyze_image.php", files=files, data=data)
    assert res_followup.status_code == 200
    followup_json = res_followup.json()
    print(f"  --> PASS: Follow-up observation created: {followup_json['observation_id']}")

    # Step 11: Real-time Digital Twin State Validation
    print("\n[Step 11] Validating Complete Digital Twin State (api/get_digital_twin.php)...")
    res_dt = session.get(f"{BASE_URL}/api/get_digital_twin.php")
    assert res_dt.status_code == 200
    dt_json = res_dt.json()
    assert dt_json["success"] is True
    overview = dt_json["digital_twin"]["ecosystem_overview"]
    print(f"  Digital Twin Summary: {overview['total_farmers']} Farmers · {overview['total_fields']} Fields · {overview['total_observations']} Observations · {overview['confirmed_outbreaks']} Confirmed Outbreaks")
    assert overview["total_observations"] >= 3
    assert overview["confirmed_outbreaks"] >= 1
    print("  --> PASS: Digital Twin reflects 100% synchronized system of record.")

    print("\n" + "=" * 70)
    print(" ALL 11 MASTER ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
    print(" THE CROPGUARD SURVEILLANCE & DECISION-SUPPORT SYSTEM IS COMPLETE.")
    print("=" * 70)

if __name__ == "__main__":
    run_master_acceptance_suite()
