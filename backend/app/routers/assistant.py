from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from app.ml.assistant.llm_provider import llm
from app.config import settings
from app.middleware.auth import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.multitenant_models import User
import logging

logger = logging.getLogger(__name__)

from app.schemas.assistant import ChatRequest, ChatResponse, AssistantStatusResponse
from app.ml.assistant.agent import retail_agent

router = APIRouter(prefix="/api/v1/assistant", tags=["AI Assistant"])

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat(request: ChatRequest, req: Request, current_user: User = Depends(get_current_user)):
    """
    Interact with the Enterprise Retail Intelligence AI Assistant.
    
    This endpoint utilizes advanced RAG (Retrieval-Augmented Generation) 
    to provide insights based on your organization's real-time data.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if not settings.ENABLE_AI_ASSISTANT:
        raise HTTPException(status_code=400, detail="AI Assistant is disabled. Set ENABLE_AI_ASSISTANT=true in .env")

    if not retail_agent.llm.is_available():
        raise HTTPException(
            status_code=503,
            detail="No AI provider available. Start Ollama (ollama serve) or add ANTHROPIC_API_KEY/OPENAI_API_KEY to .env"
        )

    try:
        # Pass conversation history to the Smart RAG Agent
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        result = await retail_agent.chat(request.message, history=history_dicts)
        
        return ChatResponse(
            response=result["response"], 
            provider=result["provider"],
            rag_enhanced=result.get("rag_enhanced", True)
        )
    except Exception as e:
        logger.error(f"AI Assistant Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

@router.get("/status", response_model=AssistantStatusResponse)
async def assistant_status(current_user: User = Depends(get_current_user)):
    """
    Check the current operational status and configuration of the AI engine.
    """
    return {
        "available": llm.is_available(),
        "provider": llm.provider,
        "model": settings.OLLAMA_MODEL if llm.provider == "ollama" else "cloud",
        "ollama_url": settings.OLLAMA_BASE_URL if settings.USE_OLLAMA else None,
    }
