# Law-Train src package
"""
法律文本训练模块

包含:
- LegalBertTrainer: 法律BERT模型训练器
- LegalCorpusDataset: 法律语料数据集
"""

__version__ = "1.0.0"
__author__ = "LexGuard Team"

# 导入主要类
try:
    from .train import LegalBertTrainer, LegalCorpusDataset
    __all__ = ['LegalBertTrainer', 'LegalCorpusDataset']
except ImportError as e:
    print(f"警告: 无法导入训练模块 - {e}")
    __all__ = []
