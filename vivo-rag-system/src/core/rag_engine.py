from .text_processor import TextProcessor  # 从当前包导入
from src.api.vivo_embedding import VivoEmbeddingAPI  # 绝对路径导入
from .data_manager import VectorDBManager  # 从当前包导入

class RAGEngine:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.embedding_api = VivoEmbeddingAPI()
        self.db_manager = VectorDBManager()

    def process_query(self, user_input):
        # 文本预处理
        processed = self.text_processor.process(user_input)
        
        # 获取查询向量
        query_embedding = self.embedding_api.get_embeddings(
            [processed['query_text']]
        )[0]
        
        # 检索相关文档
        retrieved = self.db_manager.retrieve_similar(query_embedding)
        
        # 构建增强上下文
        context = "\n".join(
            [f"相关文档 {i+1}: {doc[0]}\n关键词: {', '.join(doc[1]['keywords'])}" 
             for i, doc in enumerate(retrieved)]
        )
        
        # 生成最终输出（此处可接入LLM）
        return {
            "keywords": processed['keywords'],
            "summary": processed['summary'],
            "context": context
        }