import os
import warnings
# 禁用不相关的警告
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from transformers import (
    AutoTokenizer, 
    AutoModel,
    AutoModelForSequenceClassification,
    TrainingArguments, 
    Trainer,
    ProgressCallback,
    PrinterCallback,
    get_linear_schedule_with_warmup,
    EarlyStoppingCallback
)
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from tqdm.auto import tqdm
import logging
import sys
import jieba
import re
import wandb
from typing import Dict, List, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training.log', encoding='utf-8')
    ]
)

# 确保控制台输出也使用UTF-8编码
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

class LegalCorpusDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_length=512, augment=False):
        logging.info("正在加载数据集...")
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        logging.info(f"成功加载 {len(self.data)} 条法律文本")
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.augment = augment
        
        # 预处理法律术语
        self.legal_terms = self._load_legal_terms()
        
    def _load_legal_terms(self):
        """加载常用法律术语"""
        try:
            legal_terms_path = Path(__file__).parent.parent / 'analysis_part' / 'legal_terms.txt'
            if legal_terms_path.exists():
                with open(legal_terms_path, 'r', encoding='utf-8') as f:
                    return set(line.strip() for line in f if line.strip())
        except:
            pass
        return set()
        
    def _preprocess_text(self, text):
        """预处理文本"""
        # 清理特殊字符
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：""''（）【】《》、]', '', text)
        
        # 基础数据增强
        if self.augment and np.random.random() < 0.3:
            words = list(jieba.cut(text))
            if len(words) > 1:
                # 随机交换相邻词语
                idx = np.random.randint(0, len(words) - 1)
                words[idx], words[idx + 1] = words[idx + 1], words[idx]
                text = ''.join(words)
        
        return text
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # 构建更丰富的文本特征
        hierarchy_text = '/'.join(item['hierarchy'])
        title = item['title']
        content = item['content']
        
        # 预处理文本
        text = self._preprocess_text(f"{hierarchy_text} {title} {content}")
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # 改进标签生成策略
        hierarchy_depth = len(item['hierarchy'])
        
        # 计算风险评分（基于内容特征）
        risk_score = self._calculate_risk_score(content)
        
        # 计算合规评分
        compliance_score = self._calculate_compliance_score(content)
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(min(hierarchy_depth, 9)),  # 限制在0-9范围
            'risk_score': torch.tensor(risk_score, dtype=torch.float),
            'compliance_score': torch.tensor(compliance_score, dtype=torch.float)
        }
        
    def _calculate_risk_score(self, content):
        """计算风险评分"""
        risk_keywords = ['处罚', '违法', '违规', '禁止', '限制', '责任', '赔偿', '罚款']
        score = 0.0
        for keyword in risk_keywords:
            if keyword in content:
                score += 0.1
        return min(score, 1.0)
        
    def _calculate_compliance_score(self, content):
        """计算合规评分"""
        compliance_keywords = ['合规', '规范', '标准', '要求', '应当', '必须', '规定']
        score = 0.0
        for keyword in compliance_keywords:
            if keyword in content:
                score += 0.1
        return min(score, 1.0)

class LegalBertTrainer:
    def __init__(self, model_name='bert-base-chinese', num_labels=10):
        logging.info(f"正在加载预训练模型: {model_name}")
        # 设置模型存储路径
        model_dir = Path(__file__).parent.parent / 'model' / 'pretrained'
        model_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 尝试从本地加载
            logging.info("尝试从本地加载预训练模型...")
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(model_dir),
                num_labels=num_labels
            )
            logging.info("成功从本地加载预训练模型")
        except Exception as e:
            # 如果本地没有，则从远程下载并保存
            logging.info(f"本地模型不存在，从远程下载预训练模型: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=num_labels
            )
            
            # 保存到本地
            logging.info("保存预训练模型到本地...")
            self.tokenizer.save_pretrained(str(model_dir))
            self.model.save_pretrained(str(model_dir))
            logging.info("预训练模型已保存到本地")
            
        logging.info("模型加载完成")
    def train(self, train_dataset, output_dir, batch_size=8, num_epochs=3, learning_rate=2e-5):
        logging.info("开始配置训练参数...")
        # 设置环境变量来禁用 TensorFlow 警告
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        # 检测是否有GPU
        use_cuda = torch.cuda.is_available()
        
        # 数据分割为训练集和验证集
        train_size = int(0.8 * len(train_dataset))
        val_size = len(train_dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            train_dataset, [train_size, val_size]
        )
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=500,
            weight_decay=0.01,
            save_steps=1000,
            save_total_limit=3,
            evaluation_strategy="steps",
            eval_steps=500,
            logging_dir='./logs',
            logging_steps=50,
            report_to=["tensorboard", "wandb"] if wandb.run else ["tensorboard"],
            remove_unused_columns=True,
            logging_first_step=True,
            logging_nan_inf_filter=True,
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=use_cuda,
            dataloader_num_workers=4 if use_cuda else 0,
            disable_tqdm=False,
            no_cuda=not use_cuda,
            use_mps_device=False,
            dataloader_pin_memory=use_cuda
        )
        
        # 自定义评估函数
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            
            accuracy = accuracy_score(labels, predictions)
            precision, recall, f1, _ = precision_recall_fscore_support(
                labels, predictions, average='weighted'
            )
            
            return {
                'accuracy': accuracy,
                'f1': f1,
                'precision': precision,
                'recall': recall
            }
        
        logging.info("正在初始化训练器...")
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
            callbacks=[
                EarlyStoppingCallback(early_stopping_patience=3),
                ProgressCallback(),
                PrinterCallback()
            ]
        )
        
        # 初始化wandb（如果可用）
        try:
            wandb.init(
                project="legal-bert-training",
                config={
                    "batch_size": batch_size,
                    "num_epochs": num_epochs,
                    "learning_rate": learning_rate
                }
            )
        except:
            logging.info("WandB不可用，跳过在线监控")
        
        logging.info(f"开始训练 - 共 {num_epochs} 个 Epochs")
        with tqdm(total=num_epochs, desc="Training Progress") as pbar:
            trainer.train()
            pbar.update(1)
        
        # 在验证集上进行最终评估
        eval_results = trainer.evaluate()
        logging.info(f"验证集评估结果: {eval_results}")
        
        logging.info("训练完成！")
        
    def save_model(self, output_dir):
        logging.info("正在保存模型...")
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        logging.info(f"模型已保存至: {output_dir}")

if __name__ == '__main__':
    try:
        logging.info("=== 法律文本模型训练开始 ===")
        
        # 设置路径
        data_path = Path(__file__).parent.parent / 'data/processed/legal_corpus.json'
        model_output_dir = Path(__file__).parent.parent / 'model' / 'trained_model'
        
        # 检查CUDA可用性
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"使用设备: {device}")
        
        # 初始化训练器
        trainer = LegalBertTrainer()
        
        # 准备数据集
        dataset = LegalCorpusDataset(data_path, trainer.tokenizer)
        
        # 训练模型
        trainer.train(dataset, str(model_output_dir))
        
        # 保存模型
        trainer.save_model(str(model_output_dir))
        
        logging.info("=== 训练流程已完成 ===")
        
    except Exception as e:
        logging.error(f"训练过程中发生错误: {str(e)}", exc_info=True)
        raise