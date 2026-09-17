from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import QueryRequest, ImpactRequest
from .indexer import CodeIndexer
from .rag import RAGEngine
from .evaluator import evaluate_retrieval

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR / "sample_repo"

indexer = CodeIndexer(REPO_DIR)
indexer.build()
rag = RAGEngine(indexer)

app = FastAPI(
    title="CodeRAG API",
    description="AI-powered codebase intelligence demo",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "CodeRAG", "status": "running", "files": len(indexer.files)}

@app.get("/api/repository")
def repository():
    return {
        "files": indexer.files,
        "chunks": len(indexer.chunks),
        "symbols": indexer.symbols,
        "graph": indexer.graph,
    }

@app.post("/api/index")
def rebuild_index():
    indexer.build()
    return {"message": "Repository indexed", "files": len(indexer.files), "chunks": len(indexer.chunks)}

@app.post("/api/query")
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return rag.answer(request.question, request.top_k)

@app.post("/api/impact")
def impact(request: ImpactRequest):
    if not request.target.strip():
        raise HTTPException(status_code=400, detail="Target cannot be empty")
    return indexer.impact_analysis(request.target)

@app.get("/api/evaluate")
def evaluate():
    return evaluate_retrieval(rag)

@app.get("/api/health")
def health():
    return {"ok": True}
