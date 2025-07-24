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

def test_extract_from_ocr_result():
    """测试从OCR结果提取信息"""
    print("=== 测试从OCR结果提取信息 ===")
    
    # 初始化处理器
    processor = DocumentProcessor()
    
    # 加载房源数据库
    processor.load_property_database('data/sample_property_db.csv')
    
    # 使用现有的OCR结果进行测试
    if os.path.exists('ocr_result.json'):
        # 创建一个临时测试文件
        test_file = 'temp/test_file.txt'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试文件内容")
            
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

def run_all_tests():
    """运行所有测试"""
    test_extract_from_ocr_result()

if __name__ == "__main__":
    # 运行测试
    start_time = time.time()
    run_all_tests()
    end_time = time.time()
    print(f"\n所有测试完成，耗时: {end_time - start_time:.2f} 秒") 