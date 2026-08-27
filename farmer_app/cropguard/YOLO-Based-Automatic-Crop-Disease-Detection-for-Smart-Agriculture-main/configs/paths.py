import os

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# 更新为你的实际模型路径
MODEL_DIR = BASE_DIR / "plant_disease" / "exp1" / "weights"
MODEL_FILE = MODEL_DIR / "best.pt"  # 完整模型路径

# 确保目录存在
MODEL_DIR.mkdir(parents=True, exist_ok=True)

BASE_DIR = Path(__file__).parent.parent  # 替换 os.path.dirname

# 数据集路径
DATASET_DIR = BASE_DIR / 'datasets/PlantVillage_YOLO'
DATASET_YAML = DATASET_DIR / 'plantvillage.yaml'



# 结果保存路径
RESULTS_DIR = BASE_DIR / 'results'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)