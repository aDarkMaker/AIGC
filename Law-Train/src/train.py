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
    PrinterCallback
)
import torch
from torch.utils.data import Dataset
import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm
import logging
import sys

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
    def __init__(self, data_path, tokenizer, max_length=512):
        logging.info("正在加载数据集...")
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        logging.info(f"成功加载 {len(self.data)} 条法律文本")
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        text = f"{'/'.join(item['hierarchy'])} {item['title']} {item['content']}"
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
          # 为了序列分类任务，我们需要添加标签
        # 这里我们使用层级的深度作为简单的分类标签
        label = len(item['hierarchy'])
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label)
        }

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
    def train(self, train_dataset, output_dir, batch_size=8, num_epochs=3):
        logging.info("开始配置训练参数...")        # 设置环境变量来禁用 TensorFlow 警告
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        # 检测是否有GPU
        use_cuda = torch.cuda.is_available()
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            save_steps=1000,
            save_total_limit=2,
            logging_dir='./logs',
            logging_steps=10,
            report_to=["tensorboard"],
            remove_unused_columns=True,
            logging_first_step=True,
            logging_nan_inf_filter=True,
            save_strategy="steps",
            fp16=use_cuda,
            dataloader_num_workers=4 if use_cuda else 0,  # 只在GPU模式下使用多进程
            disable_tqdm=False,
            no_cuda=not use_cuda,
            use_mps_device=False,  # 禁用 MPS 设备
            dataloader_pin_memory=use_cuda  # 只在GPU模式下启用pin_memory
        )
        
        logging.info("正在初始化训练器...")
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,callbacks=[
                ProgressCallback(),
                PrinterCallback()
            ]
        )
        
        logging.info(f"开始训练 - 共 {num_epochs} 个 Epochs")
        with tqdm(total=num_epochs, desc="Training Progress") as pbar:
            trainer.train()
            pbar.update(1)
        
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