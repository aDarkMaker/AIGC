from .text_processor import TextProcessor
from ..api.vivo_embedding import VivoEmbeddingAPI
from .data_manager import VectorDBManager

class RAGEngine:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.embedding_api = VivoEmbeddingAPI()
        self.db_manager = VectorDBManager()
        # 假设专业知识库有独立的向量数据库管理器
        # self.pro_db_manager = VectorDBManager(db_path='path_to_professional_db') # 您需要配置正确的路径

    def process_query(self, user_input, use_professional_kb: bool = False):
        # 合并预处理和向量获取步骤
        processed = self.text_processor.process(user_input)
        query_embedding = self.embedding_api.get_embeddings([processed['query_text']])[0]
        
        retrieved_items = []
        if use_professional_kb:
            # 此处调用专业知识库的检索逻辑
            # retrieved_items = self.pro_db_manager.retrieve_similar(query_embedding)
            # 暂时使用普通知识库作为占位符，您需要替换为专业知识库的实际调用
            print("[DEBUG] Using Professional Knowledge Base (Placeholder)")
            retrieved_items = self.db_manager.retrieve_similar(query_embedding)
        else:
            retrieved_items = self.db_manager.retrieve_similar(query_embedding)

        # 优化上下文构建过程
        context_items = (
            f"相关文档 {i+1}: {content}\n关键词: {', '.join(metadata['keywords'])}"
            for i, (content, metadata) in enumerate(retrieved_items)
        )
        
        return {
            "keywords": processed['keywords'],
            "summary": processed['summary'],
            "context": "\n".join(context_items)
        }