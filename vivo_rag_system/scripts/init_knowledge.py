import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from src.core import TextProcessor, VectorDBManager
from src.api import VivoEmbeddingAPI

def init_knowledge():
    processor = TextProcessor()
    api = VivoEmbeddingAPI()
    db = VectorDBManager()
    
    # 加载知识库文档
    knowledge_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base") # Corrected path
    print(f"[DEBUG init_knowledge] Knowledge base path: {knowledge_path}")
    for filename in os.listdir(knowledge_path):
        print(f"[DEBUG init_knowledge] Processing file: {filename}")
        with open(os.path.join(knowledge_path, filename), encoding='utf-8') as f: # Added encoding
            text = f.read()
            print(f"[DEBUG init_knowledge] Text extracted: {text[:100]}...") # Print first 100 chars
            processed = processor.process(text)
            print(f"[DEBUG init_knowledge] Processed text for embedding: {processed['query_text'][:100]}...")
            print(f"[DEBUG init_knowledge] Keywords: {processed['keywords']}")
            
            # 获取嵌入向量
            embeddings = api.get_embeddings([processed['query_text']])
            print(f"[DEBUG init_knowledge] Embeddings received (first 5 values of first embedding): {embeddings[0][:5] if embeddings and embeddings[0] else 'No embeddings'}")
            
            # 将关键字列表转换为逗号分隔的字符串以符合ChromaDB的要求
            keywords_str = ", ".join(processed['keywords'])
            print(f"[DEBUG init_knowledge] Keywords string for metadata: {keywords_str}")

            # 存储元数据
            db.add_documents(
                documents=[text],
                embeddings=embeddings,
                metadata=[{
                    "keywords": keywords_str, # 使用转换后的字符串
                    "source": filename
                }]
            )

if __name__ == "__main__":
    init_knowledge()
    print("[INFO init_knowledge] Knowledge base initialization process finished.")