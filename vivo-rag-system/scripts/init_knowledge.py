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
    knowledge_path = "./data/knowledge_base"
    for filename in os.listdir(knowledge_path):
        with open(os.path.join(knowledge_path, filename)) as f:
            text = f.read()
            processed = processor.process(text)
            
            # 获取嵌入向量
            embeddings = api.get_embeddings([processed['query_text']])
            
            # 存储元数据
            db.add_documents(
                documents=[text],
                embeddings=embeddings,
                metadata=[{
                    "keywords": processed['keywords'],
                    "source": filename
                }]
            )