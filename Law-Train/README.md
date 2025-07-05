Target:
https://flk.npc.gov.cn/fl.html

待完成：done

1. 爬取所有法律条文
2. 训练模型
3. 结合 RAG 模型
4. 进行专业优化@analysis_part

项目架构：
DATA(存储训练用数据)
Model(存放训练好模型)
Src(存放训练代码)

todo:

1. RAG 分析器接入训练好的 model
2. 重新定义打分器
3. 优化检索

# How to Use (本地训练指南)

1. 环境配置

---

```bash
# 创建并激活虚拟环境
python -m venv train
.\train\Scripts\activate  # Windows
source train/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

2. 数据准备

---

- 确保 `data/processed/` 目录下存在 `legal_corpus.json` 文件
- 如需重新处理数据，运行：

```bash
python data/data_processor.py
```

3. 模型训练

---

```bash
# 进入src目录
cd src

# 开始训练
python train.py
```

- 训练日志将保存在 `training.log`
- 训练过程可通过 TensorBoard 监控：

```bash
tensorboard --logdir=logs
```

4. 模型输出

---

- 训练好的模型将保存在 `model/trained_model/` 目录下
- 预训练模型缓存在 `model/pretrained/` 目录下

5. 系统要求

---

- Python 3.8+
- CUDA 支持（推荐使用 GPU 训练）
- 至少 8GB 内存（推荐 16GB 以上）
- 磁盘空间：约 10GB（包含模型和数据）

6. 注意事项

---

- 首次运行会自动下载预训练模型，请确保网络连接稳定
- 如遇到 CUDA 相关错误，请检查 CUDA 和 PyTorch 版本是否匹配
- 训练过程可能需要几小时到几天，具体取决于硬件配置

7. 故障排除

---

如遇到问题，请检查：

1. 虚拟环境是否正确激活
2. 所有依赖是否正确安装
3. CUDA 是否可用（使用`torch.cuda.is_available()`验证）
4. 日志文件中的具体错误信息
