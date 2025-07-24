#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件
包含系统所需的各种配置参数
"""

# OCR配置
OCR_CONFIG = {
    "client_id": "test_AJ0715",
    "client_secret": "GZAJ0715",
    "url": "https://scan-business.quark.cn/vision"
}

# 文件预处理配置
FILE_PROCESS_CONFIG = {
    "input_dir": "./input",
    "output_dir": "./output",
    "temp_dir": "./temp",
    "supported_formats": ["pdf", "jpg", "jpeg", "png"]
}

# 文本清洗配置
TEXT_CLEAN_CONFIG = {
    "min_confidence": 0.7,  # 最低置信度
    "remove_noise": True,   # 是否去除噪声
}

# 数据库配置
DB_CONFIG = {
    "type": "sqlite",  # sqlite/postgresql
    "path": "./data/documents.db",
    "table_prefix": "doc_"
}

# 匹配配置
MATCH_CONFIG = {
    "similarity_threshold": 0.8,  # 相似度阈值
    "top_n": 3,                   # 保留前N个最匹配结果
}

# 文件存储配置
STORAGE_CONFIG = {
    "use_minio": False,
    "minio_config": {
        "endpoint": "localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "bucket_name": "documents"
    },
    "local_storage": "./data/files"
}

# 分类相关配置
CLASSIFY_CONFIG = {
    "model_path": "./models/classifier.pkl",
    "vectorizer_path": "./models/vectorizer.pkl",
    "use_model": True,  # 是否使用模型分类
    "rules_path": "./config/score_rules.yml",  # 评分规则文件路径
    "samples_path": "./data/training_samples.pkl",  # 训练样本存储路径
    "sample_score_threshold": 0.8,  # 高置信度样本阈值，用于自动收集训练样本
    "model_confidence_threshold": 0.9,  # 模型高置信度阈值，用于自动收集训练样本
    "classification_strategy": "hybrid",  # 分类策略: rules_only, model_only, hybrid
    "auto_train": True,  # 是否在收集到新样本后自动训练模型
    "incremental_learning": True,  # 是否启用增量学习
    "min_samples_for_training": 10,  # 训练模型所需的最少样本数量
} 