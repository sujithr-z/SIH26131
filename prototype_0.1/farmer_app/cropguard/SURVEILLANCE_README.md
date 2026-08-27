# CropGuard — Agricultural Disease Surveillance System

Complete end-to-end surveillance pipeline for detecting and monitoring priority agricultural diseases across a farmer network.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       FARMER APP                                 │
│    (diagnose.php → analyze.php → report.php)                    │
│                                                                   │
│  Farmer submits disease observation with photo & confidence     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │   PHP API                         │
        │  (api/save_observation.php)       │
        │                                   │
        │  • Validates farmer input        │
        │  • Assigns observation_id        │
        │  • Persists to database          │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │   observations.json               │
        │   (Append-only log)              │
        │                                   │
        │   [{                             │
        │     observation_id: "OBS-000001",│
        │     farmer_id: "001",            │
        │     disease: "Early Blight",     │
        │     confidence: 0.942,           │
        │     ...                          │
        │   }, ...]                        │
        └──────────┬───────────────────────┘
                   │
                   │ (polls every 1s)
                   ▼
        ┌──────────────────────────────────┐
        │   monitor.py                      │
        │   (Surveillance Engine)           │
        │                                   │
        │  • Loads observations             │
        │  • Filters by priority diseases   │
        │  • Counts detections per disease  │
        │  • Checks threshold (>1)          │
        │  • Deduplicates events            │
        └──────────┬───────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
    [No trigger]    [Trigger: 2+ detections]
    (< threshold)     (non-duplicate)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    location.py  weather.py   disease_filter.py
        │             │             │
    Adds GPS      Adds weather   Enriches data
        │             │             │
        └─────────────┴─────────────┘
                      │
                      ▼
        ┌──────────────────────────────────┐
        │   priority_events.json            │
        │   (Output database)               │
        │                                   │
        │   [{                             │
        │     event_id: "EVENT-0001",      │
        │     disease: "Early Blight",     │
        │     detection_count: 2,          │
        │     detections: [                │
        │       {                          │
        │         farmer_id: "001",        │
        │         latitude: 9.2645,        │
        │         longitude: 76.4600,      │
        │         weather: {...},          │
        │         ...                      │
        │       }, ...                     │
        │     ]                            │
        │   }, ...]                        │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │   [Future: Geospatial Computation]│
        │   • Calculate disease spread      │
        │   • Risk mapping                  │
        │   • Alerts to authorities        │
        └──────────────────────────────────┘
```

## Architecture

### Layer 1: Data Ingestion (Farmer App + PHP API)
- **Farmer submits observation** via web form with photo, disease name, confidence
- **PHP validates** farmer credentials, input formats, confidence range (0-1)
- **ObservationRepository** provides single read/write boundary to observations.json
- **API endpoint** (`api/save_observation.php`) accepts external JSON requests

### Layer 2: Observations Database
- **observations.json** — Append-only log of all farmer observations
- **Schema**:
  ```json
  {
    "observation_id": "OBS-000001",
    "farmer_id": "001",
    "disease": "Early Blight",
    "confidence": 0.942,
    "timestamp": "2026-08-26T04:10:13+00:00",
    "crop": "Tomato",
    "image_path": "uploads/farmer001_1787717413.jpg"
  }
  ```

### Layer 3: Surveillance Engine (Python)
- **monitor.py** — Live polling backend that:
  1. Reads observations.json every 1 second
  2. Filters by priority diseases (defined in config)
  3. Counts detections per disease
  4. Triggers events when detection_count > THRESHOLD
  5. Prevents re-triggering on same observations
  6. Enriches events with location & weather data
  7. Prints terminal alerts with formatted output
  8. Saves events to priority_events.json

### Layer 4: Configuration & Data Providers
- **priority_diseases.json** — List of diseases to monitor
  ```json
  {
    "priority_diseases": ["Late Blight", "Bacterial Blight", "Early Blight"],
    "config_metadata": { "version": "1.0.0", ... }
  }
  ```
- **location.py** — Provides (latitude, longitude) for observations
  - Current: Dummy pool of Kerala region coordinates
  - Future: Real GPS from devices or farmer profiles
- **weather.py** — Provides weather conditions
  - Current: Simulated Kerala/India monsoon conditions
  - Future: Real weather API (OpenWeatherMap, etc.)
- **disease_filter.py** — Helper functions for disease analysis

### Layer 5: Events Database
- **priority_events.json** — Output database of triggered surveillance events
- **Schema**:
  ```json
  {
    "event_id": "EVENT-0001",
    "disease": "Early Blight",
    "detection_count": 2,
    "unique_farmer_count": 2,
    "status": "TRIGGERED",
    "generated_at": "2026-08-26T14:30:00Z",
    "detections": [
      {
        "observation_id": "OBS-000001",
        "farmer_id": "001",
        "latitude": 9.2645,
        "longitude": 76.4600,
        "weather": { "temperature_c": 28.4, "humidity_percent": 86, ... },
        ...
      }, ...
    ]
  }
  ```

## Running the System

### Prerequisites
```bash
# Python 3.6+ with standard library only (no external packages)
python3 --version

