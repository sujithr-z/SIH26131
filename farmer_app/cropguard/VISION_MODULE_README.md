# 🌾 YOLO Image Recognition Module & Vision Subsystem

**CropGuard Agricultural Intelligence Platform**  
*Self-Contained Computer-Vision Subsystem & Structured Observation Pipeline*

---

## 1. Architecture Overview

The **Image Recognition Module** serves as the decoupled computer-vision engine for the CropGuard Farmer App. It follows a clean service boundary where the mobile client / web application captures and submits imagery, and the server executes quality validation, YOLO inference, post-processing, and persistence into the central database.

```
+-------------------------------------------------------------+
|                         FARMER APP                          |
|           (Capture Image / GPS / Crop Selection)            |
+-------------------------------------------------------------+
                              |
                              | HTTP POST (multipart/form-data)
                              v
+-------------------------------------------------------------+
|                      API / BACKEND                          |
|         (analyze.php / api/analyze_image.php)               |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                  IMAGE RECOGNITION MODULE                   |
|  +-------------------------------------------------------+  |
|  | 1. Image Quality Gate (Blur & Resolution Checks)       |  |
|  +-------------------------------------------------------+  |
|                             |                               |
|                             v                               |
|  +-------------------------------------------------------+  |
|  | 2. YOLOv8 Inference Engine (Ultralytics best.pt)      |  |
|  +-------------------------------------------------------+  |
|                             |                               |
|                             v                               |
|  +-------------------------------------------------------+  |
|  | 3. Post-Processing (NMS, Boxes, Affected Area %)      |  |
|  +-------------------------------------------------------+  |
|                             |                               |
|                             v                               |
|  +-------------------------------------------------------+  |
|  | 4. Agronomic Advisory & Precaution Lookup             |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                    CENTRAL DATABASE                         |
|      (data/observations.json via ObservationRepository)     |
+-------------------------------------------------------------+
        |                     |                     |
        v                     v                     v
   GIS Spatial          Surveillance /          Official
    Analysis             Weather Risk          Dashboard
```

---

## 2. Directory Structure

```text
cropguard/
├── vision/                                  # Independent Vision Subsystem
│   ├── __init__.py                          # Package exports
│   ├── config.py                            # Model paths, thresholds, class maps
│   ├── preprocessor.py                      # Image Quality Gate (blur, resolution)
│   ├── detector.py                          # YOLO model loader & inference engine
│   ├── postprocessor.py                     # Bounding boxes, severity, class normalization
│   ├── knowledge_base.py                    # Agronomic descriptions & precautions
│   ├── service.py                           # Python API: analyze_image(path)
│   └── cli.py                               # CLI bridge for PHP & external scripts
│
├── api/
│   ├── analyze_image.php                    # NEW: REST API endpoint for image diagnosis
│   ├── save_observation.php                # Observation persistence endpoint
│   └── get_observations.php                 # Enriched observations query endpoint
│
├── includes/
│   └── ObservationRepository.php            # Atomic DB repository for observations
│
├── data/
│   ├── observations.json                    # Central agricultural observation database
│   ├── farmers.json                         # Registered farmers database
│   ├── priority_diseases.json               # Monitored outbreak diseases config
│   └── priority_events.json                 # Triggered surveillance events
│
├── scripts/
│   ├── test_vision_pipeline.py              # Vision subsystem test suite
│   ├── test_e2e_integration.py              # Full end-to-end integration test
│   └── test_crud_consistency.py             # Database CRUD consistency test
│
├── YOLO-Based-Automatic-Crop-Disease-Detection-for-Smart-Agriculture-main/
│   ├── plant_disease/exp1/weights/best.pt   # Pretrained YOLOv8 model weights
│   ├── plantvillage.yaml                    # Dataset & class configuration
│   └── ...
│
├── analyze.php                              # Web analysis handler (invokes vision module)
├── diagnose.php                             # Farmer photo capture / dropzone UI
├── report.php                               # Diagnostic report view
└── requirements-vision.txt                  # Python dependencies
```

---

## 3. YOLO Model Location & Weights

- **Active Model Path**:  
  `cropguard/YOLO-Based-Automatic-Crop-Disease-Detection-for-Smart-Agriculture-main/plant_disease/exp1/weights/best.pt`
- **Model Architecture**: Ultralytics YOLOv8s (fine-tuned on PlantVillage dataset).
- **Model Version**: `yolo-agri-v1`
- **Fallback Base Weights**: `yolov8s.pt` / `yolov8n.pt` / `yolo11n.pt`

---

## 4. Inference Entry Points

### A. Python Programmatic Interface
```python
from vision.service import analyze_image

result = analyze_image("uploads/sample_leaf.jpg", crop="Tomato")
print(result)
```

### B. Command-Line Interface (CLI)
```bash
py -3.13 -m vision.cli --image uploads/sample_leaf.jpg --crop Tomato
```

---

## 5. REST API Endpoint

