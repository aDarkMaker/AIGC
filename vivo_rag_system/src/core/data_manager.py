import yaml
from pathlib import Path
import chromadb

class VectorDBManager:
    def __init__(self):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        storage_config = self.config.get('storage', {})
        db_path = storage_config.get('vector_db_path', './data/vector_store/chroma_db')
        knowledge_base = storage_config.get('knowledge_base', './data/knowledge_base')
        
        # 将相对路径转换为绝对路径
        self.db_path = str(package_root / db_path.lstrip('./'))  # 转换为字符串
        self.knowledge_base = str(package_root / knowledge_base.lstrip('./'))  # 转换为字符串
        
        # 新版客户端配置（持久化版本）
        self.client = chromadb.PersistentClient(
            path=self.db_path  # 使用字符串类型的路径
        )
        
        # 创建/获取集合（新增embedding_function参数）
        self.collection = self.client.get_or_create_collection(
            name="knowledge_embeddings",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents, embeddings, metadata):
        """添加文档到向量数据库"""
        ids = [f"doc_{i}" for i in range(len(documents))]
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadata,
            ids=ids
        )
        # 新版会自动持久化，无需手动调用persist()

    def retrieve_similar(self, query_embedding, top_k=3):
        """相似性检索"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        return zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )