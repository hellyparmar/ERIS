"""
R-DIOS AI Assistant API (RAG-based)
POST /api/v1/assistant/chat    — ask a question
POST /api/v1/assistant/ingest  — rebuild knowledge base from live data
GET  /api/v1/assistant/status  — check RAG system availability
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.core.rag import rag_engine
from app.models.schema import User, Outlet

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str
    include_outlet_context: bool = True


@router.post("/chat")
async def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask the RAG-based AI assistant a question about the business."""
    outlet_name = None
    if current_user.outlet_id and body.include_outlet_context:
        result = await db.execute(select(Outlet).where(Outlet.id == current_user.outlet_id))
        outlet = result.scalar_one_or_none()
        outlet_name = outlet.name if outlet else None

    result = rag_engine.query(body.message, db=db, outlet_name=outlet_name)
    return {
        "question": body.message,
        "answer": result["answer"],
        "rag_enabled": result["rag_enabled"],
        "sources_used": result["sources_used"],
        "user_role": current_user.role,
        "outlet_context": outlet_name,
    }


@router.post("/ingest")
async def ingest_knowledge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rebuild the RAG knowledge base from current database. Admin/manager only."""
    count = rag_engine.ingest_business_context(db)
    return {"message": f"Knowledge base updated with {count} documents", "documents_indexed": count}


@router.get("/status")
async def rag_status():
    """Check RAG system availability."""
    import requests as req
    ollama_ok = False
    try:
        r = req.get("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = r.ok
    except Exception:
        pass

    chroma_ok = False
    try:
        import chromadb
        chroma_ok = True
    except ImportError:
        pass

    return {"rag_available": rag_engine._initialized, "ollama_available": ollama_ok, "chromadb_available": chroma_ok}
