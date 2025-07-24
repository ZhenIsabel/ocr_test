#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块
提供各种辅助功能
"""

import os
import sys
import re
import json
import time
import uuid
import logging
import hashlib
from typing import Dict, List, Any, Union, Optional
from datetime import datetime

# 配置日志
def setup_logger(name: str, log_file: str = None, level=logging.INFO) -> logging.Logger:
    """设置日志器
    
    Args:
        name: 日志器名称
        log_file: 日志文件路径
        level: 日志级别
        
    Returns:
        logging.Logger: 日志器实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 创建唯一ID
def generate_uuid() -> str:
    """生成UUID
    
    Returns:
        str: UUID字符串
    """
    return str(uuid.uuid4())

# 计算文件MD5
def calculate_file_md5(file_path: str) -> str:
    """计算文件MD5值
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: MD5哈希值
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
        
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()

# 计时器装饰器
def timer(func):
    """计时器装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数 {func.__name__} 执行时间: {end_time - start_time:.4f} 秒")
        return result
    return wrapper

# JSON工具
def save_json(data: Dict[str, Any], file_path: str) -> None:
    """保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
    """
    # 确保目录存在
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(file_path: str) -> Dict[str, Any]:
    """从JSON文件加载数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict: 加载的数据
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 格式化工具
def format_date(date_str: str, input_format: str = "%Y年%m月%d日", output_format: str = "%Y-%m-%d") -> str:
    """格式化日期字符串
    
    Args:
        date_str: 日期字符串
        input_format: 输入格式
        output_format: 输出格式
        
    Returns:
        str: 格式化后的日期字符串
    """
    try:
        dt = datetime.strptime(date_str, input_format)
        return dt.strftime(output_format)
    except ValueError:
        return date_str

def format_money(amount: Union[str, float, int]) -> str:
    """格式化金额
    
    Args:
        amount: 金额
        
    Returns:
        str: 格式化后的金额字符串
    """
    if isinstance(amount, str):
        # 移除非数字字符
        amount = re.sub(r'[^\d.]', '', amount)
        try:
            amount = float(amount)
        except ValueError:
            return amount
    
    return f"{amount:,.2f}"

# 文件操作工具
def ensure_dir(directory: str) -> None:
    """确保目录存在
    
    Args:
        directory: 目录路径
    """
    os.makedirs(directory, exist_ok=True)

def list_files(directory: str, extensions: List[str] = None) -> List[str]:
    """列出目录中的文件
    
    Args:
        directory: 目录路径
        extensions: 文件扩展名列表
        
    Returns:
        List[str]: 文件路径列表
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"目录不存在: {directory}")
    
    files = []
    for entry in os.scandir(directory):
        if entry.is_file():
            if extensions is None or any(entry.name.lower().endswith(ext.lower()) for ext in extensions):
                files.append(entry.path)
    
    return files

# 其他工具
def clean_filename(filename: str) -> str:
    """清理文件名，移除不合法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除不合法字符
    invalid_chars = r'[\/:*?"<>|]'
    return re.sub(invalid_chars, '_', filename)


# 测试代码
if __name__ == "__main__":
    # 测试日志
    logger = setup_logger("test_logger", "logs/test.log")
    logger.info("这是一条测试日志信息")
    
    # 测试UUID生成
    print(f"生成UUID: {generate_uuid()}")
    
    # 测试计时器
    @timer
    def slow_function():
        time.sleep(1)
        return "完成"
    
    print(slow_function())
    
    # 测试JSON工具
    test_data = {"name": "测试", "value": 123}
    save_json(test_data, "temp/test.json")
    loaded_data = load_json("temp/test.json")
    print(f"加载的数据: {loaded_data}")
    
    # 测试格式化工具
    print(f"格式化日期: {format_date('2023年07月15日')}")
    print(f"格式化金额: {format_money(1234567.89)}")
    
    # 测试文件操作
    ensure_dir("temp/test_dir")
    print(f"目录已创建: temp/test_dir") 