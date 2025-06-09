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

    def process_query(self, user_input, use_professional_kb: bool = True):
        # 合并预处理和向量获取步骤
        processed = self.text_processor.process(user_input)
        query_embedding = self.embedding_api.get_embeddings([processed['query_text']])[0]
        
        retrieved_items_iterator = [] # 初始化
        if use_professional_kb:
            # 此处调用专业知识库的检索逻辑
            # retrieved_items = self.pro_db_manager.retrieve_similar(query_embedding)
            # 暂时使用普通知识库作为占位符，您需要替换为专业知识库的实际调用
            print("[DEBUG RAGEngine] Using Professional Knowledge Base (Placeholder - actually using default DB manager)")
            retrieved_items_iterator = self.db_manager.retrieve_similar(query_embedding)
        else:
            print("[DEBUG RAGEngine] Using Default Knowledge Base")
            retrieved_items_iterator = self.db_manager.retrieve_similar(query_embedding)

        # 将迭代器转换为列表进行处理和调试
        try:
            # retrieve_similar 返回 zip 对象，list() 会消耗它。
            # 如果需要多次迭代，应在此处处理或重新查询。
            retrieved_items_list = list(retrieved_items_iterator)
        except Exception as e:
            print(f"[ERROR RAGEngine] Failed to convert retrieved_items_iterator to list: {e}")
            retrieved_items_list = []

        print(f"[DEBUG RAGEngine] Retrieved items list (length {len(retrieved_items_list)}): {retrieved_items_list}")

        context_list = []
        if not retrieved_items_list:
            print("[INFO RAGEngine] No items retrieved from vector database.")
        else: # 确保后续代码在有检索结果时才执行
            for i, item_tuple in enumerate(retrieved_items_list):
                if not item_tuple or len(item_tuple) < 2: # 确保元组有效且至少有两个元素 (content, metadata)
                    print(f"[WARNING RAGEngine] Invalid or incomplete item in retrieved_items_list at index {i}: {item_tuple}")
                    continue

                content = item_tuple[0]
                metadata = item_tuple[1]
                # distance = item_tuple[2] if len(item_tuple) > 2 else None # 可选的距离

                content_text = ""
                if content is None:
                    content_text = "内容为空"
                    print(f"[WARNING RAGEngine] Content is None for retrieved item {i+1}")
                elif not str(content).strip():
                    content_text = "内容为空白"
                    print(f"[WARNING RAGEngine] Content is blank for retrieved item {i+1}")
                else:
                    content_text = str(content)

                keywords_str = "无可用关键词"
                if metadata and isinstance(metadata, dict) and 'keywords' in metadata and metadata['keywords']:
                    current_keywords = metadata['keywords']
                    if isinstance(current_keywords, list):
                        # 过滤掉 None 或空字符串的关键词
                        valid_keywords = [kw for kw in current_keywords if kw and str(kw).strip()]
                        if valid_keywords:
                            keywords_str = ', '.join(valid_keywords)
                    elif isinstance(current_keywords, str) and current_keywords.strip():
                        keywords_str = current_keywords
                
                context_list.append(f"相关文档 {i+1}: {content_text}\\n关键词: {keywords_str}")

        final_context = "\\n".join(context_list)
        
        if not final_context.strip():
            print("[INFO RAGEngine] Final context is empty or blank after processing all retrieved items.")
            # 可以考虑在这里返回一个默认的提示信息，或者让 legal_analyzer 处理空上下文
            # final_context = "未能从知识库中检索到相关内容。"

        return {
            "keywords": processed['keywords'],
            "summary": processed['summary'],
            "context": final_context
        }