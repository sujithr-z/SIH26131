#!/usr/bin/env python3
"""
main.py — Entry point for the GIS analysis pipeline.

Orchestrates the geospatial analysis of priority disease events:
  1. Load configuration (map extent, visualization params, risk weights)
  2. Load priority events from the surveillance database
  3. Select the most recent triggered event
  4. Call gis_engine to perform spatial analysis
  5. Generate analyzed map image
  6. Save GIS results to JSON
  7. Print summary to terminal

Usage:
    python3 main.py

This script reads from:
  - config.json (GIS configuration)
  - data/priority_events.json (triggered events from surveillance engine)

This script writes to:
  - output/analyzed_map.png (georeferenced map with disease points)
  - output/gis_results.json (spatial analysis results)
"""

import json
import os
import subprocess
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# PATHS — resolved relative to this script
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config", "map_config.json")
EVENTS_FILE = os.path.join(SCRIPT_DIR, "..", "data", "priority_events.json")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

# Path to the report builder — invoked after GIS analysis completes.
REPORT_BUILDER_SCRIPT = os.path.join(SCRIPT_DIR, "..", "pipeline", "build_report.py")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(SCRIPT_DIR, "src"))

# Import the GIS engine modules
try:
    import gis_engine
except ImportError as e:
    print(f"ERROR: Could not import gis_engine: {e}")
    print("Make sure gis_engine.py is in the src/ subdirectory")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CONFIGURATION LOADING
# ---------------------------------------------------------------------------
def load_config():
    """
    Load GIS configuration from config.json.
    
    Returns:
        (config_dict, error_message)
        - config_dict: Configuration parameters
        - error_message: None on success, error string on failure
    """
    if not os.path.exists(CONFIG_FILE):
        return None, f"Configuration file not found: {CONFIG_FILE}"
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ["map_extent", "analysis", "output"]
        for field in required_fields:
            if field not in config:
                return None, f"config.json missing required field: {field}"
        
        return config, None
    
    except json.JSONDecodeError as e:
        return None, f"config.json contains invalid JSON: {e}"
    except OSError as e:
        return None, f"Could not read config.json: {e}"


# ---------------------------------------------------------------------------
# EVENT LOADING
# ---------------------------------------------------------------------------
def load_priority_events():
    """
    Load priority events from the surveillance database.
    
    Returns:
        (events_list, error_message)
        - events_list: List of event dicts
        - error_message: None on success, error string on failure
    """
    if not os.path.exists(EVENTS_FILE):
        return [], "No priority events found yet. Run the surveillance engine first."
    
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        events = data.get("events", [])
        
        if not isinstance(events, list):
            return [], "priority_events.json is malformed (events is not a list)."
        
        return events, None
    
    except json.JSONDecodeError as e:
        return [], f"priority_events.json contains invalid JSON: {e}"
    except OSError as e:
        return [], f"Could not read priority_events.json: {e}"


def select_latest_event(events):
    """
    Select the most recent triggered event for analysis.
    
    Args:
        events: List of event dicts
    
    Returns:
        Most recent event dict, or None if no events
    """
    if not events:
        return None
    
    # Filter to only TRIGGERED events
    triggered = [e for e in events if e.get("status") == "TRIGGERED"]
    
    if not triggered:
        return None
    
    # Sort by generated_at timestamp (most recent first)
    def get_timestamp(event):
        ts = event.get("generated_at", "")
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.min
    
    triggered.sort(key=get_timestamp, reverse=True)
    
    return triggered[0]


