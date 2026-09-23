"""
AI Assistant API Routes

Authentication & RLS notes
---------------------------
Every user-facing endpoint in this router requires a valid JWT via
get_current_active_user (from app.api.deps).  The /chat endpoint extracts the
authenticated user's organization_id (tenant_id) and accessible outlet IDs
and threads them through ai_service.generate_response → query_executor, so
every SQL query the AI assistant executes is (a) tenant-scoped via
SELECT set_config('app.current_tenant_id', ...) and (b) outlet-filtered by
the scoped outlet IDs returned by get_outlet_scope().

Conversation history is persisted in the chat_messages table (ChatMessage
model, backend/app/models/chat.py) keyed on (user_id, session_id), so no
user can read or delete another user's conversation by supplying an arbitrary
session_id.  The in-memory `conversations` dict that previously existed here
has been removed entirely.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_current_active_user, get_outlet_scope
from app.models.users import User
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an intelligent AI assistant for ERIS, a retail intelligence system.

**Response Guidelines:**
1. **Be Concise**: Provide direct, actionable answers without unnecessary technical details
2. **Business Focus**: Frame insights in business terms, not technical jargon
3. **No Code in Responses**: Never show SQL queries, code snippets, or technical implementation details to users
4. **Clean Formatting**: Use plain text without markdown symbols (no **, •, or #)
5. **Structure**: Use this format:
   - Direct answer to the question
   - Key Insights section with numbered points
   - Suggestions section with numbered recommendations

Keep responses under 150 words unless detailed analysis is specifically requested.
Use simple, clean formatting without bold, italics, or special characters.
"""


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class Message(BaseModel):
    text: str
    language: str
    script: str  # 'native' or 'roman'
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: Message
    session_id: str
    system_prompt: Optional[str] = None

class ActionData(BaseModel):
    type: str
    data: dict

class QueryResult(BaseModel):
    """Database query results if template was matched."""
    success: bool
    data: List[Dict] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    template_matched: Optional[str] = None

class ChatResponse(BaseModel):
    message: Message
    session_id: str
    action: Optional[ActionData] = None
    query_result: Optional[QueryResult] = None


# ---------------------------------------------------------------------------
# Synchronous DB dependency (mirrors analytics.py pattern)
# ---------------------------------------------------------------------------

from app.database import SessionLocal

