import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path

# 经济影响权重配置（示例值，需根据实际调整）
ECONOMIC_WEIGHTS = {
    'stem': {
        'Apple___Apple_scab': 1.8,
        'Apple___Black_rot': 2.2,
        # 其他茎部病害...
    },
    'leaf': {
        'Apple___Apple_scab': 1.2,
        'Apple___Black_rot': 1.5,
        # 其他叶部病害...
    }
}


def calculate_sser(true_masks, pred_boxes, img_size):
    """病害严重度误判率计算"""
    total_error = 0
    for true_mask, pred_box in zip(true_masks, pred_boxes):
        pred_mask = np.zeros(img_size[::-1], dtype=np.uint8)
        x, y, w, h = pred_box
        cv2.rectangle(pred_mask,
                      (int(x - w / 2), int(y - h / 2)),
                      (int(x + w / 2), int(y + h / 2))),
        1, -1)
        true_area = np.sum(true_mask) / true_mask.size
        pred_area = np.sum(pred_mask) / pred_mask.size
        total_error += abs(true_area - pred_area)


return total_error / max(1, len(true_masks))


def calculate_eis(detections, img_size, names):
    """经济影响分数计算"""
    total_score = 0
    center_y = img_size[1] / 2

    for box in detections:
        cls_id = int(box.cls)
        cls_name = names[cls_id]
        x, y, w, h = box.xywh[0].tolist()

        position = 'stem' if y < center_y else 'leaf'
        weight = ECONOMIC_WEIGHTS.get(position, {}).get(cls_name, 1.0)
        area = (w * h) / (img_size[0] * img_size[1])
        total_score += weight * area

    return total_score


def plot_severity(img, detections, save_path):
    """生成病害严重度热力图"""
    heatmap = np.zeros(img.shape[:2], dtype=np.float32)
    for box in detections:
        x, y, w, h = box.xywh[0].tolist()
        cv2.ellipse(heatmap,
                    (int(x), int(y)),
                    (int(w / 2), int(h / 2)),
                    0, 0, 360, 1, -1)

    plt.figure(figsize=(10, 6))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.imshow(heatmap, alpha=0.5, cmap='jet')
    plt.colorbar(label='Severity Level')
    plt.savefig(save_path)
    plt.close()