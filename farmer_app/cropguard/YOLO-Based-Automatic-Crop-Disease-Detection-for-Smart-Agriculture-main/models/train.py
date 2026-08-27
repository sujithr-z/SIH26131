from pathlib import Path
from ultralytics import YOLO
from configs.paths import MODEL_DIR, DATASET_YAML
from configs.params import TRAIN_PARAMS
from utils.logger import setup_logger




logger = setup_logger('train')


def train_model():
    try:
        # 加载模型
        model = YOLO('yolov8s.pt')

        # 训练模型
        results = model.train(
            **TRAIN_PARAMS
        )

        # 保存最佳模型
        best_model_path = Path(MODEL_DIR) / 'best.pt'
        model.export(format='onnx')
        logger.info(f"Training completed. Model saved to {best_model_path}")

        return results

    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise