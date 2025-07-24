#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据模型定义
用于定义系统中使用的数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class FileInfo:
    """文件基本信息"""
    file_id: str
    file_name: str
    original_path: str
    file_md5: str
    file_size: int
    file_ext: str
    import_date: str
    temp_path: Optional[str] = None
    page_count: Optional[int] = None
    status: str = "imported"
    modified_date: Optional[str] = None


@dataclass
class PageInfo:
    """页面信息"""
    page_index: int
    text: str
    cleaned_text: Optional[str] = None
    confidence: float = 0.0
    page_type: Optional[str] = None
    dates: List[str] = field(default_factory=list)
    id_numbers: List[str] = field(default_factory=list)
    money_items: List[Dict[str, Any]] = field(default_factory=list)
    keywords_tfidf: List[tuple] = field(default_factory=list)
    keywords_textrank: List[tuple] = field(default_factory=list)
    details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DocumentClassification:
    """文档分类结果"""
    doc_type: str
    confidence: float
    keyword_scores: Dict[str, float] = field(default_factory=dict)
    model_scores: Dict[str, float] = field(default_factory=dict)
    page_types: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtractedInfo:
    """提取的关键信息"""
    cert_number: Optional[str] = None
    contract_number: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    house_number: Optional[str] = None
    area: Optional[str] = None
    date: Optional[str] = None
    money: Optional[str] = None


@dataclass
class MatchResult:
    """匹配结果"""
    property_id: Optional[str] = None
    cert_number: Optional[str] = None
    address: Optional[str] = None
    house_number: Optional[str] = None
    similarity: float = 0.0
    match_field: Optional[str] = None
    auto_matched: bool = False


@dataclass
class ProcessedDocument:
    """处理后的文档"""
    file_info: FileInfo
    pages: List[PageInfo]
    classification: DocumentClassification
    extracted_info: ExtractedInfo
    match_result: Optional[MatchResult] = None
    processing_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict: 字典表示
        """
        return {
            'file_info': self.file_info.__dict__,
            'pages': [page.__dict__ for page in self.pages],
            'classification': self.classification.__dict__,
            'extracted_info': self.extracted_info.__dict__,
            'match_result': self.match_result.__dict__ if self.match_result else None,
            'processing_time': self.processing_time,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedDocument':
        """从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            ProcessedDocument: 实例
        """
        file_info = FileInfo(**data['file_info'])
        pages = [PageInfo(**page) for page in data['pages']]
        classification = DocumentClassification(**data['classification'])
        extracted_info = ExtractedInfo(**data['extracted_info'])
        match_result = MatchResult(**data['match_result']) if data.get('match_result') else None
        
        return cls(
            file_info=file_info,
            pages=pages,
            classification=classification,
            extracted_info=extracted_info,
            match_result=match_result,
            processing_time=data.get('processing_time', 0.0),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


@dataclass
class WorkItem:
    """工作项（用于队列）"""
    id: str
    file_path: str
    status: str = "pending"  # pending, processing, completed, failed
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict: 字典表示
        """
        return self.__dict__ 