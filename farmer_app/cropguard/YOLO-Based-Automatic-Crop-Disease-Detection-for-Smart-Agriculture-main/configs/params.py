# 训练参数
TRAIN_PARAMS = {
    'data': 'plantvillage.yaml',
    'epochs': 10,
    'batch': 8,
    'imgsz': 416,
    'device': '0',
    'workers': 4,
    'optimizer': 'SGD',
    'lr0': 0.01,
    'lrf': 0.01,
    'weight_decay': 0.0005,
    'project': 'plant_disease',
    'name': 'exp1',
    'exist_ok': True
}

# 评估参数
EVAL_PARAMS = {
    'batch': 4,
    'conf': 0.25,
    'iou': 0.6,
    'split': 'test',
    'agriculture_metrics': True,  # 启用农业指标
    'severity_weight': 0.4,      # 严重度权重(0-1之间)
    'economic_weight': 0.6,      # 经济影响权重(0-1之间，需满足severity + economic = 1)
    'save_heatmaps': True        # 是否保存病害区域热力图
}