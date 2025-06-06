# LexGuard——律盾

本项目集成了 RAG (检索增强生成) 系统和专业法律文本分析功能，可以对文本进行多维度分析，特别适合处理法律文档、隐私政策等专业文本。

## 功能特点

1. 智能文本分析

   - 关键词提取和权重分析
   - 文本摘要生成
   - 相关上下文检索

2. 专业法律分析

   - 隐私条款分析
   - 知识产权相关分析
   - 合同条款分析
   - 法律合规性评估

3. 多维度评估
   - 文本结构分析
   - 专业术语识别
   - 风险等级评估
   - 建议生成

## 安装说明

1. 克隆项目后，首先安装依赖：

```bash
pip install -r requirements.txt
```

2. 确保配置文件完整：
   - config/settings.yaml (RAG 系统配置)
   - config/stopwords.txt (停用词表)
   - legal_config.json (法律分析配置)

## 使用方法

1. 交互式模式：

```bash
python main.py -i
```

2. 文件分析模式：

```bash
python main.py -f 文件路径 -d 分析领域
```

支持的分析领域：

- privacy (隐私政策分析)
- intellectual_property (知识产权分析)
- contract (合同分析)

示例：

```bash
python main.py -f privacy_policy.txt -d privacy
```

## 输出说明

分析结果将保存在 analysis_output 目录下：

- analysis_results.json：包含完整的分析结果
  - RAG 分析结果（关键词、摘要、相关上下文）
  - 法律分析结果（合规性评估、风险等级、专业建议）

## 注意事项

1. 首次运行前需要初始化知识库：

```bash
python scripts/init_knowledge.py
```

2. 确保文本文件使用 UTF-8 编码

## 开发说明

项目结构：

```
AIGC_Programme/
├── main.py              # 主程序入口
├── requirements.txt     # 依赖配置
├── vivo-rag-system/    # RAG系统模块
└── analysis-part/      # 法律分析模块
```

# 隐私条款分析系统

## 项目结构

```
AIGC_Programme/
├── analysis_part/      # 隐私条款分析核心模块
├── vivo_rag_system/    # RAG 系统模块
├── Target.txt         # 待分析的隐私政策文本
├── Analysis.txt       # 分析结果输出文件
└── main.py           # 主程序入口
```

## 使用说明

1. 将需要分析的隐私政策文本放入项目根目录的 `Target.txt` 文件中
2. 运行 `python main.py` 开始分析
3. 分析结果将自动保存在项目根目录的 `Analysis.txt` 文件中

## 功能特点

1. 自动化隐私条款分析
2. 基于 RAG 的智能问答系统
3. 专业法律术语识别
4. 隐私风险评估
5. 合规建议生成

## 依赖安装

```bash
pip install -r requirements.txt
```

## 许可证

MIT License
