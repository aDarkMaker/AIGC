# LexGuard——律盾 法律文本智能分析系统

一个集成了 RAG (检索增强生成) 系统和专业法律文本分析功能的智能法律助手，支持模型训练、多维度分析、Web 界面和专业法律建议生成。

## ✨ 核心特性

### 🎯 智能分析引擎

- **多维度文档评分**：内容质量、法律合规性、完整性、清晰度四维度严格打分
- **专业法律分析**：隐私条款、知识产权、合同条款深度解析
- **风险评估系统**：智能识别法律风险点并提供改进建议
- **情感分析**：文档情感倾向分析和复杂度计算

### 🚀 先进技术架构

- **RAG 检索增强**：结合向量数据库的智能问答系统
- **BERT 模型训练**：法律领域专用模型微调
- **混合精度训练**：GPU/CPU 自适应优化
- **实时性能监控**：TensorBoard 集成训练可视化

### 🌐 多样化交互方式

- **Web 界面**：现代化响应式 UI，支持文件上传和实时分析
- **命令行工具**：支持批量处理和自动化脚本
- **API 服务**：FastAPI 构建的 RESTful 接口
- **交互式模式**：用户友好的命令行交互界面

## 📁 项目结构

```
AIGC_Programme/
├── main.py                    # 主程序入口
├── requirements.txt           # 基础依赖
├── Target.txt                 # 默认分析文件
├── README.md                  # 项目文档
├── TRAINING_TROUBLESHOOTING.md # 训练故障排除
│
├── analysis_part/             # 法律分析核心模块
│   ├── analysis.py           # 主分析引擎
│   ├── legal_analyzer.py     # 法律专业分析
│   ├── config.json           # 分析配置
│   ├── legal_config.json     # 法律术语配置
│   └── legal_terms.txt       # 法律术语词典
│
├── vivo_rag_system/          # RAG系统模块
│   ├── src/                  # RAG核心代码
│   ├── config/               # RAG配置文件
│   ├── data/                 # 知识库数据
│   └── scripts/              # 工具脚本
│
├── Law-Train/                # 模型训练模块
│   ├── src/                  # 训练核心代码
│   ├── model/                # 模型存储
│   ├── data/                 # 训练数据
│   └── docs/                 # 法律文档语料
│
├── web_interface/            # Web前端界面
│   ├── index.html           # 主页面
│   ├── server.py            # Flask后端服务
│   ├── script.js            # 前端交互逻辑
│   ├── styles.css           # 样式文件
│   ├── instructions.html    # 使用说明
│   └── privacy.html         # 隐私政策
│
├── utils/                    # 工具模块
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志系统
│   └── auth_util.py         # 认证工具
│
├── analysis_output/          # 分析结果输出
├── logs/                     # 系统日志
└── wandb/                    # 训练监控数据
```

## 🛠️ 环境要求

### 基础环境

- **Python**: 3.8+ (推荐 3.9+)
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最低 4GB，推荐 8GB+
- **存储**: 至少 2GB 可用空间

### 硬件建议

- **CPU**: 4 核心以上处理器
- **GPU**: 可选，NVIDIA GTX 1060+（用于模型训练加速）
- **网络**: 稳定的互联网连接（用于依赖下载，必要时需要使用 VPN）

## 📦 完整部署指南

### 第一步：获取项目代码

```bash
# 方式1：Git克隆（如果有Git仓库）
git clone https://github.com/aDarkMaker/AIGC.git
cd AIGC_Programme

# 方式2：直接下载解压
# 下载项目压缩包并解压到目标目录
```

### 第二步：创建 Python 虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 第三步：安装依赖包

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装RAG系统依赖
pip install -r vivo_rag_system/requirements.txt

# 安装Web界面依赖
pip install -r web_interface/requirements.txt

# 可选：安装训练模块依赖（需要更多资源）
pip install -r Law-Train/requirements.txt
# 训练模块需要再虚拟环境下安装！！！
```

### 第四步：初始化系统配置

```bash
# 初始化知识库（首次运行必需）
python vivo_rag_system/scripts/init_knowledge.py

# 验证安装（诊断系统状态）
python main.py --diagnose
```

### 第五步：测试基础功能（没有做好应用适配，不推荐使用）

```bash
# 测试命令行分析
echo "这是一份隐私政策测试文档。" > test.txt
python main.py -f test.txt -d privacy

# 测试交互式模式
python main.py -i
```

## 🌐 Web 界面部署与使用（推荐使用）

### 启动 Web 服务

```bash
# 进入Web界面目录
cd web_interface

# 启动Flask服务器
python server.py

# 服务器将在 http://127.0.0.1:5000 启动
```

### Web 界面功能

#### 🏠 主界面 (index.html)

- **分析类型选择**: 隐私条款、知识产权、合同条款
- **文件上传**: 支持 .txt, .doc, .docx 格式
- **文本输入**: 直接粘贴文本内容
- **专业知识库**: 可选启用增强分析功能
- **实时结果**: 关键词、摘要、法律分析、风险评估

#### 📖 使用说明页 (instructions.html)

- 详细的功能介绍和操作步骤
- 结果解释和注意事项
- 最佳实践建议

#### 🔒 隐私政策页 (privacy.html)

- 数据处理说明
- 用户权利保护
- 安全措施介绍

### Web 界面使用步骤

1. **打开浏览器**，访问 `http://127.0.0.1:5000`
2. **选择分析类型**：从下拉菜单选择适合的分析领域
3. **输入文本**：
   - 方式 1：点击"选择文件"上传文档
   - 方式 2：直接在文本框中粘贴内容
