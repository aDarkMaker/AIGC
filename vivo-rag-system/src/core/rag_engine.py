from .text_processor import TextProcessor
from src.api.vivo_embedding import VivoEmbeddingAPI
from .data_manager import VectorDBManager

class RAGEngine:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.embedding_api = VivoEmbeddingAPI()
        self.db_manager = VectorDBManager()

    def process_query(self, user_input):
        # 合并预处理和向量获取步骤
        processed = self.text_processor.process(user_input)
        query_embedding = self.embedding_api.get_embeddings([processed['query_text']])[0]
        
        # 优化上下文构建过程
        context_items = (
            f"相关文档 {i+1}: {content}\n关键词: {', '.join(metadata['keywords'])}"
            for i, (content, metadata) in enumerate(
                self.db_manager.retrieve_similar(query_embedding)
            )
        )
        
        return {
            "keywords": processed['keywords'],
            "summary": processed['summary'],
            "context": "\n".join(context_items)
        }