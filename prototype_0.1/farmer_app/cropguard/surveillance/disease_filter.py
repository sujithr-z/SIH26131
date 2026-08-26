#!/usr/bin/env python3
"""
disease_filter.py — Priority disease detection and threshold analysis.

This module provides functions to:
  1. Load the priority disease list from config
  2. Filter observations to find priority disease detections
  3. Count detections and unique farmers per disease
  4. Determine which diseases exceed the trigger threshold
  5. Return structured analysis results for event generation

Used by monitor.py to drive the surveillance engine logic.
"""

import json
import os
from typing import Dict, List, Tuple, Set


# ---------------------------------------------------------------------------
# PATHS — resolved relative to this module
# ---------------------------------------------------------------------------
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIORITY_DISEASES_FILE = os.path.join(MODULE_DIR, "..", "data", "priority_diseases.json")


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLD = 1  # trigger when detection_count > THRESHOLD


# ---------------------------------------------------------------------------
# PRIORITY DISEASE LOADING
# ---------------------------------------------------------------------------
def load_priority_diseases(config_path: str = None) -> Tuple[List[str], str]:
    """
    Load the list of priority diseases from JSON config.
    
    Args:
        config_path: Optional override for config file path.
                     Defaults to ../data/priority_diseases.json
    
    Returns:
        (diseases_list, error_message)
        - diseases_list: List of disease name strings
        - error_message: None on success, error string on failure
    
    Example:
        >>> diseases, err = load_priority_diseases()
        >>> if err:
        ...     print(f"Error: {err}")
        >>> else:
        ...     print(f"Monitoring {len(diseases)} priority diseases")
    """
    path = config_path or PRIORITY_DISEASES_FILE
    
    if not os.path.exists(path):
        return [], "priority_diseases.json not found at: {}".format(path)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        diseases = data.get("priority_diseases", [])
        
        if not isinstance(diseases, list):
            return [], "priority_diseases.json is malformed (priority_diseases is not a list)."
        
        # Validate all entries are strings
        validated = [d for d in diseases if isinstance(d, str)]
        
        return validated, None
    
    except json.JSONDecodeError as e:
        return [], "priority_diseases.json contains invalid JSON: {}".format(e)
    except OSError as e:
        return [], "Could not read priority_diseases.json: {}".format(e)


# ---------------------------------------------------------------------------
# OBSERVATION FILTERING
# ---------------------------------------------------------------------------
def filter_observations_by_disease(
    observations: List[Dict],
    disease: str
) -> List[Dict]:
    """
    Filter observations to only those matching a specific disease.
    
    Args:
        observations: List of observation dicts from observations.json
        disease: Disease name to filter for
    
    Returns:
        List of observation dicts where observation['disease'] == disease
    
    Example:
        >>> obs = [{'disease': 'Late Blight', ...}, {'disease': 'Healthy', ...}]
        >>> filtered = filter_observations_by_disease(obs, 'Late Blight')
        >>> len(filtered)
        1
    """
    return [obs for obs in observations if obs.get("disease") == disease]


def count_unique_farmers(observations: List[Dict]) -> int:
    """
    Count the number of unique farmers in a list of observations.
    
    Args:
        observations: List of observation dicts
    
    Returns:
        Number of unique farmer_id values
    
    Example:
        >>> obs = [
        ...     {'farmer_id': '001', ...},
        ...     {'farmer_id': '001', ...},
        ...     {'farmer_id': '002', ...}
        ... ]
        >>> count_unique_farmers(obs)
        2
    """
    farmer_ids = {obs.get("farmer_id") for obs in observations if obs.get("farmer_id")}
    return len(farmer_ids)


# ---------------------------------------------------------------------------
# THRESHOLD ANALYSIS
# ---------------------------------------------------------------------------
def analyze_disease_threshold(
    observations: List[Dict],
    priority_diseases: List[str],
    threshold: int = DEFAULT_THRESHOLD
) -> Dict[str, Dict]:
    """
    Analyze all priority diseases and return detection statistics.
    
    For each priority disease:
      - Count total detections
      - Count unique farmers
      - Determine if threshold is exceeded
    
    Args:
        observations: List of observation dicts
        priority_diseases: List of disease names to analyze
        threshold: Detection count threshold (trigger if count > threshold)
    
    Returns:
        Dict mapping disease name → analysis dict:
        {
            'Late Blight': {
                'detection_count': 5,
                'unique_farmer_count': 3,
                'threshold_exceeded': True,
                'observations': [...]  # filtered observation list
            },
            ...
        }
    
    Example:
        >>> obs = [{'disease': 'Late Blight', 'farmer_id': '001'}, ...]
        >>> priority = ['Late Blight', 'Early Blight']
        >>> analysis = analyze_disease_threshold(obs, priority, threshold=1)
        >>> analysis['Late Blight']['threshold_exceeded']
        True
    """
    analysis = {}
    
    for disease in priority_diseases:
        filtered = filter_observations_by_disease(observations, disease)
        detection_count = len(filtered)
        unique_farmers = count_unique_farmers(filtered)
        
        analysis[disease] = {
            'detection_count': detection_count,
            'unique_farmer_count': unique_farmers,
            'threshold_exceeded': detection_count > threshold,
            'observations': filtered
        }
    
    return analysis


