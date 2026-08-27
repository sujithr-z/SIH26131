import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Optional, Union
import pandas as pd

# 经济权重配置（示例）
ECONOMIC_WEIGHTS = {
    'stem': {'Apple_scab': 1.5, 'Black_rot': 2.0},
    'leaf': {'Apple_scab': 1.0, 'Black_rot': 1.2}
}


class AgricultureMetrics:
    """农业特异性指标计算器"""

    def __init__(self, img_size: tuple = (640, 640),
                 severity_weight: float = 0.4,
                 economic_weight: float = 0.6):
        self.img_size = img_size
        self.severity_weight = severity_weight
        self.economic_weight = economic_weight

    def calculate_sser(self, true_masks: list, pred_boxes: list) -> float:
        """计算病害严重度误判率(SSER)"""
        sser = 0.0
        valid_count = 0

        for mask, box in zip(true_masks, pred_boxes):
            if mask is None:
                continue

            # 创建预测mask
            pred_mask = np.zeros(self.img_size[::-1], dtype=np.uint8)
            x, y, w, h = box.xywh[0].cpu().numpy()
            cv2.rectangle(
                pred_mask,
                (int(x - w / 2), int(y - h / 2)),
                (int(x + w / 2), int(y + h / 2)),
                1, -1
            )

            # 计算面积差异
            true_area = np.sum(mask) / mask.size
            pred_area = np.sum(pred_mask) / pred_mask.size
            sser += abs(true_area - pred_area)
            valid_count += 1

        return sser / max(1, valid_count)

    def calculate_eis(self, detections, class_names: Dict[int, str]) -> float:
        """计算经济影响分数(EIS)"""
        eis = 0.0
        center_y = self.img_size[1] / 2

        for box in detections.boxes:
            cls_id = int(box.cls)
            cls_name = class_names[cls_id]
            x, y, w, h = box.xywh[0].cpu().numpy()

            # 确定位置（茎部或叶部）
            position = 'stem' if y < center_y else 'leaf'
            weight = ECONOMIC_WEIGHTS.get(position, {}).get(cls_name, 1.0)

            # 计算归一化面积
            area = (w * h) / (self.img_size[0] * self.img_size[1])
            eis += weight * area

        return eis


def calculate_metrics(
        metrics,
        detections: Optional = None,
        dataset: Optional = None,
        img_size: tuple = (640, 640),
        agriculture_params: Optional[Dict] = None
) -> Dict[str, Union[Dict, pd.DataFrame]]:
    """
    综合指标计算函数

    参数:
        metrics: 基础检测指标对象
        detections: 检测结果对象
        dataset: 数据集对象
        img_size: 图像尺寸
        agriculture_params: 农业指标参数 {
            'enabled': bool,
            'severity_weight': float,
            'economic_weight': float
        }

    返回:
        {
            'base_metrics': dict,
            'class_metrics': pd.DataFrame,
            'agriculture_metrics': dict (如果启用)
        }
    """
    # 基础检测指标
    base_metrics = {
        'mAP@0.5': metrics.box.map50,
        'mAP@0.5:0.95': metrics.box.map,
        'Precision': metrics.box.precision.mean(),
        'Recall': metrics.box.recall.mean(),
        'F1': 2 * (metrics.box.precision.mean() * metrics.box.recall.mean()) /
              (metrics.box.precision.mean() + metrics.box.recall.mean())
    }

    # 按类别统计指标
    class_metrics = []
    for cls_id, cls_name in metrics.names.items():
        class_metrics.append({
            'Class': cls_name,
            'AP@0.5': metrics.box.ap50[cls_id],
            'AP@0.5:0.95': metrics.box.ap[cls_id],
            'Precision': metrics.box.precision[cls_id],
            'Recall': metrics.box.recall[cls_id],
            'Support': metrics.box.nt_per_class[cls_id]
        })

    result = {
        'base_metrics': base_metrics,
        'class_metrics': pd.DataFrame(class_metrics)
    }

    # 农业特异性指标
    if agriculture_params and agriculture_params.get('enabled', False):
        if detections is None or dataset is None:
            raise ValueError("农业指标计算需要提供detections和dataset参数")

        ag_metrics = AgricultureMetrics(
            img_size=img_size,
            severity_weight=agriculture_params.get('severity_weight', 0.4),
            economic_weight=agriculture_params.get('economic_weight', 0.6)
        )

        sser = ag_metrics.calculate_sser(dataset.masks, detections.boxes)
        eis = ag_metrics.calculate_eis(detections, metrics.names)

        result['agriculture_metrics'] = {
            'SSER': sser,
            'EIS': eis,
            'Agriculture_Score': (1 - sser) * ag_metrics.severity_weight +
                                 eis * ag_metrics.economic_weight
        }

    return result