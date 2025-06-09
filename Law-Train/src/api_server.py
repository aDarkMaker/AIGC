from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from pathlib import Path
import json
import uvicorn
from pydantic import BaseModel
from contextlib import asynccontextmanager # 新增导入
from fastapi.staticfiles import StaticFiles

class Query(BaseModel):
    text: str

class LegalAdviser:
    def __init__(self, model_path, corpus_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"LegalAdviser: Using device: {self.device}") # 添加日志
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path).to(self.device)
        
        # 加载法律语料库
        print(f"LegalAdviser: Loading corpus from {corpus_path}") # 添加日志
        with open(corpus_path, 'r', encoding='utf-8') as f:
            self.corpus = json.load(f)
        print(f"LegalAdviser: Corpus loaded with {len(self.corpus)} documents.") # 添加日志
            
        # 预计算所有文档的嵌入
        print("LegalAdviser: Computing document embeddings...") # 添加日志
        self.doc_embeddings = self._compute_doc_embeddings()
        print(f"LegalAdviser: Document embeddings computed. Shape: {self.doc_embeddings.shape}") # 添加日志
        
    def _compute_doc_embeddings(self):
        embeddings = []
        for i, doc in enumerate(self.corpus):
            # text = f"{'/'.join(doc['hierarchy'])} {doc['title']}"
            # 使用更完整的文本进行嵌入，以获得更好的语义表示
            text = f"{'/'.join(doc['hierarchy'])} {doc['title']} {doc.get('content', '')[:512]}" # 限制内容长度
            inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512) # 明确最大长度
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embedding = outputs.last_hidden_state.mean(dim=1)
                embeddings.append(embedding)
            if (i + 1) % 100 == 0: # 添加进度日志
                print(f"LegalAdviser: Computed embeddings for {i+1}/{len(self.corpus)} documents.")
                
        return torch.cat(embeddings, dim=0)
        
    def get_relevant_laws(self, query, top_k=3):
        # 获取查询的嵌入
        inputs = self.tokenizer(query, return_tensors='pt', padding=True, truncation=True, max_length=512) # 明确最大长度
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            query_embedding = outputs.last_hidden_state.mean(dim=1)
            
        # 计算相似度
        similarities = F.cosine_similarity(query_embedding, self.doc_embeddings)
        top_indices = similarities.argsort(descending=True)[:top_k]
        
        # 返回最相关的法律条文
        results = []
        for idx in top_indices:
            doc = self.corpus[idx.item()]
            results.append({
                'title': doc['title'],
                'category': '/'.join(doc['hierarchy']),
                'content': doc.get('content', 'N/A'), # 使用 .get 以防 'content' 键不存在
                'similarity': similarities[idx].item()
            })
            
        return results

adviser: LegalAdviser = None # 类型提示

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时加载模型
    global adviser
    print("Lifespan: Application startup...") # 添加日志
    model_path = Path(__file__).parent.parent / 'model' / 'trained_model' # 指向训练后的模型
    corpus_path = Path(__file__).parent.parent / 'data' / 'processed' / 'legal_corpus.json'
    
    if not model_path.exists():
        print(f"Lifespan: Error - Model path does not exist: {model_path}")
        # 可以选择抛出异常或进行其他错误处理
    if not corpus_path.exists():
        print(f"Lifespan: Error - Corpus path does not exist: {corpus_path}")

    print(f"Lifespan: Initializing LegalAdviser with model_path: {model_path} and corpus_path: {corpus_path}")
    adviser = LegalAdviser(str(model_path), str(corpus_path))
    print("Lifespan: LegalAdviser initialized.") # 添加日志
    yield
    # 在应用关闭时清理资源 (如果需要)
    print("Lifespan: Application shutdown...") # 添加日志
    # adviser = None # 可选的清理

app = FastAPI(lifespan=lifespan) # 使用 lifespan

# 挂载静态文件目录，用于提供HTML/CSS/JS
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/") # 新增的健康检查接口
async def read_root():
    # return {"message": "Legal AI API is running"}
    # 修改为返回HTML页面
    return FileResponse(Path(__file__).parent / "api_ui.html")

@app.post("/query")
async def query_laws(query: Query):
    if adviser is None:
        return JSONResponse(content={"error": "Legal adviser not initialized. Please wait or check server logs."}, status_code=503)
    relevant_laws = adviser.get_relevant_laws(query.text)
    return JSONResponse(content={"results": relevant_laws})

if __name__ == "__main__":
    # 确保路径正确，特别是模型路径
    # model_dir_check = Path(__file__).parent.parent / 'model' / 'trained'
    # corpus_file_check = Path(__file__).parent.parent / 'data' / 'processed' / 'legal_corpus.json'
    # print(f"Checking model directory: {model_dir_check}, Exists: {model_dir_check.exists()}")
    # print(f"Checking corpus file: {corpus_file_check}, Exists: {corpus_file_check.exists()}")
    
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True) # 使用字符串导入应用，方便重载