### `POST /api/analyze_image.php`
Accepts `multipart/form-data` with an image file and optional metadata.

#### Request Format:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `image` (or `crop_image`) | File (binary) | **Yes** | JPG, PNG, WEBP, or GIF leaf photo |
| `farmer_id` | String | No | Farmer ID (default: `"001"`) |
| `crop` | String | No | Crop name hint (e.g., `"Tomato"`, `"Apple"`) |
| `latitude` | Float | No | GPS Latitude coordinate |
| `longitude` | Float | No | GPS Longitude coordinate |

#### Example curl command:
```bash
curl -X POST http://localhost:8000/api/analyze_image.php \
  -F "image=@uploads/farmer002_1787734806.jpg" \
  -F "farmer_id=001" \
  -F "crop=Apple" \
  -F "latitude=9.2712" \
  -F "longitude=76.4721"
```

#### Response Format (200 OK):
```json
{
  "success": true,
  "observation_id": "OBS-000004",
  "farmer_id": "001",
  "crop": "Apple",
  "disease": "Apple Scab",
  "confidence": 0.6643,
  "severity": "High",
  "affected_area_percentage": 88.79,
  "detections": [
    {
      "crop": "Apple",
      "disease": "Apple Scab",
      "confidence": 0.6643,
      "is_healthy": false,
      "box_xyxy": [76.82, 40.36, 192.74, 158.79],
      "box_normalized": [0.398, 0.2538, 0.9987, 0.9987],
      "area_fraction": 0.4474
    }
  ],
  "description": "Apple Scab is caused by the fungus Venturia inaequalis...",
  "precautions": [
    {
      "icon": "✂️",
      "title": "Rake and Destroy Fallen Leaves",
      "text": "Infected leaves on the orchard floor harbor overwintering spores..."
    },
    {
      "icon": "💧",
      "title": "Apply Protective Fungicide",
      "text": "Spray sulfur or copper-based bio-fungicides..."
    }
  ],
  "model_version": "yolo-agri-v1",
  "image": {
    "relative_path": "uploads/api_001_1787823968_3d339b8b.jpg",
    "file_name": "api_001_1787823968_3d339b8b.jpg",
    "image_quality": {
      "width": 193,
      "height": 159,
      "channels": 3,
      "file_size_bytes": 4354,
      "blur_variance": 1503.32,
      "is_blurry": false,
      "quality_status": "ACCEPTABLE"
    }
  },
  "timestamp": "2026-08-27T09:46:19+00:00"
}
```

---

## 6. Database Storage & Downstream Integration

When an image is analyzed, an observation is persisted to `data/observations.json` via `ObservationRepository.php`:

```json
{
  "observation_id": "OBS-000004",
  "farmer_id": "001",
  "disease": "Apple Scab",
  "confidence": 0.6643,
  "timestamp": "2026-08-27T09:46:19+00:00",
  "crop": "Apple",
  "image_path": "uploads/api_001_1787823968_3d339b8b.jpg",
  "latitude": 9.2712,
  "longitude": 76.4721
}
```

Downstream consumers (`surveillance/monitor.py`, `gis/main.py`, `pipeline/build_report.py`) consume these structured observation records directly from the database without touching YOLO internals.

---

## 7. How to Replace or Upgrade the YOLO Model

To deploy a new model version:
1. Place the new `.pt` weights file into `vision/models/` or the YOLO directory (e.g. `weights/best_v2.pt`).
2. Update the path in `vision/config.py`:
   ```python
   DEFAULT_MODEL_PATH = YOLO_REPO_DIR / "path/to/new_weights.pt"
   MODEL_VERSION = "yolo-agri-v2"
   ```
3. If new classes were trained, add them to `PLANTVILLAGE_CLASSES` or `CLASS_NAME_ALIASES` in `vision/config.py` and register descriptions in `vision/knowledge_base.py`.

---

## 8. How to Retrain the Model

To train the YOLOv8 model on custom crop disease datasets:
```bash
cd YOLO-Based-Automatic-Crop-Disease-Detection-for-Smart-Agriculture-main
py -3.13 main.py train --data plantvillage.yaml --epochs 50 --cfg configs/yolov8s.yaml
```

The resulting weights will be exported to `plant_disease/exp<N>/weights/best.pt`.

---

## 9. Known Limitations

1. **Dataset Class Coverage**: The current `best.pt` model was trained on 10 PlantVillage classes (Apple Scab, Black Rot, Cedar Rust, Cherry Powdery Mildew, Corn Gray Leaf Spot, Corn Rust, Corn Blight, etc.). Unseen diseases are classified according to closest visual feature patterns or flagged as unclassified.
2. **Lighting & Clarity**: Leaves captured in extreme shadow or with motion blur will trigger the quality gate warning.
3. **Execution Runtime**: Local CPU inference takes ~1-3 seconds per image; GPU acceleration (CUDA) is automatically enabled when an NVIDIA GPU is available.
