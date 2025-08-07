# 房产文档智能处理系统

本系统用于批量处理房产相关文档（如房产证、合同等），实现OCR识别、关键信息提取、类型分类、与房源数据库智能匹配，并输出结构化结果，助力房产档案数字化与自动化管理。

---

## 主要功能

- **批量文件接入与预处理**  
  支持PDF/图片批量导入，自动拆页、旋转矫正、去噪等预处理。

- **OCR识别**  
  集成夸克OCR API，自动识别文档内容。

- **文本清洗与关键信息抽取**  
  合并换行、正则提取日期、证号、地址、姓名等关键信息。

- **文档类型自动分类**  
  支持房产证、合同、发票、补充协议等多种类型自动识别。

- **智能匹配房源数据库**  
  按证号、人名、地址等多字段智能匹配，支持模糊/近似匹配。

- **结构化存储与输出**  
  结果自动入库，支持导出为Excel等格式。

- **异常校验与人工回退**  
  低置信度或未匹配项自动进入人工校正队列。

---

## 目录结构

```
ocr_test/
├─ config/           # 配置与正则模式
│   ├─ config.py
│   ├─ patterns.py
│   └─ score_rules.yml
├─ core/             # 核心功能模块
│   ├─ file_processor.py
│   ├─ ocr_engine.py
│   ├─ text_cleaner.py
│   ├─ document_classifier.py
│   ├─ info_extractor.py
│   └─ matcher.py
├─ db/               # 数据库接口与模型
│   ├─ storage.py
│   └─ models.py
├─ utils/            # 工具函数
│   ├─ helpers.py
│   └─ validators.py
├─ data/             # 数据与样本
│   ├─ files/
│   ├─ sample_property_db.csv
│   └─ training_samples.pkl
├─ input/            # 输入文件目录
├─ output/           # 输出结果目录
├─ logs/             # 日志目录
├─ temp/             # 临时文件
├─ main.py           # 主程序入口
├─ README.md         # 项目说明
├─ requirements.txt  # 依赖库
```

---

## 快速开始

### 1. 环境准备

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

### 2. 使用示例

- **处理单个文件**
  ```bash
  python main.py -f input/sample.pdf
  ```

- **批量处理目录**
  ```bash
  python main.py -d input/
  ```

- **指定房源数据库进行匹配**
  ```bash
  python main.py -f input/sample.pdf -p data/sample_property_db.csv
  ```

### 3. 结果查看

- 结构化结果输出至 `output/` 目录
- 日志与异常信息见 `logs/`

---

## 核心流程说明

1. **文件导入与预处理**  
   支持PDF/图片批量导入，自动拆分、旋转、去噪。

2. **OCR识别**  
   通过 `core/ocr_engine.py` 调用OCR接口，输出文本。

3. **文本清洗与关键信息提取**  
   通过 `core/text_cleaner.py`、`core/info_extractor.py`，结合 `config/patterns.py` 中的正则模式，提取证号、地址、人名等。

4. **文档类型分类**  
   通过 `core/document_classifier.py`，基于规则或模型自动分类。

5. **与房源数据库智能匹配**  
   通过 `core/matcher.py`，按证号、人名、地址等多字段综合比对，支持模糊匹配，自动找到最优匹配行。

6. **结构化存储与输出**  
   通过 `db/storage.py`，将结果入库并导出。

7. **异常校验与人工回退**  
   置信度低或未匹配项自动进入人工校正队列。

---

## 扩展与定制

- **OCR引擎可扩展**：可在 `core/ocr_engine.py` 替换/新增OCR服务。
- **正则模式自定义**：在 `config/patterns.py` 定义/调整关键信息提取规则。
- **文档类型扩展**：在 `config/patterns.py` 的 `DOC_TYPE_KEYWORDS` 增加新类型。
- **分类模型训练**：后续可开发 `train_classifier.py`，用scikit-learn等训练自定义分类模型。
- **批量导入导出**：支持批量处理与Excel导出。

---

## 适用场景

- 房产档案数字化、批量信息录入
- 房源信息自动核验与匹配
- 房产证、合同等文档的结构化管理