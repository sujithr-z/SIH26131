# 🌾 CropGuard System Architecture & Master Integration Specification

**Agricultural Crop-Health Surveillance, Decision-Support, and Digital-Twin Platform**  
*Aligned with CROPSAP, NARO, and Edge-Cloud Digital-Twin Architectural Principles*

---

## 1. Executive Summary & Objective

CropGuard is an end-to-end agricultural crop-health surveillance and decision-support system designed for **"Early detection and management of crop diseases and pest infestations"**.

The platform decouples edge perception (farmer smartphone captures and voice interaction) from cloud computation (YOLOv8 disease diagnosis, geospatial GIS clustering, agro-meteorological risk analysis, and expert pathologist verification), closing the loop through automated multi-channel advisories (In-App alerts, SMS, and automated IVR voice notifications).

---

## 2. Master System Architecture Diagram

```
                             +-----------------------------------+
                             |       FARMER CLIENT (Edge)        |
                             |  • Leaf Photo Camera / Dropzone   |
                             |  • Multilingual (EN, HI, TA, ML)  |
                             |  • Voice Recognition & Audio TTS  |
                             |  • GPS Geolocation Auto-Capture   |
                             |  • Field & Crop Selector          |
                             +-----------------+-----------------+
                                               |
                                               | HTTPS REST API (Multipart/JSON)
                                               v
                             +-----------------------------------+
                             |            API GATEWAY            |
                             |  Authentication & Session Mgmt    |
                             |  Input Validation & Error Sanit.  |
                             +-----------------+-----------------+
                                               |
                     +-------------------------+-------------------------+
                     |                         |                         |
                     v                         v                         v
     +-------------------------------+ +---------------+ +-------------------------------+
     |   IMAGE RECOGNITION MODULE    | |  FARM/FIELD   | |      WEATHER INGESTION        |
     | • Laplacian Blur Quality Gate | |  MANAGEMENT   | | • Temp, Humidity, Rain, Wind  |
     | • YOLOv8 Detection Engine     | | • Farmer ID   | | • Fungal Spore Index Calc     |
     | • Severity & Affected Area %  | | • Field ID    | | • Spatial Met Grid Ingestion  |
     +---------------+---------------+ +-------+-------+ +---------------+---------------+
                     |                         |                         |
                     +-------------------------+-------------------------+
                                               |
                                               v
                             +-----------------------------------+
                             |      CENTRAL DATA PLATFORM        |
                             |     (Single Source of Truth)      |
                             |                                   |
                             | • observations.json (with lock)   |
                             | • farmers.json & fields.json      |
                             | • weather_observations.json       |
                             | • priority_events.json            |
                             | • expert_validations.json         |
                             | • notifications.json & call_log   |
                             +-----------------+-----------------+
                                               |
                     +-------------------------+-------------------------+
                     |                         |                         |
                     v                         v                         v
       +---------------------------+ +-------------------+ +---------------------------+
       |   GEOSPATIAL GIS ENGINE   | | SURVEILLANCE RISK | |    DIGITAL TWIN ENGINE    |
       | • Haversine Pairwise Dist | | • Spatial Density | | • Farm/Field Hierarchy    |
       | • Cluster Grouping (R<=15)| | • Humidity Weight | | • Live Observation State  |
       | • Centroid & Heatmap Gen  | | • Prototype Risk  | | • Historical Trajectory   |
       +-------------+-------------+ +---------+---------+ +-------------+-------------+
                     |                         |                         |
                     +-------------------------+-------------------------+
                                               |
                                               v
                             +-----------------------------------+
                             |     SURVEILLANCE ALERT ENGINE     |
                             |  Trigger: Count >= 2 & Radius<=15 |
                             +-----------------+-----------------+
                                               |
                                    [POSSIBLE HOTSPOT EVENT]
                                               |
                            +------------------+------------------+
                            |                                     |
                            v                                     v
             +------------------------------+      +------------------------------+
             |      OFFICIAL DASHBOARD      |      |      EXPERT REVIEW PORTAL    |
             | • Live Outbreak Risk Gauge   |      | • High-Res Leaf Specimen     |
             | • Dynamic Interactive GIS Map|      | • YOLO Bounding Box Overlay  |
             | • Pipeline Progress Tracker  |      | • Action: CONFIRM / REJECT   |
             | • Unified Database Overview  |      | • Agronomic Treatment Notes  |
             +--------------+---------------+      +--------------+---------------+
                            |                                     |
                            +------------------+------------------+
                                               |
                                       [CONFIRMED CASE]
                                               |
                                               v
                             +-----------------------------------+
                             |          ADVISORY ENGINE          |
                             | • Organic Bio-Fungicide Guidance  |
                             | • Cultural & Soil Management      |
                             +-----------------+-----------------+
                                               |
                            +------------------+------------------+
                            |                  |                  |
                            v                  v                  v
                     +--------------+   +--------------+   +--------------+
                     | IN-APP ALERT |   |  SMS ENGINE  |   |  VOICE / IVR |
                     | Red Warning  |   | Phone Alert  |   | Call Machine |
                     | Banner + TTS |   | Notification |   |  Simulator   |
                     +--------------+   +--------------+   +--------------+
                                               |
                                               v
                             +-----------------------------------+
                             |       FARMER FOLLOW-UP LOOP       |
                             | Recovery Leaf Photo Submission    |
                             +-----------------------------------+
```

