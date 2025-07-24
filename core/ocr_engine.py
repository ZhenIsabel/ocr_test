#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OCR引擎模块
封装现有的quark_ocr.py功能，提供统一接口
"""

import os
import json
import sys
from typing import Dict, List, Any, Union, Optional
import requests
import uuid
import hashlib
from time import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import OCR_CONFIG


class OCREngine:
    """OCR引擎类，封装夸克OCR API功能"""
    
    def __init__(self, config: Dict = None):
        """初始化OCR引擎
        
        Args:
            config: OCR配置，默认使用全局配置
        """
        self.config = config or OCR_CONFIG
        self.http_client = self._get_http_client()
        
    def _get_http_client(self):
        """获取HTTP客户端（requests的session对象）"""
        return requests.session()
    
    def _get_signature(self, client_id, client_secret, business, sign_method, sign_nonce, timestamp):
        """生成签名字符串
        根据不同的sign_method选择不同的哈希算法
        
        Args:
            client_id: 客户端ID
            client_secret: 客户端密钥
            business: 业务类型
            sign_method: 签名方法
            sign_nonce: 随机字符串
            timestamp: 时间戳
            
        Returns:
            str: 签名字符串
        """
        # 拼接原始字符串
        raw_str = f"{client_id}_{business}_{sign_method}_{sign_nonce}_{timestamp}_{client_secret}"
        utf8_bytes = raw_str.encode("utf-8")
        
        # 根据sign_method选择不同的摘要算法
        if sign_method.lower() == "sha256":
            digest = hashlib.sha256(utf8_bytes).hexdigest()
        elif sign_method.lower() == "sha1":
            digest = hashlib.sha1(utf8_bytes).hexdigest()
        elif sign_method.lower() == "md5":
            digest = hashlib.md5(utf8_bytes).hexdigest()
        elif sign_method.lower() in ["sha3-256", "sha3_256"]:
            digest = hashlib.sha3_256(utf8_bytes).hexdigest()
        else:
            raise ValueError("Unsupported sign method")  # 不支持的签名方法
            
        # 将摘要转换为小写十六进制字符串
        sign = digest.lower()
        return sign
    
    def _create_request_param(self, file_url: str, file_type: str = "pdf"):
        """构造OCR请求参数
        
        Args:
            file_url: 文件URL
            file_type: 文件类型，默认pdf
            
        Returns:
            Dict: OCR请求参数
        """
        client_id = self.config.get("client_id")
        client_secret = self.config.get("client_secret")
        
        business = "vision"  # 业务类型
        sign_method = "SHA3-256"  # 签名方法
        sign_nonce = uuid.uuid4().hex  # 随机字符串，防重放
        timestamp = int(time() * 1000)  # 当前时间戳（毫秒）
        signature = self._get_signature(client_id, client_secret, business, sign_method, sign_nonce, timestamp)  # 生成签名
        req_id = uuid.uuid4().hex  # 请求唯一ID

        # 构造请求参数字典
        param = {
            "dataUrl": file_url,  # 文件URL
            "dataType": file_type.lower(),  # 输入文件类型，image或者pdf
            "serviceOption": "ocr",  # 服务大类，ocr｜typeset｜structure｜scan
            "inputConfigs": "",  # 输入配置，用于配置输入数据内容
            "outputConfigs": "",  # 输出配置，用于配置输出数据内容
            "reqId": req_id,  # 请求ID, 用于问题定位
            "clientId": client_id,  # 客户端ID
            "signMethod": sign_method,  # 签名方法
            "signNonce": sign_nonce,  # 随机字符串
            "timestamp": timestamp,  # 时间戳字符串，参与加密计算，用户自己设置，不做格式要求
            "signature": signature  # 根据加密算法计算出来的签名字符串，用于鉴权
        }
        
        return param
    
    def recognize_from_url(self, file_url: str, file_type: str = "pdf") -> Dict[str, Any]:
        """从URL识别文本
        
        Args:
            file_url: 文件URL
            file_type: 文件类型，默认pdf
            
        Returns:
            Dict: OCR识别结果
        """
        param = self._create_request_param(file_url, file_type)
        url = self.config.get("url", "https://scan-business.quark.cn/vision")
        headers = {
            "Content-Type": "application/json",
        }
        
        # 发送POST请求
        response = self.http_client.post(url, json=param, headers=headers)
        if response.status_code == 200:
            body = response.json()  # 解析响应体
            code = body.get("code")  # 获取返回码
            
            if code != 0:  # 请求失败
                raise Exception(f"OCR请求失败，错误码: {code}, 错误信息: {body.get('message', '')}")
                
            # 提取OCR结果
            ocr_info = body.get("data", {}).get("OcrInfo", [])
            return {"OcrInfo": ocr_info}
        else:
            raise Exception(f"OCR请求HTTP错误，状态码: {response.status_code}")
    
    def save_result(self, result: Dict[str, Any], output_file: str) -> None:
        """保存OCR结果到文件
        
        Args:
            result: OCR结果
            output_file: 输出文件路径
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
    
    def load_result(self, input_file: str) -> Dict[str, Any]:
        """从文件加载OCR结果
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            Dict: OCR结果
        """
        with open(input_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def extract_text(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从OCR结果中提取文本
        
        Args:
            ocr_result: OCR结果
            
        Returns:
            List[Dict]: 包含文本内容、页码、置信度的列表
        """
        result = []
        
        for item in ocr_result.get("OcrInfo", []):
            text = item.get("Text", "")
            details = item.get("Detail", [])
            
            page_texts = {}
            
            # 按页码分组
            for detail in details:
                if detail.get("Type") in ["PrintedText", "WrittenText"]:
                    page_idx = detail.get("PageIndex", 0)
                    if page_idx not in page_texts:
                        page_texts[page_idx] = []
                    
                    page_texts[page_idx].append({
                        "text": detail.get("Value", ""),
                        "confidence": detail.get("Confidence", 0),
                        "in_graph": detail.get("InGraph", False),
                        "row_index": detail.get("RowIndex", -1),
                        "column_index": detail.get("ColumnIndex", -1)
                    })
            
            # 合并每页的文本
            for page_idx, texts in page_texts.items():
                page_text = " ".join([t["text"] for t in texts])
                avg_confidence = sum([t["confidence"] for t in texts]) / len(texts) if texts else 0
                
                result.append({
                    "page_index": page_idx,
                    "text": page_text,
                    "confidence": avg_confidence,
                    "details": texts
                })
                
        return result


# 测试代码
if __name__ == "__main__":
    ocr_engine = OCREngine()
    print("OCR引擎初始化完成")
    
    # 加载已有的OCR结果进行测试
    try:
        result = ocr_engine.load_result("ocr_result.json")
        extracted = ocr_engine.extract_text(result)
        print(f"成功提取了 {len(extracted)} 页文本")
        if extracted:
            print(f"第一页内容摘要: {extracted[0]['text'][:100]}...")
    except Exception as e:
        print(f"测试加载OCR结果时出错: {str(e)}") 