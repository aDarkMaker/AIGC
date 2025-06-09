import yaml
from pathlib import Path
import chromadb
import os

class VectorDBManager:
    def __init__(self, db_path=None, collection_name="knowledge_embeddings"):
        # 获取vivo_rag_system包的根目录
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / "config" / "settings.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        storage_config = self.config.get('storage', {})
        knowledge_base_config_path = storage_config.get('knowledge_base', './data/knowledge_base') # Renamed to avoid conflict
        
        # 将相对路径转换为绝对路径
        if db_path is None:
            # Corrected path: remove one level of ".." to avoid going into src
            # self.db_path = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "chroma_db")
            # Should be:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # This should point to vivo_rag_system
            self.db_path = os.path.join(base_path, "data", "vector_store", "chroma_db")
        else:
            self.db_path = db_path
        
        print(f"[DEBUG VectorDBManager __init__] Resolved DB path: {self.db_path}")
        
        self.knowledge_base = str(package_root / knowledge_base_config_path.lstrip('./'))  # 转换为字符串
        
        # 新版客户端配置（持久化版本）
        self.client = chromadb.PersistentClient(
            path=self.db_path  # 使用字符串类型的路径
        )
        self.collection_name = collection_name # Assignment of self.collection_name
        print(f"[DEBUG VectorDBManager __init__] Using collection_name: {self.collection_name}") # Moved this line after assignment
        
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"[DEBUG VectorDBManager __init__] Successfully got collection '{self.collection_name}'. Count: {self.collection.count()}")
        except Exception as e:
            print(f"[DEBUG VectorDBManager] Collection '{self.collection_name}' not found, creating it. Error: {e}")
            self.collection = self.client.create_collection(name=self.collection_name)
            print(f"[DEBUG VectorDBManager] Collection '{self.collection_name}' created. Count: {self.collection.count()}")

    def add_documents(self, documents, embeddings, metadata):
        """添加文档到向量数据库"""
        if not documents:
            print("[WARNING VectorDBManager] add_documents called with empty documents list. Skipping.")
            return

        print(f"[DEBUG VectorDBManager] Attempting to add {len(documents)} documents.")
        print(f"[DEBUG VectorDBManager] First document (first 100 chars): {documents[0][:100] if documents else 'N/A'}")
        print(f"[DEBUG VectorDBManager] Number of embeddings: {len(embeddings)}")
        print(f"[DEBUG VectorDBManager] First embedding (first 5 values): {embeddings[0][:5] if embeddings and embeddings[0] else 'N/A'}")
        print(f"[DEBUG VectorDBManager] Number of metadata entries: {len(metadata)}")
        print(f"[DEBUG VectorDBManager] First metadata entry: {metadata[0] if metadata else 'N/A'}")

        ids = [f"doc_{i}" for i in range(len(documents))] # Simple ID generation, ensure this is robust enough or matches your ID strategy
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids
            )
            print(f"[INFO VectorDBManager] Successfully added {len(documents)} documents to collection '{self.collection_name}'. New count: {self.collection.count()}")
        except Exception as e:
            print(f"[ERROR VectorDBManager] Failed to add documents to collection '{self.collection_name}': {e}")
        # 新版会自动持久化，无需手动调用persist()

    def retrieve_similar(self, query_embedding, top_k=3):
        """相似性检索"""
        print(f"[DEBUG VectorDBManager] Attempting to retrieve similar for query_embedding (type: {type(query_embedding)}, first 5 elements: {query_embedding[:5] if query_embedding and len(query_embedding) > 5 else 'N/A or too short'}) with top_k={top_k}")
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            print(f"[DEBUG VectorDBManager] Raw query results from ChromaDB: {results}")

            if not results or not results.get('documents') or not results['documents'][0]:
                print("[INFO VectorDBManager] ChromaDB query returned no documents.")
                return zip([], [], []) # Return empty iterators

            # 确保所有返回的列表长度一致
            num_docs = len(results['documents'][0])
            metadatas = results['metadatas'][0] if results.get('metadatas') and results['metadatas'] else [None] * num_docs
            distances = results['distances'][0] if results.get('distances') and results['distances'] else [None] * num_docs

            if len(metadatas) != num_docs:
                print(f"[WARNING VectorDBManager] Mismatch in length of documents ({num_docs}) and metadatas ({len(metadatas)}). Padding metadatas.")
                metadatas = (list(metadatas) + [None] * num_docs)[:num_docs]
            if len(distances) != num_docs:
                print(f"[WARNING VectorDBManager] Mismatch in length of documents ({num_docs}) and distances ({len(distances)}). Padding distances.")
                distances = (list(distances) + [None] * num_docs)[:num_docs]

            retrieved_data = list(zip(
                results['documents'][0],
                metadatas,
                distances
            ))
            print(f"[DEBUG VectorDBManager] Processed retrieved data (length {len(retrieved_data)}): {retrieved_data}")
            return iter(retrieved_data) # 返回迭代器以匹配 RAG Engine 的期望

        except Exception as e:
            print(f"[ERROR VectorDBManager] Error during ChromaDB query: {e}")
            return zip([], [], []) # Return empty iterators