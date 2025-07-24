# 房产文档处理系统

房产文档OCR识别、信息提取与匹配系统，用于批量处理房产相关文件（房产证、合同等），提取关键信息并与房源数据库匹配。

## 功能特点

- **文件接入/预处理**：批量导入PDF，拆页、旋转矫正、去噪
- **OCR识别**：调用夸克OCR API识别文档内容
- **文本清洗与关键词提取**：合并换行、正则抽出日期、号码等
- **文档粗分类**：房产证、合同、发票、补充协议等
- **关键信息抽取**：证号/合同号/房号/地址/姓名/身份证号等
- **匹配并分配附件**：与房源库匹配
- **存储与输出**：结构化结果入库
- **校验与回退**：低置信度或未匹配的进入人工校正队列

## 系统架构

```
ocr_test/
  ├─ config/               # 配置文件
  │   ├─ config.py         # 系统配置
  │   └─ patterns.py       # 正则表达式模式定义
  ├─ core/                 # 核心功能模块
  │   ├─ file_processor.py # 文件处理
  │   ├─ ocr_engine.py     # OCR引擎接口
  │   ├─ text_cleaner.py   # 文本清洗
  │   ├─ document_classifier.py # 文档分类
  │   ├─ info_extractor.py # 信息提取
  │   └─ matcher.py        # 匹配模块
  ├─ db/                   # 数据库相关
  │   ├─ storage.py        # 存储接口
  │   └─ models.py         # 数据模型
  ├─ utils/                # 工具函数
  │   ├─ helpers.py        # 辅助函数
  │   └─ validators.py     # 校验工具
  ├─ input/                # 输入文件目录
  ├─ output/               # 输出文件目录
  ├─ temp/                 # 临时文件目录
  ├─ data/                 # 数据存储目录
  │   └─ files/            # 文件存储
  ├─ logs/                 # 日志目录
  ├─ main.py               # 主程序入口
  ├─ quark_ocr.py          # 夸克OCR实现
  ├─ ocr_to_markdown.py    # OCR转Markdown工具
  ├─ ocr_result.json       # OCR结果示例
  ├─ requirements.txt      # 依赖库
  └─ README.md             # 项目说明
```

## 使用方法

### 环境准备

```bash
# 创建虚拟环境（可选）
python -m venv venv
# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 使用示例

1. 处理单个文件:

```bash
python main.py -f input/sample.pdf
```

2. 批量处理目录:

```bash
python main.py -d input/
```

3. 使用房源数据库进行匹配:

```bash
python main.py -f input/sample.pdf -p data/property_db.xlsx
```

### 目录说明

- `input/`: 放置待处理的PDF或图片文件
- `output/`: 存放处理结果
- `temp/`: 临时文件目录
- `data/files/`: 处理后的文件存储位置
- `logs/`: 日志文件

## 开发说明

### 扩展OCR功能

修改 `core/ocr_engine.py` 文件，可以替换或添加其他OCR引擎实现。

### 自定义正则表达式

在 `config/patterns.py` 中定义用于提取特定信息的正则表达式模式。

### 添加新的文档类型

在 `config/patterns.py` 的 `DOC_TYPE_KEYWORDS` 字典中添加新的文档类型及其关键词。

### 训练分类模型

实现 `train_classifier.py`（待开发），使用scikit-learn训练文档分类模型，并在配置中启用模型分类。

## 进阶功能

- **UI界面**：规划中，将提供简单的Web界面进行文档管理
- **API服务**：规划中，将提供REST API供其他系统集成
- **批量导入导出**：支持批量处理和结果导出为Excel
- **模型优化**：持续优化分类和匹配算法