# ---------------------------------------------------------------------------
# OUTPUT DIRECTORY
# ---------------------------------------------------------------------------
def ensure_output_directory():
    """
    Create the output directory if it doesn't exist.
    
    Returns:
        True if directory exists or was created, False on error
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        return True
    except OSError as e:
        print(f"ERROR: Could not create output directory: {e}")
        return False


# ---------------------------------------------------------------------------
# TERMINAL OUTPUT
# ---------------------------------------------------------------------------
def print_header():
    """Print the GIS analysis header."""
    width = 70
    print("=" * width)
    print(" AGRICULTURAL DISEASE SURVEILLANCE — GIS ANALYSIS")
    print("=" * width)
    print()


def print_event_summary(event):
    """Print summary of the event being analyzed."""
    print("EVENT BEING ANALYZED:")
    print(f"  Event ID         : {event.get('event_id', '?')}")
    print(f"  Disease          : {event.get('disease', '?')}")
    print(f"  Detection count  : {event.get('detection_count', 0)}")
    print(f"  Unique farmers   : {event.get('unique_farmer_count', 0)}")
    print(f"  Status           : {event.get('status', '?')}")
    print(f"  Generated at     : {event.get('generated_at', '?')}")
    print()


def print_analysis_results(results):
    """Print the GIS analysis results."""
    print("-" * 70)
    print("GIS ANALYSIS RESULTS:")
    print("-" * 70)
    print()
    
    analysis = results.get("analysis", {})
    spatial = results.get("spatial_analysis", {})
    
    print("Detection Summary:")
    print(f"  Total detections    : {analysis.get('total_detections', 0)}")
    print(f"  Average confidence  : {analysis.get('average_confidence', 0):.1%}")
    print(f"  Average humidity    : {analysis.get('average_humidity', 0):.1f}%")
    print()
    
    print("Spatial Analysis:")
    print(f"  Distance between    : {spatial.get('distance_km', 0):.2f} km")
    print(f"  Distance score      : {spatial.get('distance_score', 0):.3f}")
    print(f"  Humidity score      : {spatial.get('humidity_score', 0):.3f}")
    print(f"  Prototype risk      : {spatial.get('prototype_risk_score', 0):.3f}")
    print()
    
    print("Risk Classification:")
    print(f"  Status              : {results.get('status', '?')}")
    print()


def print_output_files(map_path, results_path):
    """Print the paths to generated output files."""
    print("-" * 70)
    print("OUTPUT FILES:")
    print("-" * 70)
    print(f"  Analyzed map        : {map_path}")
    print(f"  GIS results         : {results_path}")
    print()


def print_footer():
    """Print the footer."""
    print("=" * 70)
    print("GIS analysis complete.")
    print("=" * 70)


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
def main():
    """
    Main GIS analysis pipeline.
    
    Flow:
      1. Load configuration
      2. Load priority events
      3. Select latest triggered event
      4. Run GIS engine
      5. Save outputs
      6. Print summary
    """
    print_header()
    
    # Step 1: Load configuration
    print("Loading configuration...")
    config, config_error = load_config()
    if config_error:
        print(f"ERROR: {config_error}")
        sys.exit(1)
    print("  [OK] Configuration loaded")
    print()
    
    # Step 2: Load priority events
    print("Loading priority events...")
    events, events_error = load_priority_events()
    if events_error:
        print(f"ERROR: {events_error}")
        sys.exit(1)
    
    if not events:
        print("  No priority events found.")
        print("  Run the surveillance engine (monitor.py) first to generate events.")
        sys.exit(0)
    
    print(f"  [OK] Found {len(events)} event(s)")
    print()
    
    # Step 3: Select latest event
    print("Selecting latest triggered event...")
    event = select_latest_event(events)
    if not event:
        print("  No triggered events found.")
        print("  All events are in MONITORING status.")
        sys.exit(0)
    
    print_event_summary(event)
    
    # Step 4: Ensure output directory exists
    if not ensure_output_directory():
        sys.exit(1)
    
    # Step 5: Run GIS engine
    print("Running GIS engine...")
    try:
        results, map_path, results_path = gis_engine.analyze_event(event, config)
        print("  [OK] GIS analysis complete")
        print()
    except Exception as e:
        print(f"ERROR: GIS engine failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 6: Print results
    print_analysis_results(results)
    print_output_files(map_path, results_path)
    print_footer()

    # Step 7: Trigger report builder to produce reports/latest_report.json
    report_script = os.path.normpath(REPORT_BUILDER_SCRIPT)
    if os.path.exists(report_script):
        print("Running report builder...")
        try:
            ret = subprocess.run(
                [sys.executable, report_script],
                cwd=os.path.dirname(report_script),
                capture_output=True,
                text=True,
            )
            if ret.returncode == 0:
                print("  Report builder complete -> reports/latest_report.json")
            else:
                print(f"  WARNING: Report builder exited with code {ret.returncode}")
                if ret.stderr:
                    print(f"  {ret.stderr.strip()}")
        except Exception as e:
            print(f"  WARNING: Could not run report builder: {e}")
    else:
        print("  NOTE: Report builder not found yet at: {}".format(report_script))


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGIS analysis interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)