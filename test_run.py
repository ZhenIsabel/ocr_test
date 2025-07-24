#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本
用于测试项目的基本功能
"""

import os
import sys
import time
from main import DocumentProcessor
from utils.helpers import setup_logger

def test_extract_from_ocr_result():
    """测试从OCR结果提取信息"""
    print("=== 测试从OCR结果提取信息 ===")
    
    # 初始化处理器
    processor = DocumentProcessor()
    
    # 加载房源数据库
    processor.load_property_database('data/sample_property_db.csv')
    
    # 使用现有的OCR结果进行测试
    if os.path.exists('ocr_result.json'):
        test_file = 'ocr_result.json'
        # 处理文件
        result = processor.process_file(test_file)
        
        if result:
            print(f"处理成功，文档ID: {result['document_id']}")
            print(f"文档类型: {result['classification']['doc_type']}")
            print(f"文档置信度: {result['classification']['confidence']}")
            print("\n关键信息:")
            for key, value in result['key_info'].items():
                print(f"  {key}: {value}")
                
            if result.get('match_result'):
                print("\n匹配结果:")
                print(f"  房源ID: {result['match_result']['property_id']}")
                print(f"  相似度: {result['match_result']['similarity']}")
            else:
                print("\n未找到匹配的房源")
        else:
            print("处理失败")
    else:
        print("找不到OCR结果文件")

def test_text_cleaner():
    """测试文本清洗"""
    print("=== 测试文本清洗 ===")
    
    # 初始化处理器
    processor = DocumentProcessor()
    # 加载OCR结果
    ocr_result=processor.ocr_engine.load_result("output/ocr_sample.json")
    print(ocr_result[0:100])
    # 提取文本
    pages_data = processor.ocr_engine.extract_text(ocr_result)
    # 处理文本
    cleaned_pages=processor.text_cleaner.process_document(pages_data)
    # 保存结果
    # 将cleaned_pages保存为文本文件
    with open("output/cleaned_pages.txt", "w", encoding="utf-8") as f:
        for i in cleaned_pages:
            f.write("tfidf关键词：")
            f.write("\n")
            f.write(str(i['keywords_tfidf']))
            f.write("\n")
            f.write("text关键词：")
            f.write("\n")
            f.write(str(i['keywords_textrank']))

    print("清洗结果已保存到 output/cleaned_pages.txt")


def run_all_tests():
    """运行所有测试"""
    test_extract_from_ocr_result()

if __name__ == "__main__":
    # 运行测试
    start_time = time.time()
    test_text_cleaner()
    end_time = time.time()
    print(f"\n所有测试完成，耗时: {end_time - start_time:.2f} 秒") 