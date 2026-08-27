# 🌾 YOLOv8-Based Automatic Crop Disease Detection

An end-to-end crop disease detection system built on **YOLOv8**, designed for smart agriculture applications with real-time inference and edge device deployment support.

---

## 📌 Overview

Early and accurate detection of crop diseases is critical to preventing yield loss and ensuring food security. Traditional manual inspection is labor-intensive and error-prone.

This project leverages the **YOLOv8 object detection framework** and the **PlantVillage dataset** to build an automated crop disease detection system. To better reflect practical agricultural applications, we further introduce two agriculture-oriented evaluation metrics:

- **SSER (Severity Score Error Rate)** — evaluates disease severity estimation accuracy.
- **EIS (Economic Impact Score)** — measures detection effectiveness based on economic importance.

---

## 🚀 Key Features

- ✅ **High Detection Accuracy**
  - **68.4% mAP@0.5**
  - **44.6% mAP@0.5:0.95**

- ⚡ **Real-Time Inference**
  - RTX 3070: **88 FPS**
  - Jetson Xavier NX: **32 FPS**

- 🌱 **Agriculture-Specific Evaluation**
  - SSER (Severity Score Error Rate)
  - EIS (Economic Impact Score)

- 🤖 **Deployment Ready**
  - Lightweight architecture suitable for UAVs, agricultural robots, and edge AI devices.

---

## 🧬 Dataset

**Source**

- PlantVillage public dataset
- Over **50,000** leaf images
- **14 crop species**
- Healthy and diseased samples

### Dataset Processing

- Converted classification labels into YOLO object detection format.
- Annotated **1,200** images using **LabelImg**.
- Inter-annotator agreement: **92.6%**.
- Generated center-based pseudo bounding boxes for remaining samples.
- Validation on 200 manually annotated images achieved **IoU = 0.85**.

---

## 🛠️ Methodology

### Data Augmentation

To improve robustness under field conditions, the following augmentations were applied:

| Technique | Setting |
|-----------|----------|
| HSV Adjustment | ±20% |
| Mosaic | 0.5 |
| Random Rotation | ±15° |
| Scaling | 0.8–1.2 |

> All hyperparameters were selected using grid search.

---

### Model Architecture

#### Backbone

- CSP (Cross Stage Partial) Network
- Preserves fine-grained texture information
- Reduces computation by approximately **30%**

#### Neck

- AFPN (Asymptotic Feature Pyramid Network)
- Enhances multi-scale feature fusion
- Improves small lesion detection

#### Head

- YOLOv8 Detection Head
- Performs bounding box regression and disease classification in a single forward pass

---

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Epochs | 20 |
| Batch Size | 16 |
| Image Size | 640 × 640 |
| Optimizer | SGD |
| Warmup | 0.001 → 0.01 (first 3 epochs) |
| Train / Val / Test | 70% / 20% / 10% |

---

## 📊 Experimental Results

| Model | mAP@0.5 | mAP@0.5:0.95 | FPS | Params (M) | SSER ↓ | EIS ↑ |
|------|---------|--------------|-----|------------|--------|--------|
| YOLOv5s | 66.7 | 42.4 | 85 | 7.2 | 0.164 | 0.687 |
| **YOLOv8s** | **68.4** | **44.6** | **88** | **11.2** | **0.091** | **0.942** |

### Ablation Study

Data augmentation improves model performance by:

- **+1.7% mAP@0.5**

---

## 📈 Agriculture-Specific Metrics

### SSER (Severity Score Error Rate)

Measures the relative error between predicted and ground-truth diseased area.

\[
SSER=\frac{1}{N}\sum\left|\frac{A_{pred}-A_{gt}}{A_{gt}}\right|
\]

Where:

- \(A_{pred}\): predicted diseased area
- \(A_{gt}\): ground-truth diseased area

Lower values indicate better estimation accuracy.

---

### EIS (Economic Impact Score)

Measures detection effectiveness according to agricultural economic importance.

\[
EIS=\sum \omega_i s_i
\]

Where:

- \(s_i\): detection score
- \(\omega_i\): crop-specific economic weight

Example weights:

| Disease Location | Weight |
|-----------------|--------|
| Stem | 1.0 |
| Leaf | 0.7 |

The weighting strategy was validated with agronomists.

---

## 🧪 Getting Started

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Train

```bash
python train.py \
    --data config/plantvillage.yaml \
    --epochs 20 \
    --batch 16 \
    --imgsz 640
```

### Inference

```bash
python detect.py \
    --weights runs/train/exp/weights/best.pt \
    --source path/to/images
```

### Evaluation

```bash
python val.py \
    --data config/plantvillage.yaml \
    --weights best.pt
```

---

## 📁 Project Structure

```text
.
├── config/
│   ├── plantvillage.yaml
│   └── training configuration
│
├── data/
│   ├── images/
│   ├── labels/
│   └── dataset configuration
│
├── models/
│   ├── YOLOv8 architecture
│   └── AFPN implementation
│
├── utils/
│   ├── augmentations.py
│   ├── sser.py
│   ├── eis.py
│   └── helper functions
│
├── train.py
├── detect.py
├── val.py
├── requirements.txt
└── README.md
```

---

## 🔮 Future Work

- Integrate spatial-temporal disease progression analysis.
- Develop risk-aware economic loss estimation.
- Extend support to more crop species and disease categories.
- Improve inference efficiency on low-power edge devices.
- Explore lightweight YOLO variants for mobile deployment.

---

---

## 📄 License

This project is released under the **MIT License**.

---