---

## 3. Data Flow & Closed-Loop Lifecycle

```
   [FIELD] Farmer photographs leaf
      │
      ▼
   [PERCEPTION] Image Quality Gate -> YOLOv8 detects disease lesions & bounding boxes
      │
      ▼
   [CENTRAL DB] Observation persisted to observations.json (with atomic lock)
      │
      ▼
   [GIS ENGINE] Spatial clustering groups nearby detections (Radius <= 15 km)
      │
      ▼
   [RISK ENGINE] Risk = 0.35(Spatial) + 0.25(Weather) + 0.20(Confidence) + 0.20(Severity)
      │
      ▼
   [SURVEILLANCE] Threshold exceeded (Count >= 2) -> Emits "POSSIBLE HOTSPOT" event
      │
      ▼
   [EXPERT PORTAL] Agricultural pathologist inspects AI evidence, field, and weather
      │
      ▼
   [VALIDATION] Expert clicks CONFIRM -> Status becomes "CONFIRMED CASE"
      │
      ▼
   [ADVISORY] Targeted bio-fungicide & cultural precautions attached
      │
      ▼
   [DISSEMINATION] In-App Warning Banner + SMS text + Automated IVR phone call
      │
      ▼
   [FOLLOW-UP] Farmer applies treatment and submits follow-up recovery photo
      │
      ▼
   [DIGITAL TWIN] Central database updates digital farm health state
```

---

## 4. Database Schema (Single Source of Truth)

