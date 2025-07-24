#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件预处理模块
处理文件导入、拆分等
"""

import os
import shutil
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import FILE_PROCESS_CONFIG


class FileProcessor:
    """文件预处理类"""
    
    def __init__(self, config: Dict = None):
        """初始化文件处理器
        
        Args:
            config: 配置信息，默认使用全局配置
        """
        self.config = config or FILE_PROCESS_CONFIG
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所需的目录存在"""
        for dir_key in ['input_dir', 'output_dir', 'temp_dir']:
            if dir_key in self.config:
                os.makedirs(self.config[dir_key], exist_ok=True)
    
    def is_supported_format(self, filename: str) -> bool:
        """检查文件格式是否支持
        
        Args:
            filename: 文件名
        
        Returns:
            bool: 是否支持该格式
        """
        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        return ext in self.config['supported_formats']
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """处理单个文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            Dict: 包含文件信息的字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        if not self.is_supported_format(file_path):
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        # 生成文件的唯一ID和元数据
        file_info = self._generate_file_metadata(file_path)
        
        # 将文件复制到临时目录
        temp_file_path = os.path.join(
            self.config['temp_dir'], 
            f"{file_info['file_id']}{os.path.splitext(file_path)[1]}"
        )
        shutil.copy2(file_path, temp_file_path)
        file_info['temp_path'] = temp_file_path
        
        return file_info
    
    def _generate_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """生成文件元数据
        
        Args:
            file_path: 文件路径
        
        Returns:
            Dict: 包含文件元数据的字典
        """
        # 计算文件MD5
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        file_md5 = md5_hash.hexdigest()
        
        # 生成唯一ID
        file_id = str(uuid.uuid4())
        
        # 获取文件信息
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        file_modified = datetime.fromtimestamp(file_stat.st_mtime)
        
        return {
            'file_id': file_id,
            'original_path': os.path.abspath(file_path),
            'file_name': os.path.basename(file_path),
            'file_ext': os.path.splitext(file_path)[1].lower().replace('.', ''),
            'file_size': file_size,
            'file_md5': file_md5,
            'modified_date': file_modified.isoformat(),
            'import_date': datetime.now().isoformat(),
            'page_count': None,  # 后续处理时更新
            'status': 'imported'
        }

    def batch_import(self, directory: str = None) -> List[Dict[str, Any]]:
        """批量导入目录中的文件
        
        Args:
            directory: 目录路径，默认使用配置中的input_dir
        
        Returns:
            List[Dict]: 包含所有处理文件信息的列表
        """
        directory = directory or self.config['input_dir']
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"目录不存在: {directory}")
        
        result = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and self.is_supported_format(filename):
                try:
                    file_info = self.process_file(file_path)
                    result.append(file_info)
                except Exception as e:
                    print(f"处理文件 {filename} 时出错: {str(e)}")
        
        return result


# 测试代码
if __name__ == "__main__":
    processor = FileProcessor()
    print("文件处理器初始化完成，配置信息:", processor.config) 