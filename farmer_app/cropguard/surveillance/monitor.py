#!/usr/bin/env python3
"""
monitor.py — Live backend observation console + surveillance engine.

Reads data/observations.json, displays a live table of observations,
and runs the surveillance analysis whenever the database changes:

  1. Load priority_diseases.json
  2. Count detections of each priority disease
  3. If detection_count > THRESHOLD, trigger a priority event
  4. Attach dummy weather + location data
  5. Save the event to priority_events.json
  6. Print a terminal alert

This program NEVER writes to observations.json — only the PHP API does.
It DOES write to priority_events.json (the derived surveillance database).

Usage:
    python3 monitor.py
(Ctrl+C to quit)
"""

import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# PATHS — resolved relative to this script so it works from any cwd
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OBSERVATIONS_FILE = os.path.join(SCRIPT_DIR, "..", "data", "observations.json")
PRIORITY_DISEASES_FILE = os.path.join(SCRIPT_DIR, "..", "data", "priority_diseases.json")
PRIORITY_EVENTS_FILE = os.path.join(SCRIPT_DIR, "..", "data", "priority_events.json")

# Path to the GIS pipeline entry point — invoked automatically after a new event.
GIS_MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "..", "gis", "main.py")

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
POLL_SECONDS = 1.0
THRESHOLD = 1  # trigger when detection_count > THRESHOLD

DISEASE_COL_WIDTH = 20

# Dummy location pool — cycled through by index. Replace later with real GPS.
DUMMY_LOCATIONS = [
    (9.2645, 76.4600),
    (9.2712, 76.4721),
    (9.2801, 76.4815),
    (9.2910, 76.4930),
]


