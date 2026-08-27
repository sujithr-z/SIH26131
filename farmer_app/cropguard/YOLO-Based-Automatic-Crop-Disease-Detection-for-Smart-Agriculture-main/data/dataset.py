import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from configs.paths import DATASET_DIR


class PlantVillageDataset:
    def __init__(self, split='train'):
        self.split = split
        self.image_dir = Path(DATASET_DIR) / 'images' / split
        self.label_dir = Path(DATASET_DIR) / 'labels' / split
        self.image_files = list(self.image_dir.glob('*.jpg'))

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_path = self.image_files[idx]
        label_path = self.label_dir / f"{img_path.stem}.txt"

        # 加载图像
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 加载标签
        labels = []
        if label_path.exists():
            with open(label_path, 'r') as f:
                for line in f.readlines():
                    cls_id, x, y, w, h = map(float, line.strip().split())
                    labels.append([cls_id, x, y, w, h])

        return image, labels

    def visualize_sample(self, idx):
        image, labels = self.__getitem__(idx)
        h, w = image.shape[:2]

        for label in labels:
            cls_id, x, y, width, height = label
            x1 = int((x - width / 2) * w)
            y1 = int((y - height / 2) * h)
            x2 = int((x + width / 2) * w)
            y2 = int((y + height / 2) * h)

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return Image.fromarray(image)