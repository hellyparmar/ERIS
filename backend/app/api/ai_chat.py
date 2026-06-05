"""
AI Chat Router - Context-aware retail assistant with Ollama integration
"""

from datetime import datetime, timedelta
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
import requests
import json
from uuid import UUID
import uuid as uuid_lib

from app.database import get_db
from app.models import User, SaleTransaction, Inventory, Product, Outlet, Forecast, Alert
from app.models.chat import ChatMessage
from app.api.deps import get_current_active_user
from app.core.data_isolation import OutletDataAccess

router = APIRouter(prefix="/api/v1/chat", tags=["ai-chat"])

OLLAMA_BASE_URL = "http://ollama:11434"
OLLAMA_MODEL = "mistral"
OLLAMA_TIMEOUT = 30


def fetch_sales_context(outlet_ids: List[int], db: Session) -> str:
    """Fetch today's sales summary"""
    today = datetime.now().date()

    revenue_result = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id.in_(outlet_ids),
        func.date(SaleTransaction.transaction_at) == today
    ).scalar() or 0

    transactions_result = db.query(func.count(SaleTransaction.id)).filter(
        SaleTransaction.outlet_id.in_(outlet_ids),
        func.date(SaleTransaction.transaction_at) == today
    ).scalar() or 0

    top_products = db.query(
        Product.name,
        func.sum(SaleTransaction.quantity).label("qty")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).filter(
        SaleTransaction.outlet_id.in_(outlet_ids),
        func.date(SaleTransaction.transaction_at) == today
    ).group_by(Product.id, Product.name).order_by(
        func.sum(SaleTransaction.quantity).desc()
    ).limit(3).all()

    context = f"Sales Context (Today):\n"
    context += f"- Total Revenue: ₹{float(revenue_result):,.2f}\n"
    context += f"- Total Transactions: {int(transactions_result)}\n"
    if top_products:
        context += f"- Top Products: {', '.join([f'{row[0]} ({row[1]} units)' for row in top_products])}\n"

    return context


def fetch_inventory_context(outlet_ids: List[int], db: Session) -> str:
    """Fetch inventory and alerts"""
    low_stock = db.query(func.count(Inventory.id)).filter(
        Inventory.outlet_id.in_(outlet_ids),
        Inventory.current_stock <= Product.reorder_point
    ).scalar() or 0

    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.outlet_id.in_(outlet_ids),
        Alert.is_acknowledged == False
    ).scalar() or 0

    result = await db.execute(select(Alert.message).where(Alert.outlet_id.in_(outlet_ids),
        Alert.is_acknowledged == False,
        Alert.severity == "critical"
    ).limit(3).all()

    context = f"Inventory Context:\n"
    context += f"- Items Below Reorder Point: {int(low_stock)}\n"
    context += f"- Active Alerts: {int(active_alerts)}\n"
    if critical_alerts:
        context += f"- Critical Alerts: {', '.join([row[0][:50] for row in critical_alerts])}\n"

    return context


def fetch_forecast_context(outlet_ids: List[int], db: Session) -> str:
    """Fetch latest forecasts"""
    result = await db.execute(select(Forecast).where(Forecast.outlet_id.in_(outlet_ids)
    ).order_by(desc(Forecast.generated_at)))

    critical_alerts = result.scalar_one_or_none()
    context = f"Forecast Context:\n"
    if recent_forecast:
        context += f"- Latest Forecast: {recent_forecast.forecast_date}\n"
        context += f"- Predicted Value: ₹{recent_forecast.forecast_value:,.2f}\n"
        context += f"- Confidence Range: ₹{recent_forecast.lower_bound:,.2f} to ₹{recent_forecast.upper_bound:,.2f}\n"
    else:
        context += f"- No forecasts available yet\n"

    return context


def build_conversation_history(session_id: str, db: Session) -> List[dict]:
    """Load last 10 messages for session"""
    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(10))
    recent_forecast = result.scalars().all()
    messages = list(reversed(messages))
    return [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in messages
    ]


def build_system_prompt(current_user: User, outlet_name: str, context_data: str) -> str:
    """Build system prompt with user context and data"""
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""You are a helpful retail business intelligence assistant for {outlet_name}.

User Information:
- Name: {current_user.full_name}
- Role: {current_user.role}
- Date: {today}

