#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
信息提取模块
用于从文档中提取关键信息
"""

import os
import sys
import re
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.patterns import (
    PROPERTY_CERT_PATTERN, CONTRACT_NUMBER_PATTERN, ID_NUMBER_PATTERN,
    DATE_PATTERN, MONEY_PATTERN, ADDRESS_PATTERN, HOUSE_NUMBER_PATTERN, AREA_PATTERN
)


class InfoExtractor:
    """信息提取类"""
    
    def __init__(self, config: Dict = None):
        """初始化信息提取器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        
        # 定义各种信息的上下文窗口大小 (前后字符数)
        self.context_size = {
            'cert_number': 100,
            'contract_number': 100,
            'id_number': 50,
            'address': 150,
            'house_number': 80,
            'area': 50,
            'money': 80,
            'date': 50
        }
    
    def extract_with_context(self, text: str, pattern, context_size: int) -> List[Dict[str, Any]]:
        """提取匹配模式的内容及其上下文
        
        Args:
            text: 文本
            pattern: 正则表达式模式
            context_size: 上下文窗口大小
            
        Returns:
            List[Dict]: 包含匹配内容及上下文的列表
        """
        results = []
        
        for match in pattern.finditer(text):
            start_pos = max(0, match.start() - context_size)
            end_pos = min(len(text), match.end() + context_size)
            
            # 提取上下文
            pre_context = text[start_pos:match.start()]
            post_context = text[match.end():end_pos]
            
            # 处理分组
            if len(match.groups()) > 0:
                # 对于包含分组的模式，取最后一个分组作为值
                value = match.group(len(match.groups()))
            else:
                value = match.group(0)
            
            results.append({
                'value': value.strip(),
                'full_match': match.group(0).strip(),
                'pre_context': pre_context.strip(),
                'post_context': post_context.strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        return results
    
    def extract_cert_numbers(self, text: str) -> List[Dict[str, Any]]:
        """提取证书编号
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 证书编号及上下文
        """
        return self.extract_with_context(text, PROPERTY_CERT_PATTERN, self.context_size['cert_number'])
    
    def extract_contract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """提取合同编号
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 合同编号及上下文
        """
        return self.extract_with_context(text, CONTRACT_NUMBER_PATTERN, self.context_size['contract_number'])
    
    def extract_id_numbers(self, text: str) -> List[Dict[str, Any]]:
        """提取身份证号
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 身份证号及上下文
        """
        return self.extract_with_context(text, ID_NUMBER_PATTERN, self.context_size['id_number'])
    
    def extract_addresses(self, text: str) -> List[Dict[str, Any]]:
        """提取地址
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 地址及上下文
        """
        return self.extract_with_context(text, ADDRESS_PATTERN, self.context_size['address'])
    
    def extract_house_numbers(self, text: str) -> List[Dict[str, Any]]:
        """提取房号
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 房号及上下文
        """
        return self.extract_with_context(text, HOUSE_NUMBER_PATTERN, self.context_size['house_number'])
    
    def extract_areas(self, text: str) -> List[Dict[str, Any]]:
        """提取面积
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 面积及上下文
        """
        return self.extract_with_context(text, AREA_PATTERN, self.context_size['area'])
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """提取日期
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 日期及上下文
        """
        return self.extract_with_context(text, DATE_PATTERN, self.context_size['date'])
    
    def extract_money_amounts(self, text: str) -> List[Dict[str, Any]]:
        """提取金额
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 金额及上下文
        """
        results = []
        for match in MONEY_PATTERN.finditer(text):
            start_pos = max(0, match.start() - self.context_size['money'])
            end_pos = min(len(text), match.end() + self.context_size['money'])
            
            # 提取上下文
            pre_context = text[start_pos:match.start()]
            post_context = text[match.end():end_pos]
            
            # 处理金额信息
            currency = match.group(1) or '人民币'
            amount = match.group(2)
            unit = match.group(5) or ''
            
            value = f"{amount}{unit}元"
            
            results.append({
                'value': value.strip(),
                'currency': currency.strip() if currency else '人民币',
                'amount': amount.strip(),
                'unit': unit + '元' if unit else '元',
                'full_match': match.group(0).strip(),
                'pre_context': pre_context.strip(),
                'post_context': post_context.strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        return results
    
    def extract_all_info(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """提取所有类型的信息
        
        Args:
            text: 文本
            
        Returns:
            Dict[str, List]: 所有提取的信息
        """
        return {
            'cert_numbers': self.extract_cert_numbers(text),
            'contract_numbers': self.extract_contract_numbers(text),
            'id_numbers': self.extract_id_numbers(text),
            'addresses': self.extract_addresses(text),
            'house_numbers': self.extract_house_numbers(text),
            'areas': self.extract_areas(text),
            'dates': self.extract_dates(text),
            'money_amounts': self.extract_money_amounts(text)
        }
    
    def extract_document_info(self, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从文档所有页面提取信息
        
        Args:
            pages_data: 页面数据列表
            
        Returns:
            Dict: 提取的文档信息
        """
        # 合并所有页面的文本
        all_text = " ".join([page.get('cleaned_text', '') for page in pages_data])
        
        # 提取所有信息
        all_info = self.extract_all_info(all_text)
        
        # 页面级信息提取
        page_info = []
        for i, page in enumerate(pages_data):
            page_text = page.get('cleaned_text', '')
            info = self.extract_all_info(page_text)
            page_info.append({
                'page_index': i,
                'info': info
            })
        
        # 确定最可能的关键信息
        key_info = self._determine_key_info(all_info)
        
        return {
            'key_info': key_info,
            'all_info': all_info,
            'page_info': page_info
        }
    
    def _determine_key_info(self, all_info: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """确定最可能的关键信息
        
        Args:
            all_info: 所有提取的信息
            
        Returns:
            Dict: 关键信息
        """
        key_info = {}
        
        # 提取证书编号
        if all_info['cert_numbers']:
            key_info['cert_number'] = all_info['cert_numbers'][0]['value']
        
        # 提取合同编号
        if all_info['contract_numbers']:
            key_info['contract_number'] = all_info['contract_numbers'][0]['value']
        
        # 提取身份证号
        if all_info['id_numbers']:
            key_info['id_number'] = all_info['id_numbers'][0]['value']
        
        # 提取地址
        if all_info['addresses']:
            # 选择最长的地址作为主要地址
            key_info['address'] = max(all_info['addresses'], key=lambda x: len(x['value']))['value']
        
        # 提取房号
        if all_info['house_numbers']:
            key_info['house_number'] = all_info['house_numbers'][0]['value']
        
        # 提取面积
        if all_info['areas']:
            key_info['area'] = all_info['areas'][0]['value']
        
        # 提取最重要的日期（第一个）
        if all_info['dates']:
            key_info['date'] = all_info['dates'][0]['value']
        
        # 提取最大金额
        if all_info['money_amounts']:
            key_info['money'] = max(all_info['money_amounts'], key=lambda x: float(x['amount'].replace(',', '')))['value']
        
        return key_info


# 测试代码
if __name__ == "__main__":
    extractor = InfoExtractor()
    print("信息提取器初始化完成")
    
    # 简单测试
    test_text = """
    不动产权证书
    证号: 京(2023)朝阳区不动产权第0012345号
    权利人: 张三，身份证号码：110101199001011234
    坐落: 北京市朝阳区某某路100号1号楼5单元801
    权利类型: 国有建设用地使用权/房屋所有权
    权利性质: 出让/商品房
    用途: 住宅用地/住宅
    面积: 土地使用权面积:5.23㎡ 房屋建筑面积:90.25㎡
    
    签发日期: 2023年06月15日
    """
    
    all_info = extractor.extract_all_info(test_text)
    print("提取的证书编号:", [item['value'] for item in all_info['cert_numbers']])
    print("提取的身份证号:", [item['value'] for item in all_info['id_numbers']])
    print("提取的地址:", [item['value'] for item in all_info['addresses']])
    print("提取的房号:", [item['value'] for item in all_info['house_numbers']])
    print("提取的面积:", [item['value'] for item in all_info['areas']])
    print("提取的日期:", [item['value'] for item in all_info['dates']]) 