import torch
import pandas as pd
import matplotlib.pyplot as plt
from ultralytics import YOLO
from configs.paths import MODEL_DIR, RESULTS_DIR
from utils.logger import setup_logger
from pathlib import Path

logger = setup_logger('compare')


def compare_models():
    """比较YOLOv5和YOLOv8性能"""
    try:
        # 加载YOLOv8模型
        yolov8 = YOLO('plant_disease/exp1/weights/best.pt')

        # 评估YOLOv8
        yolov8_metrics = yolov8.val(
            data='plantvillage.yaml',
            split='test',
            batch=16,
            imgsz=640
        )

        # 加载YOLOv5模型
        yolov5 = torch.hub.load('ultralytics/yolov5', 'yolov5s')
        yolov5.classes = yolov8.model.names  # 使用相同的类别

        # 评估YOLOv5
        yolov5_metrics = yolov5.val(
            data='plantvillage.yaml',
            batch=16,
            imgsz=640
        )

        # 创建比较表格
        comparison = pd.DataFrame({
            'Model': ['YOLOv5s', 'YOLOv8s'],
            'mAP@0.5': [yolov5_metrics.map50, yolov8_metrics.box.map50],
            'mAP@0.5:0.95': [yolov5_metrics.map, yolov8_metrics.box.map],
            'Precision': [yolov5_metrics.precision.mean(), yolov8_metrics.box.precision.mean()],
            'Recall': [yolov5_metrics.recall.mean(), yolov8_metrics.box.recall.mean()],
            'Params (M)': [7.2, 11.2]  # 参数量
        })

        # 保存结果
        results_path = Path(RESULTS_DIR) / 'comparison'
        results_path.mkdir(exist_ok=True)
        comparison.to_csv(results_path / 'model_comparison.csv', index=False)

        # 绘制比较图
        plt.figure(figsize=(12, 6))
        comparison.set_index('Model').plot(kind='bar', rot=0)
        plt.title('Model Comparison')
        plt.ylabel('Score')
        plt.tight_layout()
        plt.savefig(results_path / 'comparison.png')
        plt.close()

        logger.info("Model comparison completed successfully")
        return comparison

    except Exception as e:
        logger.error(f"Model comparison failed: {str(e)}")
        raise