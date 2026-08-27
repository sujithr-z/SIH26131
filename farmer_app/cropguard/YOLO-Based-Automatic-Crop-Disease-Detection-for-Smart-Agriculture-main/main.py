import argparse
import sys
from pathlib import Path
from typing import Optional, Dict

# 将项目根目录添加到Python路径
sys.path.append(str(Path(__file__).parent))

from models.train import train_model
from models.evaluate import evaluate_model
from models.compare import compare_models
from utils.logger import setup_logger
from configs.paths import MODEL_DIR, RESULTS_DIR
from configs.paths import MODEL_FILE  # 导入预定义的模型文件路径

logger = setup_logger('main')


def parse_eval_args(subparsers):
    """评估子命令参数解析"""
    eval_parser = subparsers.add_parser('eval', help='Evaluate the model')
    eval_parser.add_argument('--model-path',
                             type=Path,
                             default=MODEL_FILE,  # 使用预定义的默认模型路径
                             help='Path to model weights')
    eval_parser.add_argument('--data',
                             type=str,
                             required=True,
                             help='Dataset configuration file')
    eval_parser.add_argument('--batch-size',
                             type=int,
                             default=8,
                             help='Batch size for evaluation')
    eval_parser.add_argument('--imgsz',
                             type=int,
                             default=640,
                             help='Image size for inference')
    eval_parser.add_argument('--agriculture-metrics',
                             action='store_true',
                             help='Enable agriculture-specific metrics')
    eval_parser.add_argument('--severity-weight',
                             type=float,
                             default=0.4,
                             help='Weight for disease severity (0-1)')
    eval_parser.add_argument('--economic-weight',
                             type=float,
                             default=0.6,
                             help='Weight for economic impact (0-1)')
    eval_parser.add_argument('--save-dir',
                             type=Path,
                             default=RESULTS_DIR / 'evaluation',
                             help='Directory to save results')
    return eval_parser


def main():
    parser = argparse.ArgumentParser(description='Plant Disease Detection with YOLOv8')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 训练命令
    train_parser = subparsers.add_parser('train', help='Train the model')
    train_parser.add_argument('--cfg',
                              type=str,
                              default='configs/yolov8s.yaml',
                              help='Model configuration file')
    train_parser.add_argument('--data',
                              type=str,
                              required=True,
                              help='Dataset configuration file')
    train_parser.add_argument('--epochs',
                              type=int,
                              default=100,
                              help='Number of training epochs')

    # 评估命令
    eval_parser = parse_eval_args(subparsers)

    # 比较命令
    compare_parser = subparsers.add_parser('compare', help='Compare with YOLOv5')
    compare_parser.add_argument('--yolov5-model',
                                type=Path,
                                required=True,
                                help='Path to YOLOv5 model')
    compare_parser.add_argument('--dataset',
                                type=Path,
                                required=True,
                                help='Path to evaluation dataset')

    args = parser.parse_args()

    if args.command == 'train':
        logger.info("Starting model training...")
        train_model(args.cfg, args.data, args.epochs)

    elif args.command == 'eval':
        logger.info("Evaluating model...")

        # YOLO官方支持的验证参数
        yolo_val_params = {
            'data': args.data,
            'batch': args.batch_size,
            'imgsz': args.imgsz,
            'conf': 0.25,  # 默认值
            'iou': 0.6,  # 默认值
            'split': 'test'
        }

        # 农业参数（不传递给YOLO，仅用于后处理）
        agriculture_params = {
            'severity_weight': args.severity_weight,
            'economic_weight': args.economic_weight
        } if args.agriculture_metrics else None

        evaluate_model(
            model_path=args.model_path,
            eval_params=yolo_val_params,
            save_dir=args.save_dir,
            agriculture_metrics=args.agriculture_metrics,
            agriculture_params=agriculture_params  # 新增参数
        )

    elif args.command == 'compare':
        logger.info("Comparing models...")
        compare_models(args.yolov5_model, args.dataset)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()