# PHP 7.4+ with built-in server or Apache/Nginx
php --version
```

### Step 1: Start PHP Server (Optional - for farmer app testing)
```bash
cd farmer-app/cropguard
php -S localhost:8000
# Visit: http://localhost:8000
```

### Step 2: Start Surveillance Monitor
```bash
cd farmer-app/cropguard/surveillance
python3 monitor.py
```

The monitor will:
- Load priority diseases from config
- Display current observations in a table
- Poll for new observations every 1 second
- Print alerts when thresholds are exceeded
- Save triggered events to priority_events.json

**Output example:**
```
==============================================================
 AGRICULTURAL DISEASE SURVEILLANCE
==============================================================

Database observations : 2
Priority diseases     : 3
Last update           : 2026-08-26 09:41:14

--------------------------------------------------------------
 OBSERVATIONS
--------------------------------------------------------------
| ID         | FARMER | DISEASE              | CONFIDENCE |
--------------------------------------------------------------
| OBS-000001 | 001    | Early Blight         | 94.2%      |
| OBS-000002 | 002    | Early Blight         | 94.2%      |
--------------------------------------------------------------

==============================================================
 PRIORITY DISEASE DETECTED
==============================================================

Disease          : Early Blight
Detection count  : 2
Unique farmers   : 2
STATUS           : TRIGGERED

First detection:
  Farmer     : 001
  Location   : 9.2645, 76.4600
  Confidence : 94.2%

Second detection:
  Farmer     : 002
  Location   : 9.2712, 76.4721
  Confidence : 94.2%

Weather (sample):
  Temperature : 28.5 °C
  Humidity    : 87%
  Wind Speed  : 7.4 km/h

>>> Sending event to computation stage...

==============================================================
```

### Step 3: Submit Test Observations (via API)
```bash
# Terminal 1: Running monitor.py
# Terminal 2: Submit observations via curl

curl -X POST http://localhost:8000/api/save_observation.php \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": "001",
    "disease": "Early Blight",
    "confidence": 0.94,
    "crop": "Tomato"
  }'

# Monitor will show this observation within 1 second
# When you submit a second observation of the same disease,
# the monitor will trigger an event
```

## Integration Checklist

### ✅ File Structure
- [x] All files exist in correct locations
- [x] Data directories created
- [x] File paths resolve correctly from any working directory

### ✅ Component Testing
- [x] `disease_filter.py` loads priority diseases
- [x] `location.py` generates dummy locations
- [x] `weather.py` generates dummy weather
- [x] `monitor.py` loads observations
- [x] `monitor.py` analyzes thresholds
- [x] `monitor.py` enriches events with location & weather
- [x] `monitor.py` saves to priority_events.json

### ✅ Pipeline Testing
- [x] Single observation does NOT trigger (status: MONITORING)
- [x] 2+ observations of same disease TRIGGER event (status: TRIGGERED)
- [x] Events include latitude, longitude from location.py
- [x] Events include temperature, humidity, wind from weather.py
- [x] Terminal output shows formatted alerts
- [x] priority_events.json created with correct structure

### ✅ Error Handling
- [x] Corrupt observations.json doesn't crash monitor (graceful recovery)
- [x] Empty observations.json handled correctly
- [x] Missing priority_diseases.json handled gracefully
- [x] Malformed JSON returns empty list + error message
- [x] Monitor continues polling after transient errors
- [x] No duplicate events for same observation_ids

### ✅ Data Flow Verification
After triggering an event, verify:
1. Event saved to priority_events.json with:
   - event_id, disease, detection_count, unique_farmer_count
   - detections array with observation_id, farmer_id, confidence
   - latitude/longitude from location.py
   - weather data (temperature_c, humidity_percent, wind_speed_kmh)
2. Terminal output shows formatted alert with detections
3. Subsequent runs don't re-trigger same observations

---

## Configuration

### Threshold
Edit `surveillance/monitor.py`:
```python
THRESHOLD = 1  # Trigger when detection_count > THRESHOLD
```
- Current: 1 (trigger on 2+ detections)
- Increase for less frequent alerts
- Decrease for more sensitive monitoring

### Poll Interval
Edit `surveillance/monitor.py`:
```python
POLL_SECONDS = 1.0  # Check for new observations every 1 second
```
- Default: 1 second (real-time)
- Increase for lower CPU usage
- Decrease for faster detection

### Priority Diseases
Edit `data/priority_diseases.json`:
```json
{
  "priority_diseases": [
    "Late Blight",
    "Bacterial Blight",
    "Early Blight",
    "Add more as needed..."
  ]
}
```

---

## Future Enhancements

### 1. Real GPS / Location Data
**Current**: Dummy location pool
```python
# surveillance/location.py
def get_device_location(device_id: str):
    # TODO: Query device registry or GPS tracking API
    pass