Business Context:
{context_data}

Guidelines:
1. ONLY reference data that was provided to you above
2. NEVER fabricate sales figures, inventory numbers, or any metrics
3. If asked about data not provided, say "I don't have that data available"
4. Be concise and business-focused
5. Format currency as ₹ with 2 decimal places
6. Provide actionable insights when possible"""

    return prompt


def call_ollama(messages: List[dict], system_prompt: str) -> Optional[str]:
    """Call Ollama API with conversation history"""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt}
            ] + messages,
            "stream": False
        }

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "")
        else:
            return None

    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None


@router.post("/message")
async def send_message(
    session_id: str,
    message: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Send a message to AI assistant.
    Fetches relevant context, calls Ollama, saves conversation.
    """
    # Validate session_id format (basic UUID check)
    try:
        uuid_lib.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format"
        )

    if not message or len(message.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    # Get user's accessible outlets
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if allowed_outlet_ids is not None and len(allowed_outlet_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    outlet_scope = None if allowed_outlet_ids is None else allowed_outlet_ids

    # Get outlet name
    if outlet_scope:
        result = await db.execute(select(Outlet).where(Outlet.id.in_(outlet_scope)))
    messages = result.scalar_one_or_none()
    else:
        outlet = db.query(Outlet).first()

    outlet_name = outlet.name if outlet else "Your Store"

    # Detect keywords and fetch relevant context
    message_lower = message.lower()
    context_parts = []

    # Sales context
    if any(keyword in message_lower for keyword in ["sales", "revenue", "today", "yesterday", "sold", "transaction"]):
        context_parts.append(fetch_sales_context(outlet_scope, db))

    # Inventory context
    if any(keyword in message_lower for keyword in ["inventory", "stock", "alert", "reorder", "shortage"]):
        context_parts.append(fetch_inventory_context(outlet_scope, db))

    # Forecast context
    if any(keyword in message_lower for keyword in ["forecast", "predict", "prediction", "trend"]):
        context_parts.append(fetch_forecast_context(outlet_scope, db))

    # If no keywords matched, fetch general context
    if not context_parts:
        context_parts.append(fetch_sales_context(outlet_scope, db))
        context_parts.append(fetch_inventory_context(outlet_scope, db))

    context_data = "\n".join(context_parts)

    # Build conversation history
    conversation_history = build_conversation_history(session_id, db)

    # Build system prompt
    system_prompt = build_system_prompt(current_user, outlet_name, context_data)

    # Add current message to history for API call
    messages_for_api = conversation_history + [
        {"role": "user", "content": message}
    ]

    # Call Ollama
    ai_response = call_ollama(messages_for_api, system_prompt)

    if ai_response is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "AI assistant is temporarily unavailable",
                "fallback_response": "Please try again in a moment."
            }
        )

    # Save user message to database
    try:
        user_outlet_id = getattr(current_user, "outlet_id", None)
        if not user_outlet_id and outlet is not None:
            user_outlet_id = outlet.id

        user_msg = ChatMessage(
            session_id=session_id,
            user_id=current_user.id,
            outlet_id=user_outlet_id,
            role="user",
            content=message,
            created_at=datetime.now()
        )
        db.add(user_msg)

        # Save assistant message to database
        assistant_msg = ChatMessage(
            session_id=session_id,
            user_id=current_user.id,
            outlet_id=user_outlet_id,
            role="assistant",
            content=ai_response,
            created_at=datetime.now()
        )
        db.add(assistant_msg)

        db.commit()

        return {
            "session_id": session_id,
            "message_id": user_msg.id,
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "role": "assistant"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save message"
        )


@router.get("/history/{session_id}")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get full message history for a session.
    User can only see their own sessions.
    """
    # Validate session_id format
    try:
        uuid_lib.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format"
        )

    # Get messages for this session
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at))
        outlet = result.scalars().all()
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {
        "session_id": session_id,
        "total_messages": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete all messages in a chat session.
    User can only delete their own sessions.
    """
    # Validate session_id format
    try:
        uuid_lib.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format"
        )

    # Delete messages
    deleted_count = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == current_user.id
    ).delete()

    db.commit()

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {
        "message": "Session deleted successfully",
        "session_id": session_id,
        "messages_deleted": deleted_count
    }