def get_sync_db():
    """Synchronous session for this router's endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# Helpers for ChatMessage-backed history
# ---------------------------------------------------------------------------

def _load_history(db: Session, user_id: int, session_id: str) -> list:
    """
    Load conversation history for (user_id, session_id) from chat_messages.
    Returns list of {'role': ..., 'parts': [...]} dicts for the LLM.
    """
    rows = db.execute(
        text(
            "SELECT role, content FROM chat_messages "
            "WHERE user_id = :uid AND session_id = :sid "
            "ORDER BY created_at ASC"
        ),
        {"uid": user_id, "sid": session_id},
    ).fetchall()
    return [{"role": r[0], "parts": [r[1]]} for r in rows]


def _save_message(
    db: Session,
    user_id: int,
    outlet_id: int,
    session_id: str,
    role: str,
    content: str,
):
    """Persist a single message to chat_messages."""
    db.execute(
        text(
            "INSERT INTO chat_messages "
            "(session_id, user_id, outlet_id, role, content, created_at) "
            "VALUES (:sid, :uid, :oid, :role, :content, :ts)"
        ),
        {
            "sid": session_id,
            "uid": user_id,
            "oid": outlet_id,
            "role": role,
            "content": content,
            "ts": datetime.now(timezone.utc),
        },
    )
    db.commit()


def _assert_session_owned_by_user(db: Session, user_id: int, session_id: str):
    """Raise 403 if session_id doesn't belong to user_id."""
    count = db.execute(
        text(
            "SELECT COUNT(*) FROM chat_messages "
            "WHERE session_id = :sid AND user_id = :uid"
        ),
        {"sid": session_id, "uid": user_id},
    ).scalar()
    if count == 0:
        raise HTTPException(
            status_code=403,
            detail="Session not found or does not belong to this user.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Send a message to the AI assistant.

    - Requires a valid JWT (Bearer token).
    - Conversation history is stored per-user in chat_messages (not in memory).
    - Every SQL query the assistant executes is scoped to the authenticated
      user's accessible outlets and tenant, satisfying PostgreSQL RLS.
    """
    try:
        from app.services.ai_service import ai_service

        # ── Resolve tenant + outlet scope ────────────────────────────────────
        tenant_id = str(current_user.organization_id)
        outlet_ids = get_outlet_scope(current_user, db)
        if not outlet_ids:
            outlet_ids = [-1]  # no accessible outlets → queries return 0 rows

        # Primary outlet for history storage (first scoped outlet, or user's own)
        primary_outlet_id = outlet_ids[0] if outlet_ids and outlet_ids[0] != -1 else (
            getattr(current_user, "outlet_id", None) or 0
        )

        # ── Load existing history ─────────────────────────────────────────────
        session_history = _load_history(db, current_user.id, request.session_id)

        # ── Persist incoming user message ─────────────────────────────────────
        _save_message(
            db, current_user.id, primary_outlet_id,
            request.session_id, "user", request.message.text,
        )

        # ── Build system prompt ───────────────────────────────────────────────
        full_system_prompt = f"""{SYSTEM_PROMPT}

Current Context:
- User: {current_user.username} (outlet scope: {outlet_ids})
- User is viewing the ERIS retail intelligence dashboard
- System has access to sales, inventory, customer, and analytics data
- Respond in {request.message.language}
"""

        # ── Call AI service (tenant-scoped) ───────────────────────────────────
        result = await ai_service.generate_response(
            message=request.message.text,
            system_prompt=full_system_prompt,
            session_history=session_history,
            execute_templates=True,
            outlet_ids=outlet_ids,
            tenant_id=tenant_id,
        )

        response_text = result["text"]

        # ── Persist AI response ───────────────────────────────────────────────
        _save_message(
            db, current_user.id, primary_outlet_id,
            request.session_id, "model", response_text,
        )

        action_payload = None
        if result.get("action"):
            action_payload = ActionData(
                type=result["action"]["type"],
                data=result["action"]["data"],
            )

        query_result_data = None
        if result.get("query_result"):
            query_result_data = QueryResult(**result["query_result"])

        ai_message = Message(
            text=response_text,
            language=request.message.language,
            script="native",
            timestamp=datetime.utcnow().isoformat(),
        )

        return ChatResponse(
            message=ai_message,
            session_id=request.session_id,
            action=action_payload,
            query_result=query_result_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.get("/history/{session_id}")
def get_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Retrieve chat history for a session owned by the authenticated user.
    Returns 403 if the session_id belongs to a different user.
    """
    rows = db.execute(
        text(
            "SELECT role, content, created_at FROM chat_messages "
            "WHERE session_id = :sid AND user_id = :uid "
            "ORDER BY created_at ASC"
        ),
        {"sid": session_id, "uid": current_user.id},
    ).fetchall()

    # Empty result is valid (new session) — no ownership check needed here
    messages = [
        {"role": r[0], "content": r[1], "timestamp": str(r[2])}
        for r in rows
    ]
    return {"session_id": session_id, "messages": messages}


@router.delete("/history/{session_id}")
def clear_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Delete all chat history for a session.
    Returns 403 if session_id belongs to a different user.
    """
    _assert_session_owned_by_user(db, current_user.id, session_id)
    db.execute(
        text(
            "DELETE FROM chat_messages "
            "WHERE session_id = :sid AND user_id = :uid"
        ),
        {"sid": session_id, "uid": current_user.id},
    )
    db.commit()
    return {"message": "Chat history cleared", "session_id": session_id}


@router.get("/status")
async def get_status():
    """
    Check AI service status and provider availability.
    No authentication required — used by the frontend health-check.
    """
    try:
        from app.services.ai_service import ai_service

        provider_status = ai_service.get_provider_status()
        real_providers = [k for k, v in provider_status.items() if v and k != "mock"]
        active_providers = [k for k, v in provider_status.items() if v]

        if real_providers:
            primary_key = real_providers[0]
            label_map = {
                "openrouter": "OpenRouter (Llama 3)",
                "groq": "Groq (Llama 3.3)",
                "gemini": "Gemini 1.5 Flash",
                "ollama": "Ollama (Local)",
            }
            primary = label_map.get(primary_key, primary_key.capitalize())
        elif provider_status.get("mock"):
            primary = "demo"
        else:
            primary = "Offline"

        return {
            "service": "ERIS AI Assistant",
            "primary_provider": primary,
            "providers": provider_status,
            "status": "online" if active_providers else "offline",
        }
    except Exception as e:
        return {
            "service": "ERIS AI Assistant",
            "primary_provider": "Offline",
            "providers": {"groq": False, "gemini": False, "openrouter": False, "ollama": False, "mock": False},
            "active_sessions": 0,
            "status": "offline",
            "error": "AI service dependencies not available",
        }


@router.get("/semantic-layer")
async def get_semantic_layer_info():
    """Get semantic layer configuration and capabilities."""
    from app.services.semantic_layer import semantic_layer

    return {
        "service": "ERIS Semantic Layer",
        "capabilities": {
            "business_terms_count": len(semantic_layer.definitions),
            "schema_tables_count": len(semantic_layer.schema),
            "query_templates_count": len(semantic_layer.templates),
            "validation_rules_count": len(semantic_layer.rules),
        },
        "templates": list(semantic_layer.templates.keys()),
        "tables": list(semantic_layer.schema.keys()),
        "status": "active",
    }


@router.post("/validate-sql")
def validate_sql(
    request: dict,
    current_user: User = Depends(get_current_active_user),
):
    """
    Validate a SQL query against semantic layer rules.
    Requires authentication — prevents unauthenticated probing of schema rules.
    """
    from app.services.semantic_layer import semantic_layer

    sql = request.get("sql", "")
    if not sql:
        raise HTTPException(status_code=400, detail="SQL query required")

    is_valid, issues = semantic_layer.validate_sql(sql)

    return {
        "is_valid": is_valid,
        "issues": issues,
        "sql_length": len(sql),
    }
