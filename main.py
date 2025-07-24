#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主程序入口
整合所有模块，提供完整的文档处理流程
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, List, Any, Optional
import pandas as pd

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import FILE_PROCESS_CONFIG
from core.file_processor import FileProcessor
from core.ocr_engine import OCREngine
from core.text_cleaner import TextCleaner
from core.document_classifier import DocumentClassifier
from core.info_extractor import InfoExtractor
from core.matcher import DocumentMatcher
from db.storage import DocumentStorage
from utils.helpers import setup_logger, timer, ensure_dir


class DocumentProcessor:
    """文档处理器类"""
    
    def __init__(self):
        """初始化文档处理器"""
        # 设置日志
        self.logger = setup_logger("doc_processor", "logs/process.log")
        self.logger.info("初始化文档处理器...")
        
        # 创建必要的目录
        ensure_dir("input")
        ensure_dir("output")
        ensure_dir("temp")
        ensure_dir("data/files")
        ensure_dir("logs")
        
        # 初始化各模块
        self.file_processor = FileProcessor()
        self.ocr_engine = OCREngine()
        self.text_cleaner = TextCleaner()
        self.document_classifier = DocumentClassifier()
        self.info_extractor = InfoExtractor()
        self.document_matcher = None  # 延迟加载，需要先加载房源数据
        self.storage = DocumentStorage()
        
        self.logger.info("文档处理器初始化完成")
    
    def load_property_database(self, db_path: str) -> bool:
        """加载房源数据库
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self.logger.info(f"加载房源数据库: {db_path}")
            self.document_matcher = DocumentMatcher()
            self.document_matcher.load_property_db(db_path)
            return True
        except Exception as e:
            self.logger.error(f"加载房源数据库失败: {str(e)}")
            return False
    
    @timer
    def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 处理结果
        """
        try:
            self.logger.info(f"开始处理文件: {file_path}")
            
            # 1. 文件预处理
            file_info = self.file_processor.process_file(file_path)
            self.logger.info(f"文件预处理完成: {file_info['file_id']}")
            
            # 2. OCR识别（测试中使用已有结果）
            ocr_result = self.ocr_engine.load_result("ocr_result.json")
            self.logger.info("OCR识别完成")
            
            # 3. 提取文本
            pages_data = self.ocr_engine.extract_text(ocr_result)
            file_info['page_count'] = len(pages_data)
            self.logger.info(f"文本提取完成，共 {file_info['page_count']} 页")
            
            # 4. 文本清洗
            cleaned_pages = self.text_cleaner.process_document(pages_data)
            self.logger.info("文本清洗完成")
            
            # 5. 文档分类
            doc_classification = self.document_classifier.classify_document_pages(cleaned_pages)
            self.logger.info(f"文档分类完成，类型: {doc_classification['doc_type']}")
            
            # 6. 信息提取
            doc_info = self.info_extractor.extract_document_info(cleaned_pages)
            self.logger.info("信息提取完成")
            
            # 7. 文档匹配
            match_result = None
            if self.document_matcher:
                match_result = self.document_matcher.match_document(doc_info)
                if match_result.get('auto_match'):
                    self.logger.info(f"文档匹配完成，匹配到房源: {match_result['auto_match']['property_id']}")
                else:
                    self.logger.info("文档匹配完成，未找到匹配的房源")
            else:
                self.logger.warning("房源数据库未加载，跳过匹配步骤")
            
            # 8. 存储处理结果
            doc_id = self.storage.save_document(
                file_info, doc_classification, doc_info, match_result, cleaned_pages)
            self.logger.info(f"处理结果已保存，文档ID: {doc_id}")
            
            # 返回处理结果
            return {
                'document_id': doc_id,
                'file_info': file_info,
                'classification': doc_classification,
                'key_info': doc_info['key_info'],
                'match_result': match_result['auto_match'] if match_result and match_result.get('auto_match') else None
            }
            
        except Exception as e:
            self.logger.error(f"处理文件时出错: {str(e)}", exc_info=True)
            return None
    
    @timer
    def batch_process(self, directory: str = None) -> List[Dict[str, Any]]:
        """批量处理目录中的文件
        
        Args:
            directory: 目录路径，默认使用配置中的input_dir
            
        Returns:
            List[Dict[str, Any]]: 处理结果列表
        """
        directory = directory or FILE_PROCESS_CONFIG['input_dir']
        self.logger.info(f"开始批量处理目录: {directory}")
        
        # 获取文件列表
        file_list = self.file_processor.batch_import(directory)
        self.logger.info(f"找到 {len(file_list)} 个文件")
        
        results = []
        for file_info in file_list:
            result = self.process_file(file_info['original_path'])
            if result:
                results.append(result)
        
        self.logger.info(f"批量处理完成，成功处理 {len(results)} 个文件")
        return results


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='文档处理工具')
    parser.add_argument('-f', '--file', help='要处理的文件路径')
    parser.add_argument('-d', '--dir', help='要处理的目录路径')
    parser.add_argument('-p', '--property-db', help='房源数据库路径')
    args = parser.parse_args()
    
    # 初始化处理器
    processor = DocumentProcessor()
    
    # 加载房源数据库
    if args.property_db:
        processor.load_property_database(args.property_db)
    
    # 处理文件或目录
    if args.file:
        result = processor.process_file(args.file)
        if result:
            print(f"文件处理成功，文档ID: {result['document_id']}")
            print(f"文档类型: {result['classification']['doc_type']}")
            print(f"关键信息: {result['key_info']}")
            if result.get('match_result'):
                print(f"匹配到房源: {result['match_result']['property_id']}")
        else:
            print("文件处理失败")
    
    elif args.dir:
        results = processor.batch_process(args.dir)
        print(f"批量处理完成，共处理 {len(results)} 个文件")
    
    else:
        print("请指定要处理的文件(-f)或目录(-d)")


if __name__ == "__main__":
    main() 