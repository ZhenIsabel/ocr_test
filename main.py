#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主程序入口
整合所有模块，提供完整的文档处理流程
"""

import os
import sys
import argparse
from typing import Dict, List, Any, Optional
# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import FILE_PROCESS_CONFIG, CLASSIFY_CONFIG
from core.file_processor import FileProcessor
from core.ocr_engine import OCREngine
from core.text_cleaner import TextCleaner
from core.document_classifier import DocumentClassifier
from core.info_extractor import InfoExtractor
from core.matcher import DocumentMatcher
from db.storage import DocumentStorage
from utils.helpers import setup_logger, timer, ensure_dir,generate_uuid


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
        ensure_dir("models")
        
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
    
    def train_classifier_model(self, force: bool = False, incremental: bool = True) -> bool:
        """训练分类器模型
        
        Args:
            force: 是否强制训练，即使样本数量不足
            incremental: 是否进行增量学习
            
        Returns:
            bool: 是否训练成功
        """
        try:
            samples = self.document_classifier.samples
            min_samples = CLASSIFY_CONFIG.get('min_samples_for_training', 10)
            
            if len(samples['texts']) < min_samples and not force:
                self.logger.warning(f"训练样本不足，当前{len(samples['texts'])}个，需要至少{min_samples}个")
                return False
                
            self.logger.info(f"开始{'增量' if incremental else '重新'}训练分类器模型，使用{len(samples['texts'])}个样本")
            success = self.document_classifier.train_model(incremental=incremental)
            
            if success:
                self.logger.info("分类器模型训练成功")
                return True
            else:
                self.logger.error("分类器模型训练失败")
                return False
                
        except Exception as e:
            self.logger.error(f"训练分类器模型时出错: {str(e)}")
            return False
    
    def verify_document_type(self, document_id: str, correct_type: str) -> bool:
        """验证并更正文档类型
        
        Args:
            document_id: 文档ID
            correct_type: 正确的文档类型
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 从存储中获取文档信息
            doc_data = self.storage.get_document(document_id)
            if not doc_data:
                self.logger.error(f"找不到文档: {document_id}")
                return False
            
            # 获取原始文本
            doc_text = " ".join([page.get('cleaned_text', '') for page in doc_data.get('pages_data', [])])
            
            # 重新分类并标记为已验证
            classification = self.document_classifier.classify(
                doc_text, is_verified=True, verified_type=correct_type)
            
            # 更新存储中的分类信息
            self.storage.update_document_classification(document_id, classification)
            self.logger.info(f"文档 {document_id} 类型已更新为: {correct_type}")
            
            # 检查是否需要自动训练模型
            if CLASSIFY_CONFIG.get('auto_train', False):
                sample_count = len(self.document_classifier.samples['texts'])
                min_samples = CLASSIFY_CONFIG.get('min_samples_for_training', 10)
                
                if sample_count >= min_samples:
                    self.logger.info(f"样本数量达到{sample_count}个，开始自动增量训练模型")
                    incremental = CLASSIFY_CONFIG.get('incremental_learning', True)
                    self.train_classifier_model(incremental=incremental)
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证文档类型时出错: {str(e)}")
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
            
            # # 1. 文件预处理
            # 此处为测试数据
            file_info={
            'file_id': 'test',
            'original_path': os.path.abspath(file_path),
            'file_name': os.path.basename(file_path),
            'file_ext': 'test',
            'file_size': 10,
            'file_md5': 'test',
            'modified_date': 'test',
            'import_date': 'test',
            'page_count': None,  # 后续处理时更新
            'status': 'imported'
        }
            # file_info = self.file_processor.process_file(file_path)
            # self.logger.info(f"文件预处理完成: {file_info['file_id']}")
            
            # 2. OCR识别（测试中使用已有结果）
            ocr_result = self.ocr_engine.load_result("/output/ocr_sample.json")
            # 从url中ocr到结果
            # try:
            #     url = "https://download-obs.cowcs.com/cowtransfer/cowtransfer/30466/f40caa628f80449594f908359d8c3675.pdf?auth_key=1752598135-4aa6ea237c5e452c9dc7a49bbb239a3b-0-999806cab939303390cf2e9dc67cabd0&biz_type=1&business_code=COW_TRANSFER&channel_code=COW_CN_WEB&response-content-disposition=attachment%3B%20filename%3D%25E3%2580%25902.%25E5%2590%2588%25E5%2590%258C%25E3%2580%2591%25E6%2588%25BF%25E5%25B1%258B%25E6%259F%25A5%25E9%25AA%258C%25E7%25AE%25A1%25E7%2590%2586%25E7%25B3%25BB%25E7%25BB%259F%25EF%25BC%2588%25E4%25B8%2580%25E6%259C%259F%25EF%25BC%2589%25E5%25BC%2580%25E5%258F%2591%25E6%259C%258D%25E5%258A%25A1%25E9%2587%2587%25E8%25B4%25AD%25E9%25A1%25B9%25E7%259B%25AE%25E5%2590%2588%25E5%2590%258C.pdf%3Bfilename*%3Dutf-8%27%27%25E3%2580%25902.%25E5%2590%2588%25E5%2590%258C%25E3%2580%2591%25E6%2588%25BF%25E5%25B1%258B%25E6%259F%25A5%25E9%25AA%258C%25E7%25AE%25A1%25E7%2590%2586%25E7%25B3%25BB%25E7%25BB%259F%25EF%25BC%2588%25E4%25B8%2580%25E6%259C%259F%25EF%25BC%2589%25E5%25BC%2580%25E5%258F%2591%25E6%259C%258D%25E5%258A%25A1%25E9%2587%2587%25E8%25B4%25AD%25E9%25A1%25B9%25E7%259B%25AE%25E5%2590%2588%25E5%2590%258C.pdf&user_id=1033100132874430466&x-verify=1"
            #     result = self.ocr_engine.recognize_from_url(url, "pdf")
            #     # 构造一个随机文件名
            #     random_filename = f"ocr_result_{generate_uuid()}.json"
            #     output_path = f"./output/{random_filename}"
            #     ocr_engine.save_result(result, output_path)
            #     print(f"OCR结果已保存到: {output_path}")
            # except Exception as e:
            #     print(f"测试OCR文件时出错: {str(e)}") 
            self.logger.info("OCR识别完成")
            
            # 3. 提取文本
            pages_data = self.ocr_engine.extract_text(ocr_result)
            # file_info['page_count'] = len(pages_data)
            # self.logger.info(f"文本提取完成，共 {file_info['page_count']} 页")
            
            # 4. 文本清洗
            cleaned_pages = self.text_cleaner.process_document(pages_data)
            self.logger.info("文本清洗完成")
            
            # 5. 文档分类
            doc_classification = self.document_classifier.classify_document_pages(cleaned_pages)
            self.logger.info(f"文档分类完成，类型: {doc_classification['doc_type']}, 方法: {doc_classification.get('method', '未知')}")
            
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
    
    # 新增的分类器相关参数
    parser.add_argument('--train', action='store_true', help='训练分类器模型')
    parser.add_argument('--force-train', action='store_true', help='强制训练分类器模型，即使样本不足')
    parser.add_argument('--verify', help='验证并更正文档类型，格式: <document_id>:<correct_type>')
    parser.add_argument('--incremental-train', action='store_true', help='增量训练分类器模型')
    
    args = parser.parse_args()
    
    # 初始化处理器
    processor = DocumentProcessor()
    
    # 加载房源数据库
    if args.property_db:
        processor.load_property_database(args.property_db)
    
    # 处理训练分类器
    if args.train or args.force_train:
        success = processor.train_classifier_model(force=args.force_train, incremental=args.incremental_train)
        if success:
            print("分类器模型训练成功")
        else:
            print("分类器模型训练失败")
        return
    
    # 验证文档类型
    if args.verify:
        try:
            doc_id, correct_type = args.verify.split(':')
            success = processor.verify_document_type(doc_id, correct_type)
            if success:
                print(f"文档 {doc_id} 类型已更新为: {correct_type}")
            else:
                print(f"更新文档 {doc_id} 类型失败")
            return
        except ValueError:
            print("验证参数格式错误，应为: <document_id>:<correct_type>")
            return
    
    # 处理文件或目录
    if args.file:
        result = processor.process_file(args.file)
        if result:
            print(f"文件处理成功，文档ID: {result['document_id']}")
            print(f"文档类型: {result['classification']['doc_type']}")
            print(f"分类方法: {result['classification'].get('method', '未知')}")
            print(f"分类置信度: {result['classification'].get('confidence', 0)}")
            print(f"关键信息: {result['key_info']}")
            if result.get('match_result'):
                print(f"匹配到房源: {result['match_result']['property_id']}")
        else:
            print("文件处理失败")
    
    elif args.dir:
        results = processor.batch_process(args.dir)
        print(f"批量处理完成，共处理 {len(results)} 个文件")
    
    else:
        print("请指定要处理的文件(-f)或目录(-d)，或者使用 --train 训练模型")


if __name__ == "__main__":
    main() 