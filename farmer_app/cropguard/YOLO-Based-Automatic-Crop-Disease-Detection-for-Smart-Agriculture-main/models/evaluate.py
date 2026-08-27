from ultralytics import YOLO
from typing import Dict, Union, Optional
import pandas as pd
import cv2
from pathlib import Path
from configs.paths import MODEL_DIR, RESULTS_DIR
from evaluation.metrics import calculate_metrics
from evaluation.visualize import (
    plot_confusion_matrix,
    plot_severity,
    plot_agriculture_results
)


def evaluate_model(
        model_path: Optional[Path] = None,
        data_loader: Optional = None,
        eval_params: Optional[Dict] = None,
        save_dir: Optional[Path] = None,
        agriculture_metrics: bool = False
) -> Dict[str, Union[pd.DataFrame, Dict]]:
    """
    综合评估模型性能，包含基础指标和农业特异性指标

    参数:
        model_path: 模型路径 (默认使用MODEL_DIR/best.pt)
        data_loader: 数据加载器 (如有则使用扩展评估)
        eval_params: 评估参数 (默认使用基础YOLO参数)
        save_dir: 结果保存目录 (默认使用RESULTS_DIR/evaluation)
        agriculture_metrics: 是否计算农业指标

    返回:
        包含所有评估结果的字典:
        - 'base_metrics': 基础指标DataFrame
        - 'class_metrics': 分类指标DataFrame
        - 'agriculture_metrics': 农业指标字典(如果启用)
    """
    # 初始化参数
    model_path = model_path or MODEL_DIR / 'best.pt'
    save_dir = save_dir or RESULTS_DIR / 'evaluation'
    save_dir.mkdir(exist_ok=True, parents=True)

    # YOLO官方支持的验证参数 (移除非标准参数)
    yolo_val_params = {
        'data': str(eval_params['data']) if eval_params else 'data.yaml',
        'batch': eval_params.get('batch_size', 8) if eval_params else 8,
        'imgsz': eval_params.get('imgsz', 640) if eval_params else 640,
        'conf': eval_params.get('conf', 0.25) if eval_params else 0.25,
        'iou': eval_params.get('iou', 0.6) if eval_params else 0.6,
        'split': 'val'  # 固定使用验证集
    }

    # 加载模型
    model = YOLO(str(model_path))  # 确保路径为字符串

    # 标准YOLO验证
    metrics = model.val(**yolo_val_params)

    # 农业参数提取 (不传递给YOLO)
    agriculture_params = {
        'enabled': agriculture_metrics,
        'severity_weight': eval_params.get('severity_weight', 0.4) if eval_params else 0.4,
        'economic_weight': eval_params.get('economic_weight', 0.6) if eval_params else 0.6
    } if agriculture_metrics else None

    # 计算扩展指标
    results = calculate_metrics(
        metrics=metrics,
        detections=None if data_loader is None else model.predict(getattr(data_loader.dataset, 'im_files', [])),
        dataset=None if data_loader is None else data_loader.dataset,
        img_size=yolo_val_params['imgsz'],
        agriculture_params=agriculture_params
    )

    # 保存结果
    results['base_metrics'].to_csv(save_dir / 'base_metrics.csv', index=False)
    results['class_metrics'].to_csv(save_dir / 'class_metrics.csv', index=False)

    # 可视化
    plot_confusion_matrix(model, save_dir)

    # 农业指标可视化
    if agriculture_metrics and 'agriculture_metrics' in results:
        plot_agriculture_results(
            results['agriculture_metrics'],
            save_path=save_dir / 'agriculture_metrics.png'
        )

        # 为样本生成热力图
        if data_loader and hasattr(data_loader.dataset, 'im_files'):
            detections = model.predict(data_loader.dataset.im_files[:3])
            for i, (img_path, det) in enumerate(zip(data_loader.dataset.im_files[:3], detections)):
                img = cv2.imread(str(img_path))
                plot_severity(
                    img, det,
                    save_path=save_dir / f'severity_{i}.png'
                )

    return results


def evaluate_from_config():
    """使用默认参数进行评估"""
    return evaluate_model()