4. **配置选项**：根据需要启用"专业知识库"开关
5. **开始分析**：点击"开始分析"按钮
6. **查看结果**：
   - 关键词分析：重要法律术语提取
   - 文本摘要：内容概要生成
   - 法律分析：合规评估和专业建议
   - 风险评估：可视化风险等级显示

## 💻 命令行使用方法

### 基础命令

```bash
# 分析指定文件
python main.py -f 文档路径 -d 分析领域

# 交互式模式
python main.py -i

# 系统诊断
python main.py --diagnose

# 查看帮助
python main.py --help
```

### 分析领域选项

- `privacy`: 隐私政策分析
- `intellectual_property`: 知识产权分析
- `contract`: 合同条款分析

### 使用示例

```bash
# 分析隐私政策
python main.py -f privacy_policy.txt -d privacy

# 分析知识产权文档
python main.py -f ip_agreement.txt -d intellectual_property

# 分析合同条款
python main.py -f contract.txt -d contract

# 使用默认文件（Target.txt）
python main.py
```

## 🤖 API 服务部署

### 启动训练模块 API

```bash
cd Law-Train/src
python api_server.py

# API服务将在 http://127.0.0.1:8000 启动
# 访问 http://127.0.0.1:8000 查看API文档
```

### API 端点

- `GET /`: API 状态和文档界面
- `POST /query`: 法律文档查询接口

### API 使用示例

```python
import requests

# 查询法律条文
response = requests.post('http://127.0.0.1:8000/query',
                        json={'text': '个人信息保护相关法律'})
result = response.json()
print(result['results'])
```

## 🎓 模型训练指南

### 训练环境准备

```bash
# 检查训练环境
python main.py --diagnose

# 安装训练依赖（虚拟环境！！！）
Law-Train/train/Scripts/activate  # 激活虚拟环境
pip install -r Law-Train/requirements.txt
```

### 启动训练

```bash
# 命令行训练
python main.py --train --train-data 数据路径 --model-output 模型保存路径

# 傻瓜式直接训练
(train)python Law-Train/src/train.py

# 交互式训练
python main.py -i
# 选择选项3：训练模型
```

### 训练参数配置

- **批处理大小**: 默认 8，可调整为 4 或 2（内存不足时）
- **学习率**: 默认 2e-5
- **训练轮数**: 默认 3
- **最大序列长度**: 默认 512

### 训练监控

```bash
# 查看训练日志
tensorboard --logdir=logs

# 访问 http://localhost:6006 查看训练曲线
# 需要wandb支持（账号+token）
```

## 📊 输出结果说明

### 分析结果结构

```json
{
  "metadata": {
    "source_text_length": "文本长度",
    "analysis_domain": "分析领域",
    "analysis_timestamp": "分析时间"
  },
  "scoring_results": {
    "overall_score": "总分",
    "percentage_score": "百分比分数",
    "grade": "等级",
    "detailed_breakdown": "详细分数分解"
  },
  "rag_analysis": {
    "keywords": "关键词列表",
    "summary": "文本摘要",
    "context": "相关上下文"
  },
  "legal_analysis": {
    "compliance": "合规性评估",
    "risk_assessment": "风险评估",
    "applicable_laws": "适用法律"
  },
  "recommendations": {
    "improvement_suggestions": "改进建议",
    "priority_actions": "优先行动",
    "compliance_gaps": "合规缺口"
  }
}
```

### 评分体系

- **优秀 (90-100 分)**: 文档质量很高，符合行业标准
- **良好 (75-89 分)**: 文档质量较高，有小幅改进空间
- **合格 (60-74 分)**: 文档基本可用，建议进行改进
- **需要改进 (40-59 分)**: 文档存在明显不足
- **不合格 (0-39 分)**: 文档质量较差，需要重新制定

## 🚨 常见问题解决

### 依赖包问题

```bash
# 重新安装所有依赖
pip install --upgrade -r requirements.txt

# 清理pip缓存
pip cache purge
```

### 训练模块不可用

查看 `TRAINING_TROUBLESHOOTING.md` 文件获取详细的故障排除指南。

### Web 服务连接问题

```bash
# 检查端口占用
netstat -an | grep :5000

# 修改端口启动
python server.py --port 8080
```

### 内存不足问题

```bash
# 减少批处理大小
python main.py --train --batch-size 2

# 使用CPU训练
export CUDA_VISIBLE_DEVICES=""
```

## 🔧 配置文件说明

### 主配置文件

- `analysis_part/config.json`: 分析引擎配置
- `analysis_part/legal_config.json`: 法律术语配置
- `vivo_rag_system/config/settings.yaml`: RAG 系统配置

### 自定义配置

```json
// config.json 示例
{
  "KEYWORDS": ["隐私", "数据", "信息"],
  "CONFIDENCE_WEIGHTS": { "隐私": 1.0, "数据": 0.8 },
  "THRESHOLD": 0.7
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持与联系

- **技术支持**: 查看项目 Issues 页面
- **文档更新**: 持续更新中
- **版本历史**: 查看 Releases 页面

---

## 🎯 快速开始

如果您只想快速体验系统：

```bash
# 1. 安装基础依赖
pip install -r requirements.txt
pip install -r web_interface/requirements.txt

# 2. 启动Web界面
cd web_interface && python server.py

# 3. 打开浏览器访问 http://127.0.0.1:5000

# 4. 上传文档或输入文本，开始分析！
```

**LexGuard——律盾** 让法律文档分析变得简单、准确、高效！ 🏛️⚖️
