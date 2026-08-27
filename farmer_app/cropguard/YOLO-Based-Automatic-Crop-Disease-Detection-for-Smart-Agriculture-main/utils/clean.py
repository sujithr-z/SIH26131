# utils/clean.py
import shutil
from pathlib import Path
from configs.paths import RESULTS_DIR, MODEL_DIR


def clean_training_artifacts():
    """清除所有训练生成的文件"""
    dirs_to_remove = [
        Path("runs"),  # Ultralytics默认输出目录
        Path(RESULTS_DIR),  # 你的结果目录
        Path(MODEL_DIR),  # 模型保存目录
        Path("train.log"),  # 日志文件（如果有）
        Path("val.log")
    ]

    for dir_path in dirs_to_remove:
        if dir_path.exists():
            if dir_path.is_dir():
                shutil.rmtree(dir_path)
                print(f"✅ 已删除目录: {dir_path}")
            else:
                dir_path.unlink()
                print(f"✅ 已删除文件: {dir_path}")
        else:
            print(f"⚠️ 不存在: {dir_path}")


if __name__ == "__main__":
    clean_training_artifacts()