All modules communicate strictly through [`includes/DatabaseManager.php`](file:///d:/SIH26131-materials/SIH26131-materials/prototype_0.1/farmer_app/cropguard/includes/DatabaseManager.php) and [`includes/ObservationRepository.php`](file:///d:/SIH26131-materials/SIH26131-materials/prototype_0.1/farmer_app/cropguard/includes/ObservationRepository.php):

### A. `data/farmers.json`
```json
[
  {
    "farmer_id": "001",
    "full_name": "sujith",
    "phone": "8870210301",
    "created_at": "2026-08-26 08:40:32"
  }
]
```

### B. `data/fields.json`
```json
[
  {
    "field_id": "FIELD-001",
    "farmer_id": "001",
    "field_name": "North Orchard - Plot A",
    "crop": "Apple",
    "area_acres": 2.5,
    "latitude": 9.2712,
    "longitude": 76.4721,
    "sowing_date": "2026-03-15"
  }
]
```

### C. `data/observations.json`
```json
{
  "observations": [
    {
      "observation_id": "OBS-000006",
      "farmer_id": "001",
      "field_id": "FIELD-001",
      "crop": "Apple",
      "disease": "Apple Scab",
      "confidence": 0.6643,
      "severity": "High",
      "affected_area_percentage": 88.79,
      "image_path": "uploads/api_001_1787826934_6bb2559b.jpg",
      "latitude": 9.2712,
      "longitude": 76.4721,
      "timestamp": "2026-08-27T10:35:34+00:00",
      "validation_status": "CONFIRMED",
      "expert_id": "Dr. Ananya Sharma (Lead Agronomist)",
      "expert_notes": "Confirmed fungal lesion margins. Issued urgent copper bio-fungicide protocol.",
      "follow_up_to": null,
      "model_version": "yolo-agri-v1"
    }
  ]
}
```

### D. `data/weather_observations.json`
```json
[
  {
    "weather_id": "WX-001",
    "location_name": "Chengannur Central",
    "latitude": 9.2712,
    "longitude": 76.4721,
    "temperature_c": 28.5,
    "humidity_percent": 84.0,
    "wind_speed_kmh": 14.2,
    "rainfall_mm": 12.5,
    "condition": "Humid / Overcast (High Fungal Spore Propagation Risk)",
    "timestamp": "2026-08-27T08:00:00+05:30"
  }
]
```

### E. `data/expert_validations.json`
```json
[
  {
    "validation_id": "VAL-1787826938-518",
    "observation_id": "OBS-000006",
    "action": "CONFIRM",
    "validation_status": "CONFIRMED",
    "crop": "Apple",
    "disease": "Apple Scab",
    "expert_name": "Dr. Ananya Sharma (Lead Agronomist)",
    "expert_notes": "Confirmed fungal lesion margins. Issued urgent copper bio-fungicide protocol.",
    "timestamp": "2026-08-27T10:35:38+00:00"
  }
]
```

### F. `data/notifications.json` & `data/call_log.json`
```json
[
  {
    "notification_id": "NOTIF-1787826938-164",
    "farmer_id": "001",
    "farmer_name": "sujith",
    "phone": "8870210301",
    "disease": "Apple Scab",
    "channel": "SMS & In-App",
    "message": "CropGuard Advisory: Apple Scab has been CONFIRMED by Dr. Ananya Sharma. Recommended immediate action: Apply protective bio-fungicide and isolate affected rows.",
    "status": "SENT",
    "timestamp": "2026-08-27T10:35:38+00:00"
  }
]
```

---

## 5. Master API Specifications

| Route | Method | Payload / Parameters | Response | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `/api/fields.php` | `GET` / `POST` | `farmer_id`, `field_name`, `crop`, `area_acres`, `lat`, `lon` | `{success: true, fields: [...]}` | Farm and field entity management |
| `/api/weather.php` | `GET` | `lat`, `lon` | `{success: true, weather: {...}, disease_favorable: true}` | Agro-meteorological parameter ingestion |
| `/api/analyze_image.php` | `POST` | `multipart/form-data` (`image`, `farmer_id`, `crop`, `field_id`, `lat`, `lon`) | Full structured observation JSON | Image quality validation, YOLO inference & persistence |
| `/api/get_observations.php` | `GET` | None | `{success: true, observations: [...], stats: {...}}` | Authoritative observation stream & statistics |
| `/api/expert_review.php` | `GET` / `POST` | `observation_id`, `action`, `expert_name`, `expert_notes` | `{success: true, validation: {...}}` | Pathologist inspection & validation feedback loop |
| `/api/trigger_alert.php` | `POST` | `action`, `event_id`, `disease`, `risk_label`, `officer` | `{success: true, calls_initiated: N}` | Official alert broadcast & SMS/IVR simulator |
| `/api/get_digital_twin.php` | `GET` | None | `{success: true, digital_twin: {...}}` | Structured digital-twin farm & ecosystem state |

---

## 6. Implementation Status Matrix

| Component | Status | Details |
| :--- | :--- | :--- |
| **YOLO Perception Engine** | ✅ **IMPLEMENTED** | Ultralytics YOLOv8s fine-tuned on PlantVillage dataset (`best.pt`). Quality gate blur check, bounding box extraction, affected area %. |
| **Central System of Record** | ✅ **IMPLEMENTED** | `DatabaseManager.php` and `ObservationRepository.php` with atomic file locks and uniform CRUD consistency. |
| **Farmer Mobile UI** | ✅ **IMPLEMENTED** | Responsive mobile card UI with Camera/Dropzone, GPS auto-fetch, Field selector, and History timeline. |
| **Multilingual Interaction** | ✅ **IMPLEMENTED** | Real-time client-side localization for English, हिन्दी (Hindi), தமிழ் (Tamil), and മലയാളം (Malayalam). |
| **Voice Input & TTS Advisory** | ✅ **IMPLEMENTED** | Web Speech API speech-to-text input + SpeechSynthesis TTS audio advisory playback. |
| **Geospatial GIS Engine** | ✅ **IMPLEMENTED** | Haversine distance matrix, cluster detection ($R \le 15\text{ km}, T \le 7\text{ days}$), and visual map rendering. |
| **Surveillance & Risk Engine**| ✅ **IMPLEMENTED** | Weighted risk formula combining spatial density, agro-meteorological humidity, YOLO confidence, and lesion severity. |
| **Expert Validation Portal** | ✅ **IMPLEMENTED** | Dedicated official gateway (`expert_review.php`) supporting `CONFIRM`, `REJECT`, and custom agronomic advice. |
| **Multi-Channel Alerting** | ✅ **IMPLEMENTED** | In-App warning cards, SMS notification logs, and asynchronous IVR call queue simulation (`call_simulator.php`). |
| **Digital Twin Engine** | ✅ **IMPLEMENTED** | Live structured hierarchy (`Farmer -> Farm -> Field -> Crop -> Observation -> Disease -> Risk -> Alert -> Validation`). |
| **Statewide Real Weather API**| 🟡 **MOCKED / INGESTION INTERFACE**| Fully functional weather ingestion interface (`api/weather.php`) with Kerala monsoon baseline parameters. |
| **Physical GSM / SMS Gateway**| 🟡 **SIMULATED** | Full transactional SMS and IVR call logging pipeline ready for Twilio / Fast2SMS webhook integration. |

---

## 7. How to Run the Entire System

```bash
# 1. Start the PHP Application Server
php -S 127.0.0.1:8000

# 2. Run the Background Surveillance Monitor (in terminal 2)
py -3.13 surveillance/monitor.py

# 3. Run the Complete Master Acceptance Test Suite anytime
py -3.13 scripts/test_master_system.py
```

### Portal URLs:
- **Farmer App**: `http://127.0.0.1:8000/index.php` (or `diagnose.php`)
- **Farmer Observation History**: `http://127.0.0.1:8000/history.php`
- **Farmer Surveillance Warning**: `http://127.0.0.1:8000/farmer_alert.php`
- **Expert Validation Portal**: `http://127.0.0.1:8000/expert_review.php`
- **Official Monitoring Dashboard**: `http://127.0.0.1:8000/dashboard/agri_disease_surveillance_dashboard.html`
- **Digital Twin State API**: `http://127.0.0.1:8000/api/get_digital_twin.php`