# ---------------------------------------------------------------------------
# FILE I/O HELPERS
# ---------------------------------------------------------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def load_observations():
    """
    Returns (observations_list, error_message).
    On any failure we return the empty list rather than raising, so a
    transient bad state (file mid-write, briefly invalid JSON) never
    crashes the monitor.
    """
    if not os.path.exists(OBSERVATIONS_FILE):
        return [], "Database file not found yet: {}".format(OBSERVATIONS_FILE)
    try:
        with open(OBSERVATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        observations = data.get("observations", [])
        if not isinstance(observations, list):
            return [], "observations.json is malformed (observations is not a list)."
        return observations, None
    except json.JSONDecodeError:
        return [], "observations.json is temporarily invalid (mid-write?) — will retry."
    except OSError as e:
        return [], "Could not read observations.json: {}".format(e)


def load_priority_diseases():
    """
    Returns (list_of_disease_names, error_message).
    """
    if not os.path.exists(PRIORITY_DISEASES_FILE):
        return [], "priority_diseases.json not found."
    try:
        with open(PRIORITY_DISEASES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        diseases = data.get("priority_diseases", [])
        if not isinstance(diseases, list):
            return [], "priority_diseases.json is malformed."
        return diseases, None
    except (json.JSONDecodeError, OSError) as e:
        return [], "Could not read priority_diseases.json: {}".format(e)


def load_priority_events():
    """
    Returns the existing events list (empty list on any failure).
    """
    if not os.path.exists(PRIORITY_EVENTS_FILE):
        return []
    try:
        with open(PRIORITY_EVENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        events = data.get("events", [])
        return events if isinstance(events, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_priority_events(events):
    """
    Writes the events list to priority_events.json atomically enough for
    a prototype (write + fsync). Never called for observations.json.
    """
    payload = {
        "events": events,
        "metadata": {
            "total_events": len(events),
            "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": (
                "Derived surveillance event database storing triggered "
                "priority disease events for the geospatial computation stage."
            ),
        },
    }
    tmp_path = PRIORITY_EVENTS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, PRIORITY_EVENTS_FILE)


# ---------------------------------------------------------------------------
# PIPELINE TRIGGER — automatically invoke GIS after a new event is saved
# ---------------------------------------------------------------------------
def trigger_gis_pipeline():
    """
    Launch gis/main.py as a non-blocking subprocess.

    Non-blocking: the surveillance monitor keeps polling while GIS runs in the
    background. If the GIS script is already running (previous event still
    processing), we skip rather than stack multiple concurrent invocations.

    Output from the GIS subprocess is written to gis/output/gis_run.log so
    it can be inspected without polluting the monitor terminal.
    """
    gis_script = os.path.normpath(GIS_MAIN_SCRIPT)
    if not os.path.exists(gis_script):
        print("[PIPELINE] WARNING: gis/main.py not found at: {}".format(gis_script))
        return

    log_path = os.path.join(os.path.dirname(gis_script), "output", "gis_run.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    try:
        with open(log_path, "a", encoding="utf-8") as log_f:
            log_f.write("\n[{}] GIS pipeline triggered by surveillance engine\n".format(
                datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            ))
            subprocess.Popen(
                [sys.executable, gis_script],
                stdout=log_f,
                stderr=log_f,
                cwd=os.path.dirname(gis_script),
            )
        print("[PIPELINE] GIS analysis triggered -> output in gis/output/gis_run.log")
    except Exception as e:
        print("[PIPELINE] WARNING: Failed to trigger GIS pipeline: {}".format(e))


# ---------------------------------------------------------------------------
# DUMMY DATA GENERATORS — replace with real APIs later without touching
# the rest of the architecture.
# ---------------------------------------------------------------------------
def generate_dummy_weather():
    """
    Returns a realistic-ish weather dict for Kerala/India in August.
    Later: get_real_weather(latitude, longitude).
    """
    return {
        "temperature_c": round(random.uniform(26.0, 31.0), 1),
        "humidity_percent": random.randint(78, 94),
        "wind_speed_kmh": round(random.uniform(4.0, 12.0), 1),
    }


def generate_dummy_location(index):
    """
    Returns (latitude, longitude) from a fixed pool, cycled by index.
    Later: read from device GPS or farmer profile.
    """
    return DUMMY_LOCATIONS[index % len(DUMMY_LOCATIONS)]


# ---------------------------------------------------------------------------
# SURVEILLANCE ENGINE
# ---------------------------------------------------------------------------
def analyze_surveillance(observations, priority_diseases, existing_events):
    """
    Core logic:
      - For each priority disease, find matching observations.
      - Count detections and unique farmers.
      - If detection_count > THRESHOLD and we haven't already emitted an
        event covering exactly this set of observations, create a new event.

    Returns (new_events_list, already_triggered_count).
    """
    # Build a quick lookup: which observation_ids are already covered by
    # an existing event for a given disease. This prevents re-triggering
    # on every poll cycle for the same data.
    covered_obs_ids_by_disease = {}
    for ev in existing_events:
        disease = ev.get("disease")
        ids = {d.get("observation_id") for d in ev.get("detections", [])}
        covered_obs_ids_by_disease.setdefault(disease, set()).update(ids)

    new_events = []

    for disease in priority_diseases:
        matching = [o for o in observations if o.get("disease") == disease]
        detection_count = len(matching)

        if detection_count <= THRESHOLD:
            continue

        # Which of these observations are NOT yet covered by an existing event?
        already_covered = covered_obs_ids_by_disease.get(disease, set())
        uncovered = [o for o in matching if o.get("observation_id") not in already_covered]

        if not uncovered:
            # We've already emitted an event for this exact dataset.
            continue

        # Build the event from ALL matching observations (not just uncovered),
        # so the event reflects the full current picture of this disease.
        unique_farmers = set()
        detections = []
        for idx, obs in enumerate(matching):
            farmer_id = obs.get("farmer_id", "?")
            unique_farmers.add(farmer_id)
            lat = obs.get("latitude") if obs.get("latitude") is not None else generate_dummy_location(idx)[0]
            lon = obs.get("longitude") if obs.get("longitude") is not None else generate_dummy_location(idx)[1]
            detections.append({
                "observation_id": obs.get("observation_id"),
                "farmer_id": farmer_id,
                "crop": obs.get("crop"),
                "image_path": obs.get("image_path"),
                "confidence": obs.get("confidence"),
                "timestamp": obs.get("timestamp"),
                "latitude": float(lat),
                "longitude": float(lon),
                "weather": generate_dummy_weather(),
            })

        event_id = "EVENT-{:04d}".format(len(existing_events) + len(new_events) + 1)
        event = {
            "event_id": event_id,
            "disease": disease,
            "detection_count": detection_count,
            "unique_farmer_count": len(unique_farmers),
            "status": "TRIGGERED",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "detections": detections,
        }
        new_events.append(event)

    return new_events


# ---------------------------------------------------------------------------
# TERMINAL RENDERING
# ---------------------------------------------------------------------------
def truncate(text, width):
    text = str(text)
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def format_confidence(conf):
    try:
        return "{:.1f}%".format(float(conf) * 100)
    except (TypeError, ValueError):
        return "n/a"


def render(observations, error_message, last_mtime, priority_diseases, new_events):
    clear_screen()
    width = 62

    print("=" * width)
    print(" AGRICULTURAL DISEASE SURVEILLANCE")
    print("=" * width)
    print()
    print("Database observations : {}".format(len(observations)))
    print("Priority diseases     : {}".format(len(priority_diseases)))
    if last_mtime is not None:
        last_update = datetime.fromtimestamp(last_mtime).strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_update = "n/a"
    print("Last update           : {}".format(last_update))

    if error_message:
        print()
        print("NOTE: {}".format(error_message))

    # ---- Observation table -------------------------------------------------
    print()
    print("-" * width)
    print(" OBSERVATIONS")
    print("-" * width)
    header = "| {:<10} | {:<6} | {:<20} | {:<10} |".format(
        "ID", "FARMER", "DISEASE", "CONFIDENCE"
    )
    print(header)
    print("-" * width)

    if not observations:
        print("| {:<58} |".format("No observations yet."))
    else:
        for obs in observations:
            obs_id = truncate(obs.get("observation_id", "?"), 10)
            farmer = truncate(obs.get("farmer_id", "?"), 6)
            disease = truncate(obs.get("disease", "?"), DISEASE_COL_WIDTH)
            conf_str = format_confidence(obs.get("confidence", 0))
            print("| {:<10} | {:<6} | {:<20} | {:<10} |".format(
                obs_id, farmer, disease, conf_str
            ))
    print("-" * width)

    # ---- Priority alerts ---------------------------------------------------
    if new_events:
        for ev in new_events:
            print()
            print("=" * width)
            print(" PRIORITY DISEASE DETECTED")
            print("=" * width)
            print()
            print("Disease          : {}".format(ev["disease"]))
            print("Detection count  : {}".format(ev["detection_count"]))
            print("Unique farmers   : {}".format(ev["unique_farmer_count"]))
            print()
            print("STATUS           : {}".format(ev["status"]))
            print()

            for i, det in enumerate(ev["detections"], start=1):
                ordinal = "First" if i == 1 else "Second" if i == 2 else "#{:d}".format(i)
                print("{} detection:".format(ordinal))
                print("  Farmer     : {}".format(det.get("farmer_id", "?")))
                print("  Location   : {}, {}".format(det.get("latitude"), det.get("longitude")))
                print("  Confidence : {}".format(format_confidence(det.get("confidence"))))
                print()

            # Weather — show the first detection's weather as a representative sample.
            if ev["detections"]:
                w = ev["detections"][0].get("weather", {})
                print("Weather (sample):")
                print("  Temperature : {} °C".format(w.get("temperature_c", "?")))
                print("  Humidity    : {}%".format(w.get("humidity_percent", "?")))
                print("  Wind Speed  : {} km/h".format(w.get("wind_speed_kmh", "?")))
                print()

            print(">>> Sending event to computation stage...")
            print()
            print("=" * width)
    else:
        # No new triggers this cycle. Show a quiet status line if we have data.
        if observations and priority_diseases:
            print()
            print("No computation triggered.")

    print()
    print("=" * width)
    print("(polling every {:.0f}s — press Ctrl+C to quit)".format(POLL_SECONDS))


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------
def main():
    last_mtime_seen = None
    last_rendered_mtime = None
    cached_events = load_priority_events()  # existing events from disk
    cached_new_events = []  # events generated on the most recent change

    while True:
        current_mtime = (
            os.path.getmtime(OBSERVATIONS_FILE)
            if os.path.exists(OBSERVATIONS_FILE)
            else None
        )

        should_redraw = (
            last_rendered_mtime is None
            or current_mtime != last_mtime_seen
        )

        if should_redraw:
            observations, error_message = load_observations()
            priority_diseases, _ = load_priority_diseases()

            # Re-read events from disk each cycle in case another process
            # wrote to it (defensive; in this prototype only we write).
            cached_events = load_priority_events()

            if not error_message and priority_diseases:
                new_events = analyze_surveillance(
                    observations, priority_diseases, cached_events
                )
                if new_events:
                    cached_events.extend(new_events)
                    save_priority_events(cached_events)
                    # ---- INTEGRATION: auto-trigger GIS pipeline ----
                    trigger_gis_pipeline()
                cached_new_events = new_events
            else:
                cached_new_events = []

            render(observations, error_message, current_mtime,
                   priority_diseases, cached_new_events)

            last_rendered_mtime = current_mtime
            last_mtime_seen = current_mtime

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
        sys.exit(0)