def get_triggered_diseases(
    observations: List[Dict],
    priority_diseases: List[str],
    threshold: int = DEFAULT_THRESHOLD
) -> List[str]:
    """
    Get list of diseases that exceed the trigger threshold.
    
    Args:
        observations: List of observation dicts
        priority_diseases: List of disease names to check
        threshold: Detection count threshold
    
    Returns:
        List of disease names where detection_count > threshold
    
    Example:
        >>> obs = [{'disease': 'Late Blight', ...}, {'disease': 'Late Blight', ...}]
        >>> triggered = get_triggered_diseases(obs, ['Late Blight'], threshold=1)
        >>> 'Late Blight' in triggered
        True
    """
    analysis = analyze_disease_threshold(observations, priority_diseases, threshold)
    return [disease for disease, stats in analysis.items() if stats['threshold_exceeded']]


# ---------------------------------------------------------------------------
# EVENT DEDUPLICATION
# ---------------------------------------------------------------------------
def get_covered_observation_ids(existing_events: List[Dict]) -> Dict[str, Set[str]]:
    """
    Extract observation IDs already covered by existing events.
    
    This prevents re-triggering events for the same observations on
    every polling cycle.
    
    Args:
        existing_events: List of event dicts from priority_events.json
    
    Returns:
        Dict mapping disease → set of observation_ids already in events
    
    Example:
        >>> events = [{
        ...     'disease': 'Late Blight',
        ...     'detections': [{'observation_id': 'OBS-001'}, ...]
        ... }]
        >>> covered = get_covered_observation_ids(events)
        >>> 'OBS-001' in covered['Late Blight']
        True
    """
    covered = {}
    
    for event in existing_events:
        disease = event.get("disease")
        if not disease:
            continue
        
        obs_ids = {
            det.get("observation_id")
            for det in event.get("detections", [])
            if det.get("observation_id")
        }
        
        covered.setdefault(disease, set()).update(obs_ids)
    
    return covered


def find_uncovered_observations(
    observations: List[Dict],
    covered_ids: Set[str]
) -> List[Dict]:
    """
    Filter observations to only those not yet covered by an event.
    
    Args:
        observations: List of observation dicts
        covered_ids: Set of observation_ids already in events
    
    Returns:
        List of observations not in covered_ids
    
    Example:
        >>> obs = [{'observation_id': 'OBS-001'}, {'observation_id': 'OBS-002'}]
        >>> covered = {'OBS-001'}
        >>> uncovered = find_uncovered_observations(obs, covered)
        >>> len(uncovered)
        1
    """
    return [obs for obs in observations if obs.get("observation_id") not in covered_ids]


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------
def should_trigger_event(
    disease: str,
    observations: List[Dict],
    existing_events: List[Dict],
    threshold: int = DEFAULT_THRESHOLD
) -> bool:
    """
    Quick check: should we trigger a new event for this disease?
    
    Returns True if:
      - detection_count > threshold
      - AND there are uncovered observations (not already in an event)
    
    Args:
        disease: Disease name to check
        observations: All observations for this disease
        existing_events: List of existing events
        threshold: Detection count threshold
    
    Returns:
        True if a new event should be triggered
    
    Example:
        >>> obs = [{'disease': 'Late Blight', 'observation_id': 'OBS-001'}, ...]
        >>> should_trigger_event('Late Blight', obs, [], threshold=1)
        True
    """
    if len(observations) <= threshold:
        return False
    
    covered = get_covered_observation_ids(existing_events)
    covered_ids = covered.get(disease, set())
    uncovered = find_uncovered_observations(observations, covered_ids)
    
    return len(uncovered) > 0


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Quick self-test when run directly
    print("Testing disease_filter.py...")
    print()
    
    # Test priority disease loading
    diseases, err = load_priority_diseases()
    if err:
        print(f"Error loading priority diseases: {err}")
    else:
        print(f"Loaded {len(diseases)} priority diseases: {diseases}")
    
    # Test with sample data
    sample_obs = [
        {"observation_id": "OBS-001", "farmer_id": "001", "disease": "Late Blight"},
        {"observation_id": "OBS-002", "farmer_id": "002", "disease": "Late Blight"},
        {"observation_id": "OBS-003", "farmer_id": "001", "disease": "Early Blight"},
        {"observation_id": "OBS-004", "farmer_id": "003", "disease": "Healthy"},
    ]
    
    print()
    print("Sample analysis:")
    analysis = analyze_disease_threshold(sample_obs, diseases, threshold=1)
    
    for disease, stats in analysis.items():
        print(f"  {disease}:")
        print(f"    Detections: {stats['detection_count']}")
        print(f"    Unique farmers: {stats['unique_farmer_count']}")
        print(f"    Threshold exceeded: {stats['threshold_exceeded']}")
    
    print()
    print("Triggered diseases:")
    triggered = get_triggered_diseases(sample_obs, diseases, threshold=1)
    for disease in triggered:
        print(f"  - {disease}")
    
    print()
    print("All tests passed!")