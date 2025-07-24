#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库存储模块
用于将处理结果存储到数据库中
"""

import os
import sys
import json
import sqlite3
import datetime
from typing import Dict, List, Any, Union, Optional
import pandas as pd

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import DB_CONFIG, STORAGE_CONFIG


class DocumentStorage:
    """文档存储类"""
    
    def __init__(self, config: Dict = None, db_config: Dict = None):
        """初始化文档存储器
        
        Args:
            config: 存储配置，默认使用全局配置
            db_config: 数据库配置，默认使用全局配置
        """
        self.config = config or STORAGE_CONFIG
        self.db_config = db_config or DB_CONFIG
        
        # 确保存储目录存在
        if 'local_storage' in self.config:
            os.makedirs(self.config['local_storage'], exist_ok=True)
        
        # 连接数据库
        self._conn = None
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库连接"""
        if self.db_config['type'] == 'sqlite':
            # 确保数据库目录存在
            db_dir = os.path.dirname(self.db_config['path'])
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                
            self._conn = sqlite3.connect(self.db_config['path'])
            self._conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
            
            # 创建必要的表
            self._create_tables()
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_config['type']}")
    
    def _create_tables(self) -> None:
        """创建数据库表"""
        cursor = self._conn.cursor()
        
        # 文档表
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.db_config['table_prefix']}documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            original_path TEXT,
            file_md5 TEXT,
            file_size INTEGER,
            page_count INTEGER,
            doc_type TEXT,
            doc_type_confidence REAL,
            import_date TEXT,
            status TEXT,
            storage_path TEXT,
            property_id TEXT,
            match_confidence REAL,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        # 文档页面表
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.db_config['table_prefix']}document_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            page_index INTEGER,
            text TEXT,
            cleaned_text TEXT,
            confidence REAL,
            page_type TEXT,
            storage_path TEXT,
            created_at TEXT,
            FOREIGN KEY (document_id) REFERENCES {self.db_config['table_prefix']}documents (id)
        )
        ''')
        
        # 文档提取的信息表
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.db_config['table_prefix']}document_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            info_type TEXT,
            info_key TEXT,
            info_value TEXT,
            confidence REAL,
            page_index INTEGER,
            created_at TEXT,
            FOREIGN KEY (document_id) REFERENCES {self.db_config['table_prefix']}documents (id)
        )
        ''')
        
        self._conn.commit()
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __del__(self) -> None:
        """析构函数，确保关闭数据库连接"""
        self.close()
    
    def save_document(self, file_info: Dict[str, Any], doc_classification: Dict[str, Any], 
                     doc_info: Dict[str, Any], match_result: Dict[str, Any], 
                     pages_data: List[Dict[str, Any]]) -> int:
        """保存文档信息到数据库
        
        Args:
            file_info: 文件基本信息
            doc_classification: 文档分类结果
            doc_info: 文档提取的信息
            match_result: 匹配结果
            pages_data: 页面数据
            
        Returns:
            int: 文档ID
        """
        # 保存文档基本信息
        doc_id = self._save_document_base(file_info, doc_classification, match_result)
        
        # 保存页面信息
        self._save_document_pages(doc_id, pages_data)
        
        # 保存提取的信息
        self._save_document_info(doc_id, doc_info)
        
        return doc_id
    
    def _save_document_base(self, file_info: Dict[str, Any], doc_classification: Dict[str, Any], 
                           match_result: Dict[str, Any]) -> int:
        """保存文档基本信息
        
        Args:
            file_info: 文件基本信息
            doc_classification: 文档分类结果
            match_result: 匹配结果
            
        Returns:
            int: 文档ID
        """
        cursor = self._conn.cursor()
        
        # 准备文档数据
        now = datetime.datetime.now().isoformat()
        
        # 获取分类信息
        doc_type = doc_classification.get('doc_type', '其他')
        doc_type_confidence = doc_classification.get('confidence', 0.0)
        
        # 获取匹配信息
        property_id = None
        match_confidence = 0.0
        if match_result and match_result.get('auto_match'):
            property_id = match_result['auto_match'].get('property_id')
            match_confidence = match_result['auto_match'].get('similarity', 0.0)
        
        # 存储本地路径
        storage_path = None
        if 'temp_path' in file_info and self.config.get('local_storage'):
            source_path = file_info['temp_path']
            if os.path.exists(source_path):
                # 构造存储路径
                file_ext = os.path.splitext(source_path)[1]
                dest_filename = f"{file_info['file_id']}{file_ext}"
                dest_path = os.path.join(self.config['local_storage'], dest_filename)
                
                # 复制文件
                try:
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    storage_path = dest_path
                except Exception as e:
                    print(f"保存文件失败: {str(e)}")
        
        # 插入文档记录
        cursor.execute(f'''
        INSERT INTO {self.db_config['table_prefix']}documents
        (file_id, file_name, original_path, file_md5, file_size, page_count,
         doc_type, doc_type_confidence, import_date, status, storage_path,
         property_id, match_confidence, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_info.get('file_id'),
            file_info.get('file_name'),
            file_info.get('original_path'),
            file_info.get('file_md5'),
            file_info.get('file_size'),
            file_info.get('page_count'),
            doc_type,
            doc_type_confidence,
            file_info.get('import_date'),
            file_info.get('status', 'imported'),
            storage_path,
            property_id,
            match_confidence,
            now,
            now
        ))
        
        self._conn.commit()
        return cursor.lastrowid
    
    def _save_document_pages(self, document_id: int, pages_data: List[Dict[str, Any]]) -> None:
        """保存文档页面信息
        
        Args:
            document_id: 文档ID
            pages_data: 页面数据
        """
        cursor = self._conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        for page in pages_data:
            page_index = page.get('page_index')
            text = page.get('text', '')
            cleaned_text = page.get('cleaned_text', '')
            confidence = page.get('confidence', 0.0)
            
            # 页面类型
            page_type = None
            for page_type_info in page.get('page_types', []):
                if page_type_info.get('page_index') == page_index:
                    page_type = page_type_info.get('doc_type')
                    break
            
            cursor.execute(f'''
            INSERT INTO {self.db_config['table_prefix']}document_pages
            (document_id, page_index, text, cleaned_text, confidence, page_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                page_index,
                text,
                cleaned_text,
                confidence,
                page_type,
                now
            ))
        
        self._conn.commit()
    
    def _save_document_info(self, document_id: int, doc_info: Dict[str, Any]) -> None:
        """保存文档提取的信息
        
        Args:
            document_id: 文档ID
            doc_info: 提取的信息
        """
        cursor = self._conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # 保存关键信息
        key_info = doc_info.get('key_info', {})
        for key, value in key_info.items():
            cursor.execute(f'''
            INSERT INTO {self.db_config['table_prefix']}document_info
            (document_id, info_type, info_key, info_value, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                'key_info',
                key,
                str(value),
                1.0,  # 关键信息置信度默认为1.0
                now
            ))
        
        # 保存页面级信息
        page_info = doc_info.get('page_info', [])
        for page in page_info:
            page_index = page.get('page_index')
            page_data = page.get('info', {})
            
            for info_type, items in page_data.items():
                for i, item in enumerate(items):
                    value = item.get('value', '')
                    confidence = item.get('confidence', 0.0) if isinstance(item, dict) and 'confidence' in item else 0.5
                    
                    cursor.execute(f'''
                    INSERT INTO {self.db_config['table_prefix']}document_info
                    (document_id, info_type, info_key, info_value, confidence, page_index, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        document_id,
                        info_type,
                        f"{info_type}_{i+1}",
                        str(value),
                        confidence,
                        page_index,
                        now
                    ))
        
        self._conn.commit()
    
    def save_json(self, data: Dict[str, Any], filename: str) -> str:
        """将数据保存为JSON文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
            
        Returns:
            str: 保存的文件路径
        """
        if 'local_storage' not in self.config:
            raise ValueError("未配置本地存储路径")
            
        file_path = os.path.join(self.config['local_storage'], filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return file_path
    
    def get_document_by_id(self, document_id: int) -> Dict[str, Any]:
        """通过ID获取文档信息
        
        Args:
            document_id: 文档ID
            
        Returns:
            Dict: 文档信息
        """
        cursor = self._conn.cursor()
        
        # 查询文档基本信息
        cursor.execute(f'''
        SELECT * FROM {self.db_config['table_prefix']}documents
        WHERE id = ?
        ''', (document_id,))
        
        doc_row = cursor.fetchone()
        if not doc_row:
            return None
            
        # 转换为字典
        doc_info = dict(doc_row)
        
        # 查询页面信息
        cursor.execute(f'''
        SELECT * FROM {self.db_config['table_prefix']}document_pages
        WHERE document_id = ?
        ORDER BY page_index
        ''', (document_id,))
        
        pages = [dict(row) for row in cursor.fetchall()]
        doc_info['pages'] = pages
        
        # 查询提取的信息
        cursor.execute(f'''
        SELECT * FROM {self.db_config['table_prefix']}document_info
        WHERE document_id = ?
        ''', (document_id,))
        
        extracted_info = [dict(row) for row in cursor.fetchall()]
        doc_info['extracted_info'] = extracted_info
        
        return doc_info
    
    def list_documents(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """列出文档
        
        Args:
            filters: 过滤条件
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 文档列表
        """
        cursor = self._conn.cursor()
        
        query = f"SELECT * FROM {self.db_config['table_prefix']}documents"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY created_at DESC LIMIT {limit}"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


# 测试代码
if __name__ == "__main__":
    storage = DocumentStorage()
    print("文档存储器初始化完成")
    
    # 创建临时目录
    os.makedirs("./data/files", exist_ok=True)
    os.makedirs("./temp", exist_ok=True)
    
    # 创建测试文件
    test_file_path = "./temp/test.txt"
    with open(test_file_path, "w") as f:
        f.write("测试文件内容")
    
    # 准备测试数据
    file_info = {
        'file_id': 'test_file_001',
        'file_name': 'test.txt',
        'original_path': os.path.abspath(test_file_path),
        'file_md5': 'abcd1234',
        'file_size': 100,
        'page_count': 1,
        'temp_path': test_file_path,
        'import_date': datetime.datetime.now().isoformat(),
        'status': 'processed'
    }
    
    doc_classification = {
        'doc_type': '房产证',
        'confidence': 0.85
    }
    
    doc_info = {
        'key_info': {
            'cert_number': '京(2023)朝阳区不动产权第0012345号',
            'address': '北京市朝阳区某某路100号'
        },
        'page_info': [
            {
                'page_index': 0,
                'info': {
                    'cert_numbers': [{'value': '京(2023)朝阳区不动产权第0012345号'}]
                }
            }
        ]
    }
    
    match_result = {
        'auto_match': {
            'property_id': 'P001',
            'similarity': 0.95
        }
    }
    
    pages_data = [
        {
            'page_index': 0,
            'text': '这是测试文本内容',
            'cleaned_text': '这是测试文本内容',
            'confidence': 0.9,
            'page_types': [{'page_index': 0, 'doc_type': '房产证'}]
        }
    ]
    
    # 测试保存文档
    try:
        doc_id = storage.save_document(file_info, doc_classification, doc_info, match_result, pages_data)
        print(f"文档保存成功，ID: {doc_id}")
        
        # 测试获取文档
        doc = storage.get_document_by_id(doc_id)
        print(f"获取到文档: {doc['file_name']}, 类型: {doc['doc_type']}")
        
        # 测试列出文档
        docs = storage.list_documents()
        print(f"文档列表: {len(docs)} 条")
        
    except Exception as e:
        print(f"测试出错: {str(e)}")
    finally:
        storage.close() 