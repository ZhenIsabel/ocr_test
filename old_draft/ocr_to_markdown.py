#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR结果JSON转Markdown工具
将OCR识别的JSON结果转换为结构化的Markdown文档

支持的内容类型：
- PrintedText: 印刷文字
- WrittenText: 手写文字  
- PrintedFormula: 印刷公式
- WrittenFormula: 手写公式
- Illustration: 插图（目前没处理）
- Stamp: 印章（目前没处理）
"""

import json
import re
import argparse
from typing import Dict, List, Any


class OCRToMarkdownConverter:
    """OCR结果转Markdown转换器"""
    
    def __init__(self):
        self.current_page = 0
        self.markdown_content = []
        self.table_data = {}  # 存储表格数据
        
    def convert_json_to_markdown(self, json_file_path: str, output_file_path: str = None) -> str:
        """
        将OCR JSON文件转换为Markdown格式
        
        Args:
            json_file_path: JSON文件路径
            output_file_path: 输出Markdown文件路径，如果为None则只返回字符串
            
        Returns:
            Markdown格式的字符串
        """
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 开始转换
        self.markdown_content = []
        self.current_page = 0
        self.table_data = {}
        
        # 处理OCR信息
        if 'OcrInfo' in data:
            self.ProcessOcrInfo(data['OcrInfo'])
        
        # 生成Markdown内容
        markdown_text = '\n'.join(self.markdown_content)
        
        # 保存到文件
        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"Markdown文件已保存到: {output_file_path}")
        
        return markdown_text
    
    def ProcessOcrInfo(self, ocr_info: List[Dict[str, Any]]):
        """处理OCR信息列表"""
        # 按页码排序
        sorted_info = sorted(ocr_info, key=lambda x: x.get('PageIndex', 0))
        
        for page_info in sorted_info:
            page_index = page_info.get('PageIndex', 0)
            text = page_info.get('Text', '')
            details = page_info.get('Detail', [])
            
            # 添加页面分隔符
            if page_index > 0:
                self.markdown_content.append("\n---\n")
            
            # 添加页面标题
            self.markdown_content.append(f"## 第 {page_index + 1} 页\n")
            
            # 处理页面文本
            if text.strip():
                self.ProcessPageText(text)
            
            # 处理详细信息
            if details:
                self.ProcessPageDetails(details, page_index)
    
    def ProcessPageText(self, text: str):
        """处理页面文本内容"""
        # 感觉这里是不需要的，因为value里面会再次输入一次内容，所以这里没必要对文本作处理以及把文本附加进去了
        # 清理文本 - 清除所有空格
        cleaned_text = text.replace(' ', '').strip()
        if not cleaned_text:
            return
        
        # 按行分割
        lines = cleaned_text.split('\n')
        
        current_paragraph = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            line = line.replace(' ', '')  # 去除行内所有空格
            if not line:
                # 空行表示段落分隔
                if current_paragraph:
                    self._add_paragraph(current_paragraph)
                    current_paragraph = []
                continue
            
            # 检测特殊格式（标题、列表、键值对等）
            if self._is_title(line) or self._is_list_item(line) or self._is_numbered_list(line) or self._is_key_value_pair(line):
                # 先处理之前的段落
                if current_paragraph:
                    self._add_paragraph(current_paragraph)
                    current_paragraph = []
                
                # 处理特殊格式
                if self._is_title(line):
                    self.markdown_content.append(f"### {line}\n")
                elif self._is_list_item(line):
                    self.markdown_content.append(f"- {line}\n")
                elif self._is_numbered_list(line):
                    self.markdown_content.append(f"{line}\n")
                elif self._is_key_value_pair(line):
                    self.markdown_content.append(f"**{line}**\n")
            else:
                # 普通文本，需要判断是否需要分行
                if current_paragraph:
                    # 检查上一行是否以标点符号结尾
                    last_line = current_paragraph[-1]
                    should_break = self._should_break_line(last_line, line)
                    
                    if should_break:
                        # 需要分行，先处理当前段落
                        self._add_paragraph(current_paragraph)
                        current_paragraph = [line]
                    else:
                        # 不需要分行，继续添加到当前段落
                        current_paragraph.append(line)
                else:
                    # 第一行，直接添加
                    current_paragraph.append(line)
        
        # 处理最后一个段落
        if current_paragraph:
            self._add_paragraph(current_paragraph)
    
    def ProcessPageDetails(self, details: List[Dict[str, Any]], page_index: int):
        """处理页面详细信息"""
        # 按类型分组处理
        content_by_type = {
            'PrintedText': [],
            'WrittenText': [],
            'PrintedFormula': [],
            'WrittenFormula': [],
            'Illustration': [],
            'Stamp': []
        }
        
        # 表格数据
        table_items = []
        
        for detail in details:
            detail_type = detail.get('Type', '')
            value = detail.get('Value', '').replace(' ', '')
            confidence = detail.get('Confidence', 0)
            in_graph = detail.get('InGraph', False)
            column_index = detail.get('ColumnIndex', -1)
            row_index = detail.get('RowIndex', -1)
            
            # 检查是否为表格内容
            if column_index >= 0 and row_index >= 0:
                table_items.append({
                    'type': detail_type,
                    'value': value,
                    'confidence': confidence,
                    'row': row_index,
                    'column': column_index,
                    'column_span': detail.get('ColumnSpan', 1),
                    'row_span': detail.get('RowSpan', 1)
                })
            else:
                # 按类型分组
                if detail_type in content_by_type:
                    content_by_type[detail_type].append({
                        'text': value,
                        'confidence': confidence,
                        'in_graph': in_graph
                    })
        
        # 处理表格
        if table_items:
            self._process_table_data(table_items, page_index)
        
        # 处理各类型内容
        self._process_content_by_type(content_by_type, page_index)
    
    def _process_table_data(self, table_items: List[Dict], page_index: int):
        """处理表格数据"""
        # 按行列组织数据
        table_data = {}
        max_row = 0
        max_col = 0
        
        for item in table_items:
            row = item['row']
            col = item['column']
            max_row = max(max_row, row)
            max_col = max(max_col, col)
            
            if row not in table_data:
                table_data[row] = {}
            table_data[row][col] = item
        
        # 生成表格Markdown
        if table_data:
            self.markdown_content.append("### 表格内容\n")
            
            # 表头
            header_row = "|"
            separator_row = "|"
            for col in range(max_col + 1):
                header_row += f" 列{col + 1} |"
                separator_row += " --- |"
            
            self.markdown_content.append(header_row)
            self.markdown_content.append(separator_row)
            
            # 数据行
            for row in range(max_row + 1):
                if row in table_data:
                    row_content = "|"
                    for col in range(max_col + 1):
                        if col in table_data[row]:
                            cell_data = table_data[row][col]
                            cell_text = cell_data['value'][:20] + "..." if len(cell_data['value']) > 20 else cell_data['value']
                            row_content += f" {cell_text} |"
                        else:
                            row_content += " |"
                    self.markdown_content.append(row_content)
            
            self.markdown_content.append("")
    
    def _process_content_by_type(self, content_by_type: Dict[str, List], page_index: int):
        """按类型处理内容"""
        type_names = {
            'PrintedText': '印刷文字',
            'WrittenText': '手写文字',
            'PrintedFormula': '印刷公式',
            'WrittenFormula': '手写公式',
            'Illustration': '插图',
            'Stamp': '印章'
        }
        
        has_content = any(content_by_type.values())
        if has_content:
            for content_type, items in content_by_type.items():
            # items 是一个列表，包含同一类型（如PrintedText、WrittenText等）的内容项
            # 每个 item 是一个字典，通常包含如下字段：
            # {
            #     'text': 文字内容（str），
            #     'confidence': 置信度（float），
            #     'in_graph': 是否在图形中（bool），
            #     其他可能字段（如表格相关信息等）
            # }
                if items:
                    for item in items:
                        text = item['text'].strip()
                        confidence = item['confidence']
                        in_graph = item['in_graph']
                        
                        if text and content_type != 'Illustration' and content_type != 'Stamp':
                            self.markdown_content.append(f"{text}")
                            self.markdown_content.append("")
    
    def _is_title(self, line: str) -> bool:
        """判断是否为标题"""
        # 检测中文数字标题
        title_patterns = [
            r'^[一二三四五六七八九十]+、',  # 中文数字标题
            r'^\d+\.\d+',  # 数字标题如 1.1, 2.1
            r'^第[一二三四五六七八九十]+章',  # 第X章
            r'^第[一二三四五六七八九十]+条',  # 第X条
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, line):
                return True
        
        # 检测特殊标题
        special_titles = ['合同', '协议', '附件', '条款', '违约责任', '争议解决']
        for title in special_titles:
            if title in line and len(line) < 50:
                return True
        
        return False
    
    def _is_list_item(self, line: str) -> bool:
        """判断是否为列表项"""
        # 检测项目符号
        list_patterns = [
            r'^[•·▪▫◦‣⁃]\s*',  # 项目符号
            r'^[a-zA-Z]\)\s*',  # 字母编号
            r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*',  # 中文数字编号
        ]
        
        for pattern in list_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _is_numbered_list(self, line: str) -> bool:
        """判断是否为编号列表"""
        # 检测数字编号
        numbered_patterns = [
            r'^\d+\.\s*',  # 1. 格式
            r'^\d+、\s*',  # 1、格式
            r'^\d+\)\s*',  # 1) 格式
        ]
        
        for pattern in numbered_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _is_key_value_pair(self, line: str) -> bool:
        """判断是否为键值对"""
        # 包含冒号且长度适中
        if ':' in line and len(line.split(':')) == 2:
            parts = line.split(':')
            if len(parts[0].strip()) < 20 and len(parts[1].strip()) > 0:
                return True
        
        return False

    def _should_break_line(self, last_line: str, current_line: str) -> bool:
        """
        判断是否需要分行
        
        Args:
            last_line: 上一行内容
            current_line: 当前行内容
            
        Returns:
            True: 需要分行
            False: 不需要分行，应该合并
        """
        # 中文标点符号（句号、问号、感叹号、分号、冒号等）
        chinese_punctuation = ['。', '！', '？', '；', '：', '…', '—']
        # 英文标点符号
        english_punctuation = ['.', '!', '?', ';', ':', '...', '-']
        
        # 检查上一行是否以标点符号结尾
        last_line_trimmed = last_line.strip()
        if not last_line_trimmed:
            return True
        
        ends_with_punctuation = (
            last_line_trimmed[-1] in chinese_punctuation or 
            last_line_trimmed[-1] in english_punctuation
        )
        
        # 如果上一行以标点符号结尾，则应该分行
        if ends_with_punctuation:
            return True
        
        # 如果上一行不以标点符号结尾，检查当前行是否应该合并
        # 检查当前行是否包含特殊格式（如编号、项目符号等）
        if self._contains_special_format(current_line):
            return True
        
        # 其他情况，不分行，合并到当前段落
        return False
    
    def _contains_special_format(self, line: str) -> bool:
        """检查行是否包含特殊格式"""
        # 检查是否包含编号格式
        number_patterns = [
            r'^\d+\.',  # 1.
            r'^\d+、',  # 1、
            r'^\d+\)',  # 1)
            r'^\d+\）',  # 1）
            r'^[一二三四五六七八九十]+、',  # 一、
            r'^[①②③④⑤⑥⑦⑧⑨⑩]',  # ①
        ]
        
        for pattern in number_patterns:
            if re.match(pattern, line):
                return True
        
        # 检查是否包含项目符号
        bullet_patterns = [
            r'^[•·▪▫◦‣⁃]\s*',  # 项目符号
            r'^[a-zA-Z]\)\s*',  # 字母编号
        ]
        
        for pattern in bullet_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _add_paragraph(self, lines: List[str]):
        """添加段落到Markdown内容"""
        if not lines:
            return
        
        # 合并段落行，并清除所有空格
        paragraph_text = ''.join(lines)
        
        if paragraph_text:
            self.markdown_content.append(f"{paragraph_text}\n\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将OCR JSON结果转换为Markdown格式')
    parser.add_argument('input_file', help='输入的JSON文件路径')
    parser.add_argument('-o', '--output', help='输出的Markdown文件路径')
    parser.add_argument('--preview', action='store_true', help='预览转换结果')
    parser.add_argument('--no-details', action='store_true', help='不显示详细信息')
    
    args = parser.parse_args()
    
    # 创建转换器
    converter = OCRToMarkdownConverter()
    
    try:
        # 执行转换
        markdown_content = converter.convert_json_to_markdown(
            args.input_file, 
            args.output
        )
        
        # 预览结果
        if args.preview:
            print("\n" + "="*50)
            print("转换结果预览:")
            print("="*50)
            print(markdown_content[:2000] + "..." if len(markdown_content) > 2000 else markdown_content)
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {args.input_file}")
    except json.JSONDecodeError:
        print(f"错误: {args.input_file} 不是有效的JSON文件")
    except Exception as e:
        print(f"转换过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main() 