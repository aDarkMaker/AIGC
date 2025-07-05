# 训练模块故障排除指南

## 问题：训练模块不可用

如果您看到 "⚠️ 警告: 训练模块不可用" 的消息，请按以下步骤排查：

### 1. 诊断环境

```bash
python main.py --diagnose
```

### 2. 检查依赖包

确保已安装所有必需的包：

```bash
pip install -r requirements.txt
pip install -r Law-Train/requirements.txt
```

### 3. 验证文件结构

确保以下文件存在：

```
Law-Train/
├── __init__.py
├── requirements.txt
└── src/
    ├── __init__.py
    └── train.py
```

### 4. 手动测试导入

在项目根目录运行 Python：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "Law-Train"))
from src.train import LegalBertTrainer, LegalCorpusDataset
```

### 5. 常见问题解决

#### 问题 1: ModuleNotFoundError: No module named 'torch'

解决方案：

```bash
pip install torch transformers
```

#### 问题 2: CUDA 相关错误

解决方案：

- 如果没有 GPU，确保安装 CPU 版本的 PyTorch
- 如果有 GPU，确保 CUDA 版本与 PyTorch 版本匹配

#### 问题 3: 内存不足

解决方案：

- 减少 batch_size (默认为 8，可降至 4 或 2)
- 使用混合精度训练

### 6. 联系支持

如果问题仍然存在，请：

1. 运行诊断命令并保存输出
2. 检查详细错误信息
3. 确认 Python 版本 (建议 3.8+)

### 7. 最小可用配置

如果仅需要分析功能，可以在没有训练模块的情况下使用：

```bash
python main.py -i  # 选择选项1或2进行分析
```
