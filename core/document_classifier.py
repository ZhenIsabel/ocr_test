#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档分类模块
根据文本内容对文档进行分类
"""

import os
import sys
import re
from typing import Dict, List, Any, Tuple, Optional
import pickle

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import CLASSIFY_CONFIG
from config.patterns import DOC_TYPE_KEYWORDS


class DocumentClassifier:
    """文档分类器类"""
    
    def __init__(self, config: Dict = None):
        """初始化文档分类器
        
        Args:
            config: 配置信息，默认使用全局配置
        """
        self.config = config or CLASSIFY_CONFIG
        self.model = None
        self.keywords = DOC_TYPE_KEYWORDS
        
        # 如果配置指定使用模型，则尝试加载模型
        if self.config.get('use_model', False):
            self._load_model()
    
    def _load_model(self) -> None:
        """加载分类模型"""
        model_path = self.config.get('model_path')
        if model_path and os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"成功加载分类模型: {model_path}")
            except Exception as e:
                print(f"加载分类模型失败: {str(e)}")
                self.model = None
        else:
            print(f"分类模型文件不存在: {model_path}")
            self.model = None
    
    def classify_by_keywords(self, text: str) -> Dict[str, float]:
        """使用关键词匹配对文档进行分类
        
        Args:
            text: 文档文本
            
        Returns:
            Dict[str, float]: 文档类型及其匹配分数
        """
        scores = {}
        
        # 计算每个类型的得分
        for doc_type, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                # 统计关键词出现次数并累加分数
                count = len(re.findall(keyword, text, re.IGNORECASE))
                score += count
            
            # 归一化分数
            if keywords:  # 避免除以零
                score = score / len(keywords)
            
            scores[doc_type] = score
        
        return scores
    
    def classify_by_model(self, text: str) -> Dict[str, float]:
        """使用机器学习模型对文档进行分类
        
        Args:
            text: 文档文本
            
        Returns:
            Dict[str, float]: 文档类型及其置信度
        """
        if not self.model:
            return {}
            
        try:
            # 这里应根据实际模型的预处理和预测方法进行调整
            proba = self.model.predict_proba([text])[0]
            classes = self.model.classes_
            
            return {classes[i]: float(proba[i]) for i in range(len(classes))}
        except Exception as e:
            print(f"模型预测失败: {str(e)}")
            return {}
    
    def classify(self, document_text: str) -> Dict[str, Any]:
        """对文档进行分类
        
        Args:
            document_text: 文档文本
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        # 基于规则的分类
        keyword_scores = self.classify_by_keywords(document_text)
        
        # 基于模型的分类（如果配置启用）
        model_scores = {}
        if self.config.get('use_model', False) and self.model:
            model_scores = self.classify_by_model(document_text)
        
        # 确定最终类型
        if model_scores:
            # 如果有模型预测结果，优先使用模型结果
            doc_type = max(model_scores.items(), key=lambda x: x[1])[0]
            confidence = model_scores[doc_type]
        else:
            # 否则使用关键词匹配结果
            doc_type = max(keyword_scores.items(), key=lambda x: x[1])[0]
            total_score = sum(keyword_scores.values())
            confidence = keyword_scores[doc_type] / total_score if total_score > 0 else 0
        
        # 如果最高分数为0，则归为"其他"类
        if confidence == 0:
            doc_type = "其他"
        
        return {
            'doc_type': doc_type,
            'confidence': confidence,
            'keyword_scores': keyword_scores,
            'model_scores': model_scores
        }
    
    def classify_document_pages(self, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对整个文档的所有页面进行分类
        
        Args:
            pages_data: 页面数据列表
            
        Returns:
            Dict[str, Any]: 文档分类结果
        """
        # 合并所有页面的文本
        all_text = " ".join([page.get('cleaned_text', '') for page in pages_data])
        
        # 进行分类
        classification = self.classify(all_text)
        
        # 分析各页面的特征
        page_types = []
        for i, page in enumerate(pages_data):
            page_text = page.get('cleaned_text', '')
            page_classification = self.classify(page_text)
            page_types.append({
                'page_index': i,
                'doc_type': page_classification['doc_type'],
                'confidence': page_classification['confidence']
            })
        
        # 更新分类结果
        classification['page_types'] = page_types
        
        return classification


# 测试代码
if __name__ == "__main__":
    classifier = DocumentClassifier()
    print("文档分类器初始化完成")
    
    # 简单测试
    test_doc1 = """
    不动产权证书
    证号: 京(2023)朝阳区不动产权第0012345号
    权利人: 张三
    坐落: 北京市朝阳区某某路100号1号楼5单元801
    权利类型: 国有建设用地使用权/房屋所有权
    权利性质: 出让/商品房
    用途: 住宅用地/住宅
    面积: 土地使用权面积:5.23㎡ 房屋建筑面积:90.25㎡
    """
    
    test_doc2 = """
    商品房买卖合同
    合同编号: HT-2023-001
    
    出卖人: XX房地产开发有限公司
    买受人: 李四
    
    商品房基本情况:
    项目名称: XX花园
    房屋坐落: 北京市海淀区某某路200号
    房屋用途: 住宅
    建筑面积: 89.50平方米
    
    价款: 总价人民币叁佰万元整(¥3,000,000.00)
    
    付款方式: 按揭付款
    """
    
    result1 = classifier.classify(test_doc1)
    print(f"文档1分类结果: {result1['doc_type']}, 置信度: {result1['confidence']}")
    
    result2 = classifier.classify(test_doc2)
    print(f"文档2分类结果: {result2['doc_type']}, 置信度: {result2['confidence']}") 