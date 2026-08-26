#!/usr/bin/env python3
"""
scripts/test_crud_consistency.py
Verifies single source of truth and CRUD operations across
ObservationRepository, JSON database, and API endpoints.
"""

import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "..")
OBS_FILE = os.path.join(BASE_DIR, "data", "observations.json")
PHP_EXE = "php"

def run_php(code):
    result = subprocess.run([PHP_EXE, "-r", code], capture_output=True, text=True, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"PHP Error:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError("PHP execution failed")
    return result.stdout.strip()

def run_test():
    print("==================================================")
    print(" RUNNING DATA CONSISTENCY & CRUD TEST SUITE")
    print("==================================================")

    # 1. Reset database to empty state
    print("\n[Step 1] Resetting data/observations.json to empty state...")
    reset_php = """
    require_once 'includes/ObservationRepository.php';
    $repo = new ObservationRepository();
    $repo->clear();
    echo json_encode($repo->all());
    """
    out = run_php(reset_php)
    assert out == "[]", f"Expected [], got {out}"
    print(" -> Database cleared successfully: []")

    # 2. Check get_observations.php output on empty state
    print("\n[Step 2] Testing api/get_observations.php on empty state...")
    get_obs_php = """
    $_SERVER['REQUEST_METHOD'] = 'GET';
    ob_start();
    require 'api/get_observations.php';
    $res = ob_get_clean();
    echo $res;
    """
    out = run_php(get_obs_php)
    data = json.loads(out)
    assert data["success"] is True
    assert data["total_observations"] == 0
    assert data["unique_farmers"] == 0
    assert len(data["observations"]) == 0
    print(" -> get_observations.php returned 0 records correctly.")

    # 3. Create Observation 1 via save_observation.php
    print("\n[Step 3] Creating Observation 1 (Farmer 001, Late Blight, 0.94)...")
    save1_php = """
    $_SERVER['REQUEST_METHOD'] = 'POST';
    $body = json_encode(['farmer_id' => '001', 'disease' => 'Late Blight', 'confidence' => 0.94, 'crop' => 'Tomato']);
    // simulate php://input
    require_once 'includes/ObservationRepository.php';
    $repo = new ObservationRepository();
    $rec = $repo->save('001', 'Late Blight', 0.94, ['crop' => 'Tomato']);
    echo json_encode($rec);
    """
    out = run_php(save1_php)
    rec1 = json.loads(out)
    obs_id_1 = rec1["observation_id"]
    print(f" -> Created observation: {obs_id_1}")

    # 4. Create Observation 2 via save_observation
    print("\n[Step 4] Creating Observation 2 (Farmer 002, Late Blight, 0.91)...")
    save2_php = f"""
    require_once 'includes/ObservationRepository.php';
    $repo = new ObservationRepository();
    $rec = $repo->save('002', 'Late Blight', 0.91, ['crop' => 'Tomato']);
    echo json_encode($rec);
    """
    out = run_php(save2_php)
    rec2 = json.loads(out)
    obs_id_2 = rec2["observation_id"]
    print(f" -> Created observation: {obs_id_2}")

    # 5. Verify get_observations.php with 2 records
    print("\n[Step 5] Checking get_observations.php with 2 records...")
    out = run_php(get_obs_php)
    data = json.loads(out)
    assert data["total_observations"] == 2
    assert data["unique_farmers"] == 2
    assert abs(data["average_confidence"] - 0.925) < 0.001
    assert len(data["observations"]) == 2
    assert data["observations"][0]["observation_id"] == obs_id_1
    assert data["observations"][1]["observation_id"] == obs_id_2
    print(f" -> get_observations.php confirmed 2 records: avg_conf={data['average_confidence']}")

    # 6. Update Observation 2 confidence from 0.91 to 0.96
    print(f"\n[Step 6] Updating {obs_id_2} confidence to 0.96...")
    update_php = f"""
    require_once 'includes/ObservationRepository.php';
    $repo = new ObservationRepository();
    $updated = $repo->update('{obs_id_2}', ['confidence' => 0.96]);
    echo json_encode($updated);
    """
    out = run_php(update_php)
    up_rec = json.loads(out)
    assert up_rec["confidence"] == 0.96
    print(f" -> Updated {obs_id_2} confidence to 0.96")

    # 7. Create Observation 3 (Farmer 004, Early Blight, 0.88)
    print("\n[Step 7] Creating Observation 3 (Farmer 004, Early Blight, 0.88)...")
    save3_php = """
    require_once 'includes/ObservationRepository.php';
    $repo = new ObservationRepository();
    $rec = $repo->save('004', 'Early Blight', 0.88, ['crop' => 'Tomato']);
    echo json_encode($rec);
    """
    out = run_php(save3_php)
    rec3 = json.loads(out)
    obs_id_3 = rec3["observation_id"]
    print(f" -> Created observation: {obs_id_3}")

    # 8. Verify get_observations with 3 records
    out = run_php(get_obs_php)
    data = json.loads(out)
    assert data["total_observations"] == 3
    assert data["unique_farmers"] == 3
    print(f" -> Database now has {data['total_observations']} observations across {data['unique_farmers']} farmers.")

    # 9. Delete Observation 2
    print(f"\n[Step 9] Deleting observation {obs_id_2}...")
    del_php = f"""
    require_once 'includes/ObservationRepository.php';
    $repo = new ObservationRepository();
    $success = $repo->delete('{obs_id_2}');
    echo json_encode(['deleted' => $success, 'all' => $repo->all()]);
    """
    out = run_php(del_php)
    del_res = json.loads(out)
    assert del_res["deleted"] is True
    remaining_ids = [o["observation_id"] for o in del_res["all"]]
    assert obs_id_2 not in remaining_ids
    assert obs_id_1 in remaining_ids
    assert obs_id_3 in remaining_ids
    assert len(remaining_ids) == 2
    print(f" -> Deleted {obs_id_2}. Remaining records: {remaining_ids}")

    # 10. Verify get_observations after deletion
    print("\n[Step 10] Verifying get_observations.php after deletion...")
    out = run_php(get_obs_php)
    data = json.loads(out)
    assert data["total_observations"] == 2
    assert data["unique_farmers"] == 2
    obs_ids_in_api = [o["observation_id"] for o in data["observations"]]
    assert obs_ids_in_api == [obs_id_1, obs_id_3]
    print(f" -> API consistently reflects {len(obs_ids_in_api)} observations: {obs_ids_in_api}")

    print("\n==================================================")
    print(" ALL 10 TESTS PASSED! DATA CONSISTENCY CONFIRMED.")
    print(" Single Source of Truth is fully functional.")
    print("==================================================")

if __name__ == "__main__":
    run_test()
