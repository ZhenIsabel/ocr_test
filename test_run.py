#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本
用于测试项目的基本功能
"""

from operator import mod
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

def test_document_classifier():
    """测试文档分类"""
    print("=== 测试文档分类 ===")
    # 初始化处理器
    processor = DocumentProcessor()
    # 加载OCR结果
    ocr_result=processor.ocr_engine.load_result("output/ocr_quark_combine.json")
    # ocr_result=processor.ocr_engine.load_result("output/ocr_quark_seperate.json")
    # 提取文本
    pages_data = processor.ocr_engine.extract_text(ocr_result)
    # 处理文本
    cleaned_pages=processor.text_cleaner.process_document(pages_data)
    # 对所有页面分类
    classified_pages=processor.document_classifier.classify_document_pages(cleaned_pages)
    # 保存结果
    with open("output/classified_pages.txt", "w", encoding="utf-8") as f:  
        index=1 
        for i in classified_pages:
            f.write("page"+str(index)+":\n")
            f.write(str(i))
            f.write("\n")
            index+=1
    print("分类结果已保存到 output/classified_pages.txt")
    # 合并相同类别的页
    class_start_indices=[] # 用来标记每个类别的开始页
    for index in range(len(classified_pages)):
        if index==0:
            class_start_indices.append(0)
        if classified_pages[index]['doc_type']!=classified_pages[index-1]['doc_type']:
            class_start_indices.append(index)
        if index==len(classified_pages)-1:
            class_start_indices.append(index) # 结束页
    # 正确打印每个类别的起止页和类别
    for i in range(0, len(class_start_indices)-1):
        start_page = class_start_indices[i] + 1
        end_page = class_start_indices[i+1]
        doc_type = classified_pages[class_start_indices[i]]['doc_type']
        print(f"第{start_page}页到第{end_page}页是{doc_type}")


def test_matcher():
    """测试文档匹配"""
    # 设置日志
    logger = setup_logger("test", "logs/test.log")
    logger.info("初始化文档处理器...")
    # 初始化处理器
    processor = DocumentProcessor()
    # 加载OCR结果
    ocr_result=processor.ocr_engine.load_result("output/ocr_quark_combine.json")
    # 提取文本
    logger.info("提取文本...")
    pages_data = processor.ocr_engine.extract_text(ocr_result)
    # 处理文本
    logger.info("处理文本...")
    cleaned_pages=processor.text_cleaner.process_document(pages_data)
    # 6. 信息提取
    logger.info("信息提取...")
    doc_info = processor.info_extractor.extract_document_info(cleaned_pages)
    logger.info("信息提取完成")
    # 7. 文档匹配
    match_result = None
    try:
        db_path="data/sample_property_db.csv"
        logger.info(f"加载房源数据库: {db_path}")
        from core.matcher import DocumentMatcher
        processor.document_matcher = DocumentMatcher()
        processor.document_matcher.load_property_db(db_path)
    except Exception as e:
        logger.error(f"加载房源数据库失败: {str(e)}")

    if processor.document_matcher:
        match_result = processor.document_matcher.match_document(doc_info)
        if match_result.get('auto_match'):
            logger.info(f"文档匹配完成，匹配到房源: {match_result['auto_match']['property_id']}")
        else:
            logger.info("文档匹配完成，未找到匹配的房源")
    else:
        logger.warning("房源数据库未加载，跳过匹配步骤")

def run_all_tests():
    """运行所有测试"""
    test_extract_from_ocr_result()

if __name__ == "__main__":
    # 运行测试
    start_time = time.time()
    test_matcher()
    end_time = time.time()
    print(f"\n所有测试完成，耗时: {end_time - start_time:.2f} 秒") 