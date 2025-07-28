#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档分类模块
根据文本内容对文档进行分类
结合规则评分系统和机器学习模型
"""

import os
import sys
import re
import yaml
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import pickle
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
import joblib

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import CLASSIFY_CONFIG
from config.patterns import *  # 导入所有正则表达式模式
from utils.helpers import setup_logger


class DocumentClassifier:
    """文档分类器类"""
    
    def __init__(self, config: Dict = None):
        """初始化文档分类器
        
        Args:
            config: 配置信息，默认使用全局配置
        """
        self.config = config or CLASSIFY_CONFIG
        self.rules = None
        self.model = None
        self.vectorizer = None
        
        # 设置日志记录器
        self.logger = setup_logger('document_classifier', 'logs/document_classifier.log')

        # 加载评分规则
        self.rules_path = self.config.get('rules_path', 'config/score_rules.yml')
        self.load_score_rules()
        
        # 样本存储路径
        self.samples_path = self.config.get('samples_path', 'data/training_samples.pkl')
        self.samples = self.load_samples()
        
        # 如果配置指定使用模型，则尝试加载模型
        if self.config.get('use_model', False):
            self._load_model()
    
    def load_score_rules(self) -> None:
        """加载评分规则"""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                self.rules = yaml.safe_load(f)
                print(f"成功加载评分规则: {self.rules_path}")
        except Exception as e:
            print(f"加载评分规则失败: {str(e)}")
            # 创建一个最基本的规则结构
            self.rules = {'doc_types': {'其它/未知': {'keywords': {'must': []}, 'regex': [], 'score': {'threshold': 0}}}}
    
    def load_samples(self) -> Dict:
        """加载训练样本"""
        if os.path.exists(self.samples_path):
            try:
                with open(self.samples_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"加载训练样本失败: {str(e)}")
        
        # 初始化样本结构
        return {
            'texts': [],
            'labels': [],
            'metadata': {
                'last_updated': None,
                'sample_count': 0
            }
        }
    
    def save_samples(self) -> None:
        """保存训练样本"""
        self.samples['metadata']['last_updated'] = datetime.now()
        self.samples['metadata']['sample_count'] = len(self.samples['texts'])
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.samples_path), exist_ok=True)
            
            with open(self.samples_path, 'wb') as f:
                pickle.dump(self.samples, f)
            print(f"成功保存训练样本: {self.samples_path}")
        except Exception as e:
            print(f"保存训练样本失败: {str(e)}")
    
    def _load_model(self) -> None:
        """加载分类模型"""
        model_path = self.config.get('model_path')
        vectorizer_path = self.config.get('vectorizer_path')
        
        if model_path and os.path.exists(model_path):
            try:
                # 加载SVM模型
                self.model = joblib.load(model_path)
                print(f"成功加载分类模型: {model_path}")
                
                # 加载向量化器
                if vectorizer_path and os.path.exists(vectorizer_path):
                    self.vectorizer = joblib.load(vectorizer_path)
                    print(f"成功加载向量化器: {vectorizer_path}")
                else:
                    print(f"向量化器文件不存在: {vectorizer_path}")
                    self.model = None  # 如果没有向量化器，模型也无法使用
            except Exception as e:
                print(f"加载分类模型失败: {str(e)}")
                self.model = None
        else:
            print(f"分类模型文件不存在: {model_path}")
            self.model = None
    
    def _save_model(self) -> None:
        """保存分类模型"""
        model_path = self.config.get('model_path')
        vectorizer_path = self.config.get('vectorizer_path')
        
        if model_path and self.model:
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                
                # 保存SVM模型
                joblib.dump(self.model, model_path)
                print(f"成功保存分类模型: {model_path}")
                
                # 保存向量化器
                if vectorizer_path and self.vectorizer:
                    os.makedirs(os.path.dirname(vectorizer_path), exist_ok=True)
                    joblib.dump(self.vectorizer, vectorizer_path)
                    print(f"成功保存向量化器: {vectorizer_path}")
            except Exception as e:
                print(f"保存模型失败: {str(e)}")
    
    def train_model(self, incremental: bool = True) -> bool:
        """训练SVM模型
        
        Args:
            incremental: 是否进行增量学习，如果为True则在已有模型基础上继续训练
            
        Returns:
            bool: 是否训练成功
        """
        if not self.samples['texts'] or len(self.samples['texts']) < 2:
            print("训练样本不足，无法训练模型")
            return False
        
        try:
            # 判断是否进行增量学习
            if incremental and self.model and self.vectorizer:
                print(f"执行增量学习，在现有模型基础上继续训练，使用{len(self.samples['texts'])}个样本")
                
                # 使用现有的向量化器转换新文本
                X = self.vectorizer.transform(self.samples['texts'])
                y = self.samples['labels']
                
                # 使用部分样本进行模型校准
                base_svm = SVC(kernel='linear', probability=True, class_weight='balanced')
                # 使用新样本更新模型
                self.model = CalibratedClassifierCV(base_svm, cv=min(3, len(set(y))))
                self.model.fit(X, y)
            else:
                # 重新训练模型
                print(f"从零开始训练新模型，使用{len(self.samples['texts'])}个样本")
                
                # 初始化向量化器
                self.vectorizer = TfidfVectorizer(
                    analyzer='char',
                    ngram_range=(2, 4),
                    max_features=5000
                )
                
                # 转换文本为特征向量
                X = self.vectorizer.fit_transform(self.samples['texts'])
                y = self.samples['labels']
                
                # 初始化并训练SVM模型
                base_svm = SVC(kernel='linear', probability=True, class_weight='balanced')
                self.model = CalibratedClassifierCV(base_svm, cv=min(3, len(set(y))))
                self.model.fit(X, y)
            
            print(f"成功训练模型，使用了{len(self.samples['texts'])}个样本")
            
            # 保存模型
            self._save_model()
            
            return True
        except Exception as e:
            print(f"训练模型失败: {str(e)}")
            return False
    
    def add_training_sample(self, text: str, doc_type: str, confidence: float, is_verified: bool = False) -> bool:
        """添加训练样本
        
        Args:
            text: 文档文本
            doc_type: 文档类型
            confidence: 分类置信度
            is_verified: 是否是人工验证的样本
            
        Returns:
            bool: 是否成功添加样本
        """
        # 样本筛选逻辑：高分样本或人工验证的样本
        score_threshold = self.config.get('sample_score_threshold', 0.8)
        
        if is_verified or confidence >= score_threshold:
            # 添加到样本集
            self.samples['texts'].append(text)
            self.samples['labels'].append(doc_type)
            
            # 保存样本
            self.save_samples()
            
            print(f"添加训练样本：类型={doc_type}, 置信度={confidence:.2f}, 是否验证={is_verified}")
            return True
        
        return False
    
    def evaluate_regex(self, text: str, regex_name: str) -> bool:
        """评估正则表达式是否匹配文本
        
        Args:
            text: 文档文本
            regex_name: 正则表达式名称
            
        Returns:
            bool: 是否匹配
        """
        # 根据正则表达式名称获取对应的模式
        regex_patterns = {
            'certificate_no': PROPERTY_CERT_PATTERN,
            'contract_no': CONTRACT_NUMBER_PATTERN,
            'id_card': ID_NUMBER_PATTERN,
            'date': DATE_PATTERN,
            'price': MONEY_PATTERN,
            'location': ADDRESS_PATTERN,
            'unit_no': HOUSE_NUMBER_PATTERN,
            'area': AREA_PATTERN
        }
        
        if regex_name in regex_patterns:
            return bool(regex_patterns[regex_name].search(text))
        
        return False
    
    def classify_by_rules(self, text: str) -> Dict[str, Any]:
        """使用评分规则对文档进行分类
        
        Args:
            text: 文档文本
            
        Returns:
            Dict[str, Any]: 分类结果，包含类型、置信度和分数
        """
        if not self.rules or 'doc_types' not in self.rules:
            return {'doc_type': '其它/未知', 'confidence': 0, 'scores': {}}
        
        scores = {}
        doc_types = self.rules['doc_types']
        
        for doc_type, rules in doc_types.items():
            score = 0
            score_rules = rules.get('score', {})
            
            # 检查必须关键词
            must_keywords = rules.get('keywords', {}).get('must', [])
            must_count = 0
            for keyword in must_keywords:
                if re.search(keyword, text, re.IGNORECASE):
                    must_count += 1
                    score += score_rules.get('must_keyword', 10)
                    self.logger.info(f"匹配到必须关键词: {keyword}, 得分: {score_rules.get('must_keyword', 10)}")
            
            # 如果有必须关键词但一个都没匹配到，则这个类型不可能
            if must_keywords and must_count == 0:
                scores[doc_type] = 0
                continue
            
            # 检查可选关键词
            optional_keywords = rules.get('keywords', {}).get('optional', [])
            for keyword in optional_keywords:
                if re.search(keyword, text, re.IGNORECASE):
                    score += score_rules.get('optional_keyword', 5)
                    self.logger.info(f"匹配到可选关键词: {keyword}, 得分: {score_rules.get('optional_keyword', 5)}")
            
            # 检查正则表达式
            regex_patterns = rules.get('regex', [])
            for regex_name in regex_patterns:
                if self.evaluate_regex(text, regex_name):
                    score += score_rules.get('regex_hit', 10)
                    self.logger.info(f"匹配到正则表达式: {regex_name}, 得分: {score_rules.get('regex_hit', 10)}")
            
            scores[doc_type] = score
        
        # 找出得分最高的类型
        if not scores:
            return {'doc_type': '其它/未知', 'confidence': 0, 'scores': {}}
        
        best_type = max(scores.items(), key=lambda x: x[1])
        doc_type, score = best_type
        
        # 检查是否达到阈值
        threshold = doc_types.get(doc_type, {}).get('score', {}).get('threshold', 0)
        if score < threshold:
            confidence = score / threshold if threshold > 0 else 0
            return {
                'doc_type': '其它/未知',  # 未达到阈值，返回未知类型
                'candidate_type': doc_type,  # 但仍然记录候选类型
                'confidence': confidence,
                'scores': scores,
                'passed_threshold': False
            }
        
        # 计算置信度 - 这里简单地用得分除以阈值，也可以用其他计算方式
        self.logger.info(f"得分: {score}, 阈值: {threshold}")
        confidence = min(score / threshold if threshold > 0 else 0, 1.0)
        
        return {
            'doc_type': doc_type,
            'confidence': confidence,
            'scores': scores,
            'passed_threshold': True
        }
    
    def classify_by_model(self, text: str) -> Dict[str, Any]:
        """使用SVM模型对文档进行分类
        
        Args:
            text: 文档文本
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        if not self.model or not self.vectorizer:
            return {'doc_type': '其它/未知', 'confidence': 0, 'probabilities': {}}
        
        try:
            # 转换文本为特征向量
            X = self.vectorizer.transform([text])
            
            # 预测概率
            probas = self.model.predict_proba(X)[0]
            classes = self.model.classes_
            
            # 转换为字典
            probabilities = {classes[i]: float(probas[i]) for i in range(len(classes))}
            
            # 找出最高概率的类型
            best_type = max(probabilities.items(), key=lambda x: x[1])
            doc_type, confidence = best_type
            
            return {
                'doc_type': doc_type,
                'confidence': confidence,
                'probabilities': probabilities
            }
        except Exception as e:
            print(f"模型预测失败: {str(e)}")
            return {'doc_type': '其它/未知', 'confidence': 0, 'probabilities': {}}
    
    def classify(self, document_text: str, is_verified: bool = False, verified_type: str = None) -> Dict[str, Any]:
        """对文档进行分类，主入口
        
        Args:
            document_text: 文档文本
            is_verified: 是否是人工验证的结果
            verified_type: 人工验证的文档类型
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        # 如果是人工验证的结果，直接添加到训练样本
        if is_verified and verified_type:
            self.add_training_sample(document_text, verified_type, 1.0, True)
            return {
                'doc_type': verified_type,
                'confidence': 1.0,
                'method': 'verified',
                'rule_scores': {},
                'model_probabilities': {}
            }
        
        # 基于规则的分类
        rule_result = self.classify_by_rules(document_text)
        
        # 如果规则分类通过阈值，使用规则结果
        if rule_result.get('passed_threshold', False):
            doc_type = rule_result['doc_type']
            confidence = rule_result['confidence']
            
            # 添加高分样本到训练集
            self.add_training_sample(document_text, doc_type, confidence)
            
            return {
                'doc_type': doc_type,
                'confidence': confidence,
                'method': 'rules',
                'rule_scores': rule_result.get('scores', {}),
                'model_probabilities': {}
            }
        
        # 如果规则分类未通过阈值且模型可用，使用模型分类
        if self.config.get('use_model', False) and self.model:
            model_result = self.classify_by_model(document_text)
            doc_type = model_result['doc_type']
            confidence = model_result['confidence']
            
            # 如果模型预测置信度很高，也添加到训练集
            model_confidence_threshold = self.config.get('model_confidence_threshold', 0.9)
            if confidence >= model_confidence_threshold:
                self.add_training_sample(document_text, doc_type, confidence)
            
            return {
                'doc_type': doc_type,
                'confidence': confidence,
                'method': 'model',
                'rule_scores': rule_result.get('scores', {}),
                'model_probabilities': model_result.get('probabilities', {})
            }
        
        # 如果规则分类未通过阈值且没有可用模型，默认为"其他"
        # candidate_type = rule_result.get('candidate_type', '其它/未知')
        return {
            'doc_type': '其它/未知',
            'confidence': rule_result['confidence'],
            'method': 'rules_fallback',
            'rule_scores': rule_result.get('scores', {}),
            'model_probabilities': {}
        }
    
    def classify_document_pages(self, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对整个文档的所有页面进行分类
        
        Args:
            pages_data: 页面数据列表
            
        Returns:
            Dict[str, Any]: 文档分类结果
        """
        # 分析各页面的特征
        page_types = []
        for i, page in enumerate(pages_data):
            page_text = page.get('cleaned_text', '')
            page_classification = self.classify(page_text)
            page_types.append({
                'page_index': i,
                'doc_type': page_classification['doc_type'],
                'confidence': page_classification['confidence'],
                'method': page_classification['method']
            })
        
        return page_types


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
    print(f"文档1分类结果: {result1['doc_type']}, 置信度: {result1['confidence']}, 方法: {result1['method']}")
    
    result2 = classifier.classify(test_doc2)
    print(f"文档2分类结果: {result2['doc_type']}, 置信度: {result2['confidence']}, 方法: {result2['method']}") 