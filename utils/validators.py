#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校验工具模块
用于对提取的信息进行校验
"""

import re
import datetime
from typing import Dict, List, Any, Union, Optional, Tuple, Callable


class Validator:
    """校验器类"""
    
    @staticmethod
    def is_valid_cert_number(cert_number: str) -> bool:
        """校验证书编号是否有效
        
        Args:
            cert_number: 证书编号
            
        Returns:
            bool: 是否有效
        """
        if not cert_number:
            return False
            
        # 证书编号通常包含省市区信息和编号
        # 示例格式: 京(2023)朝阳区不动产权第0012345号
        pattern = r'^[\u4e00-\u9fa5]\([0-9]{4}\)[\u4e00-\u9fa5]{2,}[第]([0-9A-Z\-]+)[号]$'
        return bool(re.match(pattern, cert_number))
    
    @staticmethod
    def is_valid_contract_number(contract_number: str) -> bool:
        """校验合同编号是否有效
        
        Args:
            contract_number: 合同编号
            
        Returns:
            bool: 是否有效
        """
        if not contract_number:
            return False
            
        # 合同编号通常是字母数字组合
        # 示例格式: HT-2023-001, XS20230001
        pattern = r'^[A-Z0-9\-]{5,}$'
        return bool(re.match(pattern, contract_number))
    
    @staticmethod
    def is_valid_id_number(id_number: str) -> bool:
        """校验身份证号是否有效
        
        Args:
            id_number: 身份证号
            
        Returns:
            bool: 是否有效
        """
        if not id_number:
            return False
            
        # 18位身份证号
        if len(id_number) == 18:
            # 检查格式
            pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
            if not re.match(pattern, id_number):
                return False
                
            # 检查校验位
            factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
            checksum_map = '10X98765432'
            checksum = sum(int(id_number[i]) * factors[i] for i in range(17))
            return id_number[17].upper() == checksum_map[checksum % 11]
        
        # 15位身份证号
        elif len(id_number) == 15:
            pattern = r'^[1-9]\d{7}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}$'
            return bool(re.match(pattern, id_number))
            
        return False
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """校验日期是否有效
        
        Args:
            date_str: 日期字符串
            
        Returns:
            bool: 是否有效
        """
        if not date_str:
            return False
            
        # 支持的日期格式
        formats = [
            '%Y年%m月%d日',
            '%Y-%m-%d',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                datetime.datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
                
        return False
    
    @staticmethod
    def is_valid_money(money_str: str) -> bool:
        """校验金额是否有效
        
        Args:
            money_str: 金额字符串
            
        Returns:
            bool: 是否有效
        """
        if not money_str:
            return False
            
        # 移除货币符号和单位
        cleaned = re.sub(r'[^\d.]', '', money_str)
        
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_area(area_str: str) -> bool:
        """校验面积是否有效
        
        Args:
            area_str: 面积字符串
            
        Returns:
            bool: 是否有效
        """
        if not area_str:
            return False
            
        # 提取数字部分
        match = re.search(r'([\d.]+)', area_str)
        if not match:
            return False
            
        try:
            value = float(match.group(1))
            # 面积应为正数且在合理范围内
            return 0 < value < 10000
        except ValueError:
            return False
    
    @staticmethod
    def validate_info(info: Dict[str, Any]) -> Dict[str, bool]:
        """校验提取的信息
        
        Args:
            info: 提取的信息字典
            
        Returns:
            Dict[str, bool]: 校验结果
        """
        validators = {
            'cert_number': Validator.is_valid_cert_number,
            'contract_number': Validator.is_valid_contract_number,
            'id_number': Validator.is_valid_id_number,
            'date': Validator.is_valid_date,
            'money': Validator.is_valid_money,
            'area': Validator.is_valid_area
        }
        
        results = {}
        for key, value in info.items():
            validator = validators.get(key)
            if validator:
                results[key] = validator(value)
            else:
                # 对于没有特定验证器的字段，只验证非空
                results[key] = bool(value)
                
        return results
    
    @staticmethod
    def get_validation_errors(info: Dict[str, Any]) -> Dict[str, str]:
        """获取校验错误信息
        
        Args:
            info: 提取的信息字典
            
        Returns:
            Dict[str, str]: 错误信息
        """
        validation_results = Validator.validate_info(info)
        errors = {}
        
        for key, is_valid in validation_results.items():
            if not is_valid and key in info and info[key]:
                errors[key] = f"'{info[key]}' 不是有效的{key}格式"
                
        return errors


# 测试代码
if __name__ == "__main__":
    # 测试证书编号校验
    cert_numbers = [
        "京(2023)朝阳区不动产权第0012345号",  # 有效
        "沪(2022)浦东新区不动产权第0098765号",  # 有效
        "123456",  # 无效
        "不动产权证"  # 无效
    ]
    
    print("=== 证书编号校验 ===")
    for cert in cert_numbers:
        print(f"{cert}: {'有效' if Validator.is_valid_cert_number(cert) else '无效'}")
    
    # 测试身份证号校验
    id_numbers = [
        "110101199001011234",  # 有效
        "11010119900101123X",  # 有效
        "110101900101123",     # 有效
        "12345678",            # 无效
        "11010119901301234"    # 无效日期
    ]
    
    print("\n=== 身份证号校验 ===")
    for id_num in id_numbers:
        print(f"{id_num}: {'有效' if Validator.is_valid_id_number(id_num) else '无效'}")
    
    # 测试日期校验
    dates = [
        "2023年07月15日",  # 有效
        "2023-07-15",     # 有效
        "2023/07/15",     # 有效
        "2023.07.15",     # 无效
        "2023年7月32日"    # 无效日期
    ]
    
    print("\n=== 日期校验 ===")
    for date in dates:
        print(f"{date}: {'有效' if Validator.is_valid_date(date) else '无效'}")
    
    # 测试面积校验
    areas = [
        "90.25平方米",  # 有效
        "120㎡",       # 有效
        "0平方米",     # 无效
        "abc㎡"        # 无效
    ]
    
    print("\n=== 面积校验 ===")
    for area in areas:
        print(f"{area}: {'有效' if Validator.is_valid_area(area) else '无效'}")
    
    # 测试整体校验
    test_info = {
        "cert_number": "京(2023)朝阳区不动产权第0012345号",
        "id_number": "110101199001011234",
        "date": "2023年07月15日",
        "money": "100万元",
        "area": "90.25平方米",
        "address": "北京市朝阳区某某路100号"
    }
    
    validation_results = Validator.validate_info(test_info)
    print("\n=== 整体校验结果 ===")
    for key, result in validation_results.items():
        print(f"{key}: {'通过' if result else '不通过'}")
    
    # 测试获取错误信息
    test_info_with_errors = {
        "cert_number": "123456",
        "id_number": "1101011990010",
        "date": "2023年7月32日",
        "money": "abc元",
        "area": "0平方米",
        "address": "北京市朝阳区某某路100号"
    }
    
    errors = Validator.get_validation_errors(test_info_with_errors)
    print("\n=== 校验错误信息 ===")
    for key, error in errors.items():
        print(f"{key}: {error}") 