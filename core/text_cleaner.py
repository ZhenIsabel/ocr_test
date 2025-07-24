#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文本清洗模块
处理OCR结果中的文本，合并换行、去除噪声等
"""

import re
import os
import sys
from typing import Dict, List, Any, Tuple, Optional
import jieba
import jieba.analyse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import TEXT_CLEAN_CONFIG
from config.patterns import DATE_PATTERN, ID_NUMBER_PATTERN, MONEY_PATTERN
from utils.helpers import setup_logger


class TextCleaner:
    """文本清洗类"""
    
    def __init__(self, config: Dict = None):
        """初始化文本清洗器
        
        Args:
            config: 配置信息，默认使用全局配置
        """
        self.logger = setup_logger("text_cleaner", "logs/text_cleaner.log")
        self.config = config or TEXT_CLEAN_CONFIG
        # 加载停用词
        self.stopwords = self._load_stopwords()
        
    def _load_stopwords(self) -> set:
        """加载停用词
        
        Returns:
            set: 停用词集合
        """
        # 这里可以从文件加载停用词，暂时使用一个简单的内置列表
        common_stopwords = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', 
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', 
            '自己', '这'
        }
        return common_stopwords
    
    def clean_text(self, text: str) -> str:
        """清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            self.logger.info("clean_text: 清洗前文本为空")
            return ""
            
        # 1. 去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        self.logger.info("去除多余空格：", text)
        
        # 2. 合并断行
        text = self.merge_broken_lines(text)
        
        # 3. 去除特殊字符（保留中文、英文、数字、基本标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\.\,\，\。\!\?\-\:\：\%\;\(\)\（\）\《\》\【\】]', ' ', text)
        
        # 4. 再次去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def merge_broken_lines(self, text: str) -> str:
        """合并断行
        
        Args:
            text: 原始文本
            
        Returns:
            str: 合并断行后的文本
        """
        # 将换行符替换为空格，但保留段落换行（连续两个或以上的换行）
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 将多个连续换行符替换为两个换行符
        text = re.sub(r'\n{2,}', '\n\n', text)
        
        return text
    
    def extract_dates(self, text: str) -> List[str]:
        """提取日期
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 日期列表
        """
        return DATE_PATTERN.findall(text)
    
    def extract_id_numbers(self, text: str) -> List[str]:
        """提取身份证号码
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 身份证号码列表
        """
        matches = ID_NUMBER_PATTERN.findall(text)
        return [match[0] for match in matches if match]
    
    def extract_money(self, text: str) -> List[Tuple[str, str]]:
        """提取金额
        
        Args:
            text: 文本
            
        Returns:
            List[Tuple[str, str]]: 金额列表，每项为(数值, 单位)的元组
        """
        matches = MONEY_PATTERN.findall(text)
        return [(match[2], match[4] + '元' if match[4] else '元') for match in matches if match]
    
    def extract_keywords(self, text: str, topK: int = 20, method: str = 'tfidf') -> List[Tuple[str, float]]:
        """提取关键词
        
        Args:
            text: 文本
            topK: 提取关键词数量
            method: 提取方法，'tfidf'或'textrank'
            
        Returns:
            List[Tuple[str, float]]: 关键词列表，每项为(词, 权重)的元组
        """
        if not text:
            return []
            
        if method == 'tfidf':
            return jieba.analyse.extract_tags(text, topK=topK, withWeight=True)
        elif method == 'textrank':
            return jieba.analyse.textrank(text, topK=topK, withWeight=True)
        else:
            raise ValueError(f"不支持的关键词提取方法: {method}")
    
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单页文本
        
        Args:
            page_data: 页面数据
            
        Returns:
            Dict[str, Any]: 处理后的页面数据
        """
        text = page_data.get('text', '')
        self.logger.info(f"处理页面文本: {text[:100]}")
        
        # 文本清洗
        cleaned_text = self.clean_text(text)
        
        # 提取日期、身份证号、金额
        dates = self.extract_dates(cleaned_text)
        id_numbers = self.extract_id_numbers(cleaned_text)
        money_items = self.extract_money(cleaned_text)
        
        # 提取关键词
        keywords_tfidf = self.extract_keywords(cleaned_text, method='tfidf')
        print(f"tfidf关键词: {keywords_tfidf}")
        keywords_textrank = self.extract_keywords(cleaned_text, method='textrank')
        print(f"textrank关键词: {keywords_textrank}")

        # 更新并返回结果
        result = page_data.copy()
        result.update({
            'cleaned_text': cleaned_text,
            'dates': dates,
            'id_numbers': id_numbers,
            'money_items': money_items,
            'keywords_tfidf': keywords_tfidf,
            'keywords_textrank': keywords_textrank
        })
        
        return result
    
    def process_document(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理整个文档的文本
        
        Args:
            pages_data: 页面数据列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的页面数据列表
        """
        return [self.process_page(page) for page in pages_data]


# 测试代码
if __name__ == "__main__":
    cleaner = TextCleaner()
    print("文本清洗器初始化完成")
    
    # 简单测试
    test_text = """
    合同编号: HT-2023-001
    签署日期：2023年05月20日
    甲方：张三，身份证号码：110101199001011234
    乙方：李四
    合同总金额：100000元（人民币壹拾万元整）
    """
    
    cleaned = cleaner.clean_text(test_text)
    print("清洗后的文本:")
    print(cleaned)
    
    dates = cleaner.extract_dates(cleaned)
    print(f"提取到的日期: {dates}")
    
    id_nums = cleaner.extract_id_numbers(cleaned)
    print(f"提取到的身份证号: {id_nums}")
    
    money = cleaner.extract_money(cleaned)
    print(f"提取到的金额: {money}")
    
    keywords = cleaner.extract_keywords(cleaned, topK=5)
    print(f"提取到的关键词: {keywords}") 