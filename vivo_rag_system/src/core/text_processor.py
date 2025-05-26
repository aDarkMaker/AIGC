import jieba.analyse
from snownlp import SnowNLP
import yaml
import os
from pathlib import Path
import re # 新增导入

class TextProcessor:
    def __init__(self):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        stopwords_path = package_root / "config" / "stopwords.txt"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        self.model_config = self.config.get('model_config', {})
        self.keyword_topk = self.model_config.get('keyword_topK', 10) # 增加关键词数量
        self.summary_sentences = self.model_config.get('summary_sentences', 5) # 增加摘要句子数量
        
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
        # 增加更多法律相关的词性，如 'nz' (其他专名), 'j' (简称略语)
        # 'n', 'vn', 'v', 'ns', 'nr', 'nz', 'j'
        # 调整 allowPOS 以包含更多可能相关的词性
        return jieba.analyse.textrank(
            text, 
            topK=self.keyword_topk,
            withWeight=False, # 暂时不输出权重，按需开启
            allowPOS=('n', 'vn', 'v', 'ns', 'nr', 'nz', 'j', 'l', 'i') # l:成语, i:习用语
        )    
        
    def generate_summary(self, text, num_sentences=None):
        """法律文本专业摘要生成器
        
        此方法使用改进的抽取式摘要算法，专门针对法律文本特点进行了优化：
        1. 精确的分句处理，支持法律文本常见的标点符号
        2. 专业术语权重加权
        3. 多维度句子重要性评分
        4. 上下文连贯性优化
        5. 关键法律结构识别
        """
        if num_sentences is None:
            num_sentences = self.summary_sentences

        if not text:
            return []        # 1. 增强版分句处理
        # 使用正则表达式保留标点符号
        pattern = r'([^。？！；：]*[。？！；：])'
        sentences = re.findall(pattern, text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]  # 过滤过短的句子

        if not sentences:
            return []

        # 2. 获取文档关键词与专业术语
        # 使用更大的topK值以获取更全面的关键词覆盖
        doc_keywords = jieba.analyse.textrank(text, topK=self.keyword_topk * 3, withWeight=True)
        
        # 3. 多维度句子评分
        sentence_scores = []
        prev_score = 0  # 用于追踪上一个句子的分数，实现平滑过渡
        
        for i, sentence in enumerate(sentences):
            # 基础分数初始化
            score = 0
            length_score = min(1.0, len(sentence) / 100)  # 句子长度标准化得分
            position_score = 1.0 / (i/len(sentences) + 1)  # 位置得分，越靠前越重要
            
            # 关键词匹配得分
            keyword_score = 0
            for keyword, weight in doc_keywords:
                if keyword in sentence:
                    keyword_score += weight  # 使用TextRank给出的权重
            
            # 特定法律文本结构识别分数
            structure_score = 0
            if re.search(r'(本|该|此)(协议|政策|合同|声明)', sentence):
                structure_score += 0.5
            if re.search(r'(我们|您|用户)(应当|必须|可以|有权|承诺)', sentence):
                structure_score += 0.3
                
            # 整合多个维度的分数
            total_score = (
                keyword_score * 0.4 +  # 关键词权重
                position_score * 0.2 +  # 位置权重
                length_score * 0.2 +    # 长度权重
                structure_score * 0.2    # 结构权重
            )
            
            # 平滑处理，考虑上下文连贯性
            if i > 0:
                total_score = 0.7 * total_score + 0.3 * prev_score
            
            sentence_scores.append((total_score, i, sentence))
            prev_score = total_score

        # 4. 智能句子筛选
        # 按分数排序，但同时考虑句子的原始顺序
        sorted_sentences = sorted(sentence_scores, key=lambda x: x[0], reverse=True)
        
        # 初步选择得分最高的句子
        candidates = sorted_sentences[:num_sentences * 2]
        
        # 按原文顺序重排，并确保首句必选
        final_sentences = []
        if candidates:
            # 确保包含文档第一句话（通常包含重要上下文）
            first_sent = next((s for s in candidates if s[1] == 0), None)
            if first_sent:
                final_sentences.append(first_sent)
            # 添加其他重要句子，保持原文顺序
            for score, idx, sent in sorted(candidates, key=lambda x: x[1]):
                if len(final_sentences) < num_sentences and (score, idx, sent) not in final_sentences:
                    final_sentences.append((score, idx, sent))
        
        # 5. 生成初步摘要
        raw_summary = [sent for _, _, sent in sorted(final_sentences, key=lambda x: x[1])]
        
        # 如果摘要生成失败，使用备选方案
        if not raw_summary and len(sentences) > 0:
            s = SnowNLP(text)
            raw_summary = [sent for sent in s.summary(num_sentences)]
            
        # 6. 使用大模型优化摘要语言
        if raw_summary:
            return self._refine_summary_language(raw_summary)
        return []
    
    def _refine_summary_language(self, raw_summary):
        """使用大模型优化摘要语言
        
        对生成的初步摘要进行语言组织和优化，确保：
        1. 语言更加严谨、专业
        2. 句子之间的连贯性
        3. 符合法律文本的表达习惯
        4. 保持文本的客观性和准确性
        """
        from ..api.vivo_llm import VivoLLMAPI
        
        try:
            # 初始化API
            llm_api = VivoLLMAPI()
              # 将初步摘要组合成文本，确保每个句子都有标点符号
            summary_text = "".join([sent if sent.strip()[-1] in "。？！；：" else sent + "。" for sent in raw_summary])
            
            # 调用API优化摘要
            optimized_text = llm_api.optimize_summary(summary_text)
              # 将优化后的文本按标点符号拆分，保留标点
            pattern = r'([^。？！；：]*[。？！；：])'
            refined_summary = re.findall(pattern, optimized_text)
            
            # 如果优化后的摘要为空，返回原始摘要
            return refined_summary if refined_summary else raw_summary
            
        except Exception as e:
            print(f"摘要语言优化失败: {str(e)}")
            return raw_summary