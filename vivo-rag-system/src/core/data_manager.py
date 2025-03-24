import chromadb
import os
import yaml

class VectorDBManager:
    def __init__(self, config_path="./config/settings.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # 新版客户端配置（持久化版本）
        self.client = chromadb.PersistentClient(
            path=config['storage']['vector_db_path']  # 直接使用配置文件中的路径
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