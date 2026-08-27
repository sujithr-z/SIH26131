import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import cv2
from pathlib import Path
from ultralytics import YOLO
from typing import Optional, Dict, Union


def plot_training_curves(results_csv: Path, save_path: Path) -> None:
    """
    绘制训练曲线

    参数:
        results_csv: 训练结果CSV文件路径
        save_path: 图片保存目录
    """
    results = pd.read_csv(results_csv)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 损失曲线
    axes[0, 0].plot(results['epoch'], results['train/box_loss'], label='Train')
    axes[0, 0].plot(results['epoch'], results['val/box_loss'], label='Validation')
    axes[0, 0].set_title('Box Loss')
    axes[0, 0].legend()

    # 精度曲线
    axes[0, 1].plot(results['epoch'], results['metrics/mAP50(B)'], label='mAP@0.5')
    axes[0, 1].plot(results['epoch'], results['metrics/mAP50-95(B)'], label='mAP@0.5:0.95')
    axes[0, 1].set_title('mAP Metrics')
    axes[0, 1].legend()

    # 精确率-召回率曲线
    axes[1, 0].plot(results['epoch'], results['metrics/precision(B)'], label='Precision')
    axes[1, 0].plot(results['epoch'], results['metrics/recall(B)'], label='Recall')
    axes[1, 0].set_title('Precision & Recall')
    axes[1, 0].legend()

    plt.tight_layout()
    plt.savefig(save_path / 'training_curves.png', dpi=300, bbox_inches='tight')
    plt.close()


def plot_confusion_matrix(model: YOLO, save_path: Path) -> None:
    """
    生成并保存混淆矩阵

    参数:
        model: 训练好的YOLO模型
        save_path: 图片保存目录
    """
    val_dir = Path(model.trainer.save_dir) / 'val'
    conf_mat = np.loadtxt(val_dir / 'confusion_matrix.csv', delimiter=',')

    plt.figure(figsize=(15, 15))
    sns.heatmap(conf_mat, annot=True, fmt='.2f', cmap='Blues',
                xticklabels=model.names.values(),
                yticklabels=model.names.values())
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()


def plot_severity(img: np.ndarray, detections, save_path: Optional[Path] = None) -> None:
    """
    绘制病害严重度热力图

    参数:
        img: 原始图像 (BGR格式)
        detections: 检测结果对象
        save_path: 图片保存路径(可选)
    """
    heatmap = np.zeros(img.shape[:2], dtype=np.float32)

    for box in detections.boxes:
        x, y, w, h = box.xywh[0].cpu().numpy()
        cv2.ellipse(heatmap,
                    (int(x), int(y)),
                    (int(w / 2), int(h / 2)),
                    0, 0, 360, 1, -1)

    plt.figure(figsize=(10, 6))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.imshow(heatmap, alpha=0.5, cmap='jet')
    plt.colorbar(label='Severity Level')
    plt.title('Disease Severity Heatmap')

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()


def plot_agriculture_results(metrics: Dict[str, float], save_path: Optional[Path] = None) -> None:
    """
    绘制农业指标结果

    参数:
        metrics: 包含农业指标的字典
        save_path: 图片保存路径(可选)
    """
    agri_metrics = {
        'SSER': metrics['SSER'],
        'EIS': metrics['EIS'],
        'Composite Score': metrics['Agriculture_Score']
    }

    plt.figure(figsize=(10, 6))
    bars = plt.bar(agri_metrics.keys(), agri_metrics.values(),
                   color=['#ff7f0e', '#2ca02c', '#1f77b4'])

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height:.3f}',
                 ha='center', va='bottom')

    plt.title('Agriculture-specific Metrics', fontsize=14)
    plt.ylim(0, 1.1)
    plt.ylabel('Score', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()


def plot_all_results(model: YOLO, results_csv: Path,
                     agriculture_metrics: Optional[Dict] = None,
                     sample_img: Optional[np.ndarray] = None,
                     sample_detections=None,
                     output_dir: Path = Path('results')) -> None:
    """
    一键生成所有可视化结果

    参数:
        model: 训练好的YOLO模型
        results_csv: 训练结果CSV文件路径
        agriculture_metrics: 农业指标字典(可选)
        sample_img: 示例图像(用于热力图)(可选)
        sample_detections: 示例检测结果(用于热力图)(可选)
        output_dir: 输出目录
    """
    output_dir.mkdir(exist_ok=True)

    # 绘制基础训练曲线
    plot_training_curves(results_csv, output_dir)

    # 绘制混淆矩阵
    plot_confusion_matrix(model, output_dir)

    # 如果有农业指标，绘制农业指标图表
    if agriculture_metrics:
        plot_agriculture_results(agriculture_metrics, output_dir / 'agriculture_metrics.png')

    # 如果有示例图像和检测结果，绘制热力图
    if sample_img is not None and sample_detections is not None:
        plot_severity(sample_img, sample_detections, output_dir / 'severity_heatmap.png')