```

**Future options**:
- Read from device registration database
- Integrate with mobile device GPS
- Geocode farmer address
- Use IoT sensor coordinates

### 2. Real Weather Data
**Current**: Simulated monsoon conditions
```python
# surveillance/weather.py
def get_real_weather(latitude, longitude):
    # TODO: Call weather API
    pass
```

**Future options**:
- OpenWeatherMap API
- WeatherAPI.com
- NOAA weather data
- Local weather station network
- Historical weather for timestamp

### 3. Geospatial Computation
**Current**: Events saved to database
**Future**:
- Calculate disease spread zones (buffer around detections)
- Risk mapping with heatmaps
- Predict next affected areas
- Weather-disease correlation analysis
- Alert generation for authorities

### 4. Map Visualization
- Display triggered events on map
- Show farmer locations and detections
- Weather overlay
- Disease spread zones
- Risk heatmaps

### 5. Alert System
- Email notifications to authorities
- SMS alerts for priority events
- Push notifications to mobile app
- Alert distribution based on geography

### 6. Database Upgrade
**Current**: JSON files
**Future**:
- SQLite for prototype scaling
- PostgreSQL for production
- Only change ObservationRepository class
- No changes needed to monitor.py or calling code

### 7. Analytics Dashboard
- Historical disease trends
- Seasonal patterns
- Farmer productivity reports
- Disease-weather correlations
- Prediction models

---

## Troubleshooting

### Monitor shows "No observations yet"
- Check that farmer app is submitting observations
- Verify observations.json exists and is valid JSON
- Check file permissions (observations.json must be readable)

### Events not triggering
- Check THRESHOLD value in monitor.py (default: 1, triggers on 2+)
- Verify disease name in observation matches priority_diseases.json exactly (case-sensitive)
- Check that detection_count > THRESHOLD
- Look for error messages in terminal output

### Duplicate events
- Events are deduplicated by observation_id
- If you want to re-test triggering, clear priority_events.json
- Each run of monitor.py checks if observations are already in events

### Monitor crashes with JSON error
- Check observations.json syntax with: `python3 -m json.tool observations.json`
- If file is mid-write, monitor will retry in 1 second
- Clear or restore from backup if necessary

### File not found errors
- Ensure you run monitor.py from surveillance/ directory
- Or update file paths in monitor.py to use absolute paths
- Check that ../data/ paths resolve correctly

---

## Testing Scenarios

### Scenario 1: Monitor Startup
```bash
python3 monitor.py
# Expected: Shows current observations, "No observations yet" if empty
```

### Scenario 2: Single Detection
```bash
# Add 1 observation of priority disease
# Expected: "MONITORING" status, no event triggered
```

### Scenario 3: Threshold Exceeded
```bash
# Add 2 observations of same priority disease from different farmers
# Expected: "PRIORITY DISEASE DETECTED" alert printed
#           event_id generated and saved
#           weather/location data attached
```

### Scenario 4: Different Disease
```bash
# Add 2 observations of non-priority disease
# Expected: No trigger (disease not in priority list)
```

### Scenario 5: Error Recovery
```bash
# Corrupt observations.json while monitor is running
# Expected: Monitor shows error message but continues polling
# Fix JSON → Monitor recovers automatically within 1 second
```

---

## File Reference

| File | Purpose | Type |
|------|---------|------|
| `index.php` | Login page | Farmer UI |
| `login.php` | Login handler | Farmer UI |
| `diagnose.php` | Disease diagnosis form | Farmer UI |
| `analyze.php` | AI analysis (calls ObservationRepository.save) | Farmer UI + API |
| `report.php` | Diagnosis report | Farmer UI |
| `logout.php` | Session termination | Farmer UI |
| `api/save_observation.php` | JSON HTTP endpoint | API |
| `includes/ObservationRepository.php` | Observations I/O | Backend |
| `data/observations.json` | Observation log | Database |
| `data/priority_diseases.json` | Disease config | Config |
| `data/priority_events.json` | Triggered events | Database |
| `surveillance/monitor.py` | Live monitoring engine | Backend |
| `surveillance/disease_filter.py` | Disease analysis helpers | Backend |
| `surveillance/location.py` | Location data provider | Backend |
| `surveillance/weather.py` | Weather data provider | Backend |
| `js/main.js` | Frontend interactivity | Farmer UI |
| `css/style.css` | Frontend styling | Farmer UI |
| `uploads/` | Farmer-submitted images | Storage |

---

## Architecture Decision Log

### Why Python for monitor.py?
- Standard library only (no external dependencies)
- Rapid development without environment setup
- Cross-platform (works on Linux, macOS, Windows)
- Easy to understand and extend
- Perfect for prototyping

### Why JSON for data?
- Human-readable and debuggable
- No database setup required
- Append-only observations.json prevents accidental deletion
- Easy to version control and backup
- Clear structure for future upgrade to SQL

### Why single ObservationRepository class?
- One place to change when upgrading to database
- Prevents data consistency issues
- Enforces validation rules
- Clear separation of concerns

### Why monitor.py polls instead of event-driven?
- No message queue setup required
- Fault-tolerant (missing updates recoverable)
- Deterministic behavior
- Easy to understand timing
- Can be upgraded to push-based later

### Why deduplication by observation_id?
- Prevents re-triggering on same data
- Avoids alert fatigue
- Ensures one event per unique set of observations
- Clear audit trail

---

## Performance Notes

- **Polling**: 1 second interval, ~5-10ms processing per cycle
- **JSON I/O**: Fast for <10k observations (future: upgrade to SQLite)
- **Memory**: ~1-2 MB for full system (negligible)
- **Disk space**: ~1KB per observation + event metadata

For production with 100k+ observations:
- Migrate observations.json to SQLite
- Index by farmer_id, disease, timestamp
- Query only new observations since last check
- Archive old events separately

---

## Support & Maintenance

### Adding New Priority Disease
1. Edit `data/priority_diseases.json` — add disease name
2. Restart monitor.py
3. Next observation of that disease will be analyzed

### Changing Trigger Threshold
1. Edit `THRESHOLD` in `surveillance/monitor.py`
2. Restart monitor.py
3. Takes effect immediately

### Backing Up Data
```bash
# Events are important — back these up
cp data/observations.json data/observations.json.backup
cp data/priority_events.json data/priority_events.json.backup

# Or full directory backup
tar czf backup-$(date +%Y%m%d).tar.gz data/
```

### Resetting System (for testing)
```bash
# Clear observations but keep structure
echo '{"observations": []}' > data/observations.json

# Clear events but keep structure
echo '{"events": [], "metadata": {...}}' > data/priority_events.json

# Restart monitor.py
python3 surveillance/monitor.py
```

---

## License & Credits

Agricultural Disease Surveillance System v1.0
Built for SIH26131 — Smart India Hackathon

System Design: Multi-layer pipeline architecture
- Data Ingestion: Farmer App + PHP API
- Storage: JSON databases
- Processing: Python surveillance engine
- Output: Event database + terminal alerts
- Future: Geospatial computation & visualization

---

**Last Updated**: 2026-08-26  
**Status**: ✅ Integration Complete & Tested  
**Version**: 1.0 Prototype  
