import jieba.analyse
from snownlp import SnowNLP
import yaml

class TextProcessor:
    def __init__(self, config_path="./config/settings.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)
            model_config = config['model_config']
        
        self.keyword_topK = model_config['keyword_topK']
        self.summary_sentences = model_config['summary_sentences']
        
        # 加载停用词
        with open('./config/stopwords.txt',encoding='utf-8') as f:
            self.stopwords = set(f.read().splitlines())
        
        # 初始化结巴分词
        jieba.analyse.set_stop_words('./config/stopwords.txt')

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
            topK=self.keyword_topK,
            withWeight=False,
            allowPOS=('n', 'vn', 'v', 'ns', 'nr')
        )

    def generate_summary(self, text):
        """改进版摘要生成"""
        s = SnowNLP(text)
        return [sent for sent in s.summary(self.summary_sentences)]