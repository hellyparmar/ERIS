"""
AI Assistant API Router
Provides conversational AI interface with RAG capabilities
"""

import time
from sqlalchemy import select
import uuid
import asyncio
# import requests  # TEMPORARILY DISABLED - requests package not in container yet
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import redis
import json

from app.database import get_db
from app.api.auth.dependencies import get_current_user
from app.models.users import User, UserStore
from app.ml.rag.pipeline import ERISRAGPipeline
from app.core.config import settings
from app.tasks.rag_tasks import refresh_knowledge_base_task


router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


def get_redis_client():
    """Dependency to get Redis client"""
    return redis.Redis(
        host=settings.REDIS_URL.split('://')[1].split(':')[0],
        port=int(settings.REDIS_URL.split(':')[-1]),
        decode_responses=True
    )


@router.post("/chat")
async def chat(
    request: Request,
    message: str,
    conversation_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Chat with AI assistant using RAG
    """
    try:
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Load conversation history
        history_key = f"chat:{current_user.id}:{conversation_id}"
        history_data = redis_client.get(history_key)
        conversation_history = json.loads(history_data) if history_data else []

        # Get user's outlet ID
        result = await db.execute(select(UserStore).where(UserStore.user_id == current_user.id,
            UserStore.is_active == True))
        user_store = result.scalar_one_or_none()
        if not user_store:
            raise HTTPException(status_code=400, detail="User not assigned to any outlet")

        # Initialize RAG pipeline
        pipeline = ERISRAGPipeline(db, user_store.outlet_id, redis_client)

        # Generate response
        response = pipeline.generate_response(message, conversation_history)

        # Update conversation history
        conversation_history.append({
            "user": message,
            "assistant": response,
            "timestamp": time.time()
        })

        # Keep only last 50 messages
        if len(conversation_history) > 50:
            conversation_history = conversation_history[-50:]

        # Store updated history (TTL: 24 hours)
        redis_client.setex(
            history_key,
            86400,  # 24 hours
            json.dumps(conversation_history)
        )

        # Get sources (retrieved chunks)
        sources = pipeline.retrieve(message)

        # Check if streaming is requested
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" in accept_header:
            # Return streaming response
            async def generate():
                # Simulate streaming by yielding chunks
                words = response.split()
                for i, word in enumerate(words):
                    yield f"data: {json.dumps({'chunk': word + ' ', 'done': False})}\n\n"
                    await asyncio.sleep(0.05)  # Small delay for streaming effect
                yield f"data: {json.dumps({'chunk': '', 'done': True, 'conversation_id': conversation_id, 'sources': sources})}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache"}
            )

        # Return regular response
        return {
            "response": response,
            "conversation_id": conversation_id,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/refresh-knowledge")
async def refresh_knowledge(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh knowledge base for user's outlet
    Requires outlet_manager or above
    """
    # Check permissions
    if current_user.role not in ["super_admin", "area_manager", "outlet_manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Get user's outlet
    result = await db.execute(select(UserStore).where(UserStore.user_id == current_user.id,
        UserStore.is_active == True))
    user_store = result.scalar_one_or_none()
    if not user_store:
        raise HTTPException(status_code=400, detail="User not assigned to any outlet")

    # Trigger background task
    background_tasks.add_task(
        refresh_knowledge_base_task.delay,
        user_store.outlet_id
    )

    return {"message": "Knowledge base refresh initiated"}


@router.get("/health")
async def health_check():
    """
    Check AI assistant health
    """
    try:
        start_time = time.time()

        # Check Ollama connectivity
        response = requests.get(
            f"{ERISRAGPipeline.OLLAMA_HOST}/api/tags",
            timeout=5
        )

        response_time = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            models = response.json().get("models", [])
            mistral_available = any(model.get("name") == "mistral" for model in models)

            return {
                "status": "ok",
                "model": "mistral" if mistral_available else "unknown",
                "response_time_ms": response_time
            }
        else:
            return {
                "status": "unavailable",
                "model": None,
                "response_time_ms": response_time
            }

    except Exception as e:
        return {
            "status": "unavailable",
            "model": None,
            "response_time_ms": 0
        }