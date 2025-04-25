import jieba.analyse
from snownlp import SnowNLP
import yaml
import os
from pathlib import Path

class TextProcessor:
    def __init__(self):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        stopwords_path = package_root / "config" / "stopwords.txt"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        self.model_config = self.config.get('model_config', {})
        self.keyword_topk = self.model_config.get('keyword_topK', 5)
        self.summary_sentences = self.model_config.get('summary_sentences', 3)
        
        # 加载停用词
        with open(stopwords_path, encoding='utf-8') as f:
            self.stopwords = set(f.read().splitlines())
        
        # 初始化结巴分词
        jieba.analyse.set_stop_words(str(stopwords_path))

    def process(self, text):
        """完整文本处理流水线"""
        return {
            "raw_text": text,
            "keywords": self.extract_keywords(text),
            "summary": self.generate_summary(text),
            "query_text": self._build_retrieval_query(text)
        }

    def _build_retrieval_query(self, text):
        """构建RAG检索查询"""
        return f"为这个句子生成表示以用于检索相关文章：{text}"

    def extract_keywords(self, text):
        """增强版关键词提取"""
        return jieba.analyse.textrank(
            text, 
            topK=self.keyword_topk,
            withWeight=False,
            allowPOS=('n', 'vn', 'v', 'ns', 'nr')
        )

    def generate_summary(self, text):
        """改进版摘要生成"""
        s = SnowNLP(text)
        return [sent for sent in s.summary(self.summary_sentences)]