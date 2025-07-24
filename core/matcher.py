#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
匹配模块
用于将文档与房源数据库进行匹配
"""

import os
import sys
import re
from typing import Dict, List, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import MATCH_CONFIG


class DocumentMatcher:
    """文档匹配器类"""
    
    def __init__(self, config: Dict = None):
        """初始化文档匹配器
        
        Args:
            config: 配置信息，默认使用全局配置
        """
        self.config = config or MATCH_CONFIG
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)
        self.top_n = self.config.get('top_n', 3)
        
        # 房源数据库，实际使用时可以从数据库加载
        self.property_db = None
    
    def load_property_db(self, data_source: Union[str, pd.DataFrame]) -> None:
        """加载房源数据库
        
        Args:
            data_source: 数据源，可以是CSV/Excel文件路径或DataFrame对象
        """
        if isinstance(data_source, str):
            # 从文件加载
            if data_source.endswith('.csv'):
                self.property_db = pd.read_csv(data_source)
            elif data_source.endswith(('.xls', '.xlsx')):
                self.property_db = pd.read_excel(data_source)
            else:
                raise ValueError(f"不支持的文件格式: {data_source}")
        elif isinstance(data_source, pd.DataFrame):
            # 直接使用DataFrame
            self.property_db = data_source
        else:
            raise ValueError("data_source必须是文件路径或DataFrame对象")
        
        print(f"成功加载房源数据库，共 {len(self.property_db)} 条记录")
    
    def match_by_cert_number(self, cert_number: str, threshold: float = None) -> List[Dict[str, Any]]:
        """通过证书编号匹配房源
        
        Args:
            cert_number: 证书编号
            threshold: 相似度阈值，默认使用配置中的值
            
        Returns:
            List[Dict]: 匹配结果列表
        """
        if self.property_db is None:
            raise ValueError("房源数据库未加载")
            
        threshold = threshold or self.similarity_threshold
        
        if 'cert_number' not in self.property_db.columns:
            print("警告: 房源数据库中没有'cert_number'字段")
            return []
        
        results = []
        
        # 使用模糊匹配计算相似度
        for _, row in self.property_db.iterrows():
            db_cert_number = str(row['cert_number'])
            similarity = fuzz.ratio(cert_number, db_cert_number) / 100.0
            
            if similarity >= threshold:
                results.append({
                    'property_id': row.get('property_id', ''),
                    'cert_number': db_cert_number,
                    'address': row.get('address', ''),
                    'similarity': similarity,
                    'match_field': 'cert_number',
                    'row_data': row.to_dict()
                })
        
        # 按相似度降序排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 返回top N结果
        return results[:self.top_n]
    
    def match_by_address(self, address: str, threshold: float = None) -> List[Dict[str, Any]]:
        """通过地址匹配房源
        
        Args:
            address: 地址
            threshold: 相似度阈值，默认使用配置中的值
            
        Returns:
            List[Dict]: 匹配结果列表
        """
        if self.property_db is None:
            raise ValueError("房源数据库未加载")
            
        threshold = threshold or self.similarity_threshold
        
        if 'address' not in self.property_db.columns:
            print("警告: 房源数据库中没有'address'字段")
            return []
        
        results = []
        
        # 使用模糊匹配计算相似度
        for _, row in self.property_db.iterrows():
            db_address = str(row['address'])
            similarity = fuzz.token_sort_ratio(address, db_address) / 100.0
            
            if similarity >= threshold:
                results.append({
                    'property_id': row.get('property_id', ''),
                    'cert_number': row.get('cert_number', ''),
                    'address': db_address,
                    'similarity': similarity,
                    'match_field': 'address',
                    'row_data': row.to_dict()
                })
        
        # 按相似度降序排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 返回top N结果
        return results[:self.top_n]
    
    def match_by_house_number(self, house_number: str, threshold: float = None) -> List[Dict[str, Any]]:
        """通过房号匹配房源
        
        Args:
            house_number: 房号
            threshold: 相似度阈值，默认使用配置中的值
            
        Returns:
            List[Dict]: 匹配结果列表
        """
        if self.property_db is None:
            raise ValueError("房源数据库未加载")
            
        threshold = threshold or self.similarity_threshold
        
        if 'house_number' not in self.property_db.columns:
            print("警告: 房源数据库中没有'house_number'字段")
            return []
        
        results = []
        
        # 使用模糊匹配计算相似度
        for _, row in self.property_db.iterrows():
            db_house_number = str(row['house_number'])
            similarity = fuzz.ratio(house_number, db_house_number) / 100.0
            
            if similarity >= threshold:
                results.append({
                    'property_id': row.get('property_id', ''),
                    'cert_number': row.get('cert_number', ''),
                    'house_number': db_house_number,
                    'address': row.get('address', ''),
                    'similarity': similarity,
                    'match_field': 'house_number',
                    'row_data': row.to_dict()
                })
        
        # 按相似度降序排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 返回top N结果
        return results[:self.top_n]
    
    def match_document(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """匹配文档信息与房源数据库
        
        Args:
            doc_info: 文档提取的信息
            
        Returns:
            Dict: 匹配结果
        """
        if self.property_db is None:
            raise ValueError("房源数据库未加载")
        
        # 获取关键信息
        key_info = doc_info.get('key_info', {})
        
        results = {
            'cert_number_matches': [],
            'address_matches': [],
            'house_number_matches': []
        }
        
        # 通过证书编号匹配
        cert_number = key_info.get('cert_number')
        if cert_number:
            results['cert_number_matches'] = self.match_by_cert_number(cert_number)
        
        # 通过地址匹配
        address = key_info.get('address')
        if address:
            results['address_matches'] = self.match_by_address(address)
        
        # 通过房号匹配
        house_number = key_info.get('house_number')
        if house_number:
            results['house_number_matches'] = self.match_by_house_number(house_number)
        
        # 合并和排序所有匹配结果
        all_matches = []
        all_matches.extend(results['cert_number_matches'])
        all_matches.extend(results['address_matches'])
        all_matches.extend(results['house_number_matches'])
        
        # 按相似度降序排序
        all_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 去重（基于property_id）
        unique_matches = []
        seen_ids = set()
        for match in all_matches:
            property_id = match['property_id']
            if property_id not in seen_ids:
                unique_matches.append(match)
                seen_ids.add(property_id)
        
        # 确定最佳匹配
        best_match = None
        if unique_matches:
            best_match = unique_matches[0]
        
        # 自动匹配结果
        auto_match = best_match if best_match and best_match['similarity'] >= self.similarity_threshold else None
        
        return {
            'all_matches': unique_matches[:self.top_n],
            'best_match': best_match,
            'auto_match': auto_match,
            'field_matches': results
        }


# 测试代码
if __name__ == "__main__":
    matcher = DocumentMatcher()
    print("文档匹配器初始化完成")
    
    # 创建一个示例房源数据库
    sample_data = {
        'property_id': ['P001', 'P002', 'P003', 'P004'],
        'cert_number': [
            '京(2023)朝阳区不动产权第0012345号',
            '京(2023)海淀区不动产权第0054321号',
            '京(2022)东城区不动产权第0023456号',
            '京(2021)西城区不动产权第0098765号'
        ],
        'address': [
            '北京市朝阳区某某路100号1号楼5单元801',
            '北京市海淀区某某街200号2号楼3单元502',
            '北京市东城区某某胡同30号平房',
            '北京市西城区某某大街50号3号楼2单元301'
        ],
        'house_number': ['5-801', '3-502', '30号', '2-301']
    }
    
    sample_df = pd.DataFrame(sample_data)
    matcher.load_property_db(sample_df)
    
    # 测试匹配
    test_cert = '京(2023)朝阳区不动产权第0012346号'  # 稍有差异
    cert_matches = matcher.match_by_cert_number(test_cert)
    print(f"证书号匹配结果: {len(cert_matches)} 条")
    if cert_matches:
        print(f"最佳匹配: {cert_matches[0]['cert_number']}, 相似度: {cert_matches[0]['similarity']:.2f}")
    
    test_address = '北京市朝阳区某某路100号1栋501'  # 较大差异
    addr_matches = matcher.match_by_address(test_address)
    print(f"地址匹配结果: {len(addr_matches)} 条")
    if addr_matches:
        print(f"最佳匹配: {addr_matches[0]['address']}, 相似度: {addr_matches[0]['similarity']:.2f}") 