"""
AI Assistant API Routes
Handles chat interactions with Google Gemini API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging
from datetime import datetime
try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Configure Gemini API
# Note: API key should be set in environment variable GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Concise system prompt for business-focused responses
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

**Example:**
User: "What were last month's sales trends?"
Response: "Last month showed steady growth with total revenue of ₹2.4L, up 12% from the previous month.

Key Insights:
1. Peak sales occurred on weekends (Fri-Sun), accounting for 45% of revenue
2. Electronics category drove the growth with 28% increase
3. Average transaction value increased from ₹850 to ₹920

Suggestions:
1. Focus weekend promotions on high-margin electronics
2. Consider extending weekend hours to capture more traffic"

Keep responses under 150 words unless detailed analysis is specifically requested.
Use simple, clean formatting without bold, italics, or special characters.
"""

# In-memory storage for conversations (replace with database in production)
conversations = {}

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
    type: str # e.g., 'draft_po'
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
    query_result: Optional[QueryResult] = None  # New: database results if available

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI assistant using Multi-Provider Routing
    Now includes database results when template matches.
    """
    try:
        from app.services.ai_service import ai_service
        from app.services.semantic_layer import semantic_layer
        from app.services.query_executor import query_executor
        
        # Initialize conversation history if not exists
        if request.session_id not in conversations:
            conversations[request.session_id] = []

        # Add user message to history
        conversations[request.session_id].append({
            "role": "user",
            "parts": [request.message.text]
        })

        # Get system prompt if provided
        base_system_prompt = request.system_prompt or "You are a helpful AI assistant for an Enterprise Retail Intelligence System."
        
        # Try to match and execute a query (template or dynamic)
        # This is now handled entirely within ai_service.generate_response
        
        # Build full system prompt with context
        full_system_prompt = f"""{SYSTEM_PROMPT}

Current Context:
- User is viewing the ERIS retail intelligence dashboard
- System has access to sales, inventory, customer, and analytics data
- Respond in {request.message.language}
"""
        
        # Call AI Service (will also execute templates internally)
        result = await ai_service.generate_response(
            message=request.message.text,
            system_prompt=full_system_prompt,
            session_history=conversations[request.session_id][:-1],
            execute_templates=True
        )
        
        response_text = result["text"]
        action_payload = None
        
        if result.get("action"):
             action_payload = ActionData(type=result["action"]["type"], data=result["action"]["data"])

        query_result_data = None
        if result.get("query_result"):
             query_result_data = QueryResult(**result["query_result"])

        # Add AI response to history
        conversations[request.session_id].append({
            "role": "model",
            "parts": [response_text]
        })

        # Create response message (NO provider label added to text)
        ai_message = Message(
            text=response_text,
            language=request.message.language,
            script='native',
            timestamp=datetime.utcnow().isoformat()
        )
        
        return ChatResponse(
            message=ai_message,
            session_id=request.session_id,
            action=action_payload,
            query_result=query_result_data  # Include database results if available
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Retrieve chat history for a session
    """
    if session_id not in conversations:
        return {"session_id": session_id, "messages": []}

    return {
        "session_id": session_id,
        "messages": conversations[session_id]
    }

@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Clear chat history for a session
    """
    if session_id in conversations:
        del conversations[session_id]

    return {"message": "Chat history cleared", "session_id": session_id}

@router.get("/status")
async def get_status():
    """
    Check AI service status and provider availability
    """
    try:
        from app.services.ai_service import ai_service
        
        provider_status = ai_service.get_provider_status()
        
        # Determine primary active provider for display
        # Prefer real API providers over mock; mock is always available
        real_providers = [k for k, v in provider_status.items() if v and k != "mock"]
        active_providers = [k for k, v in provider_status.items() if v]
        
        # Pick a friendly primary provider label
        if real_providers:
            primary_key = real_providers[0]
            label_map = {
                "openrouter": "OpenRouter (Llama 3)",
                "groq": "Groq (Llama 3.3)",
                "gemini": "Gemini 1.5 Flash",
                "ollama": "Ollama (Local)"
            }
            primary = label_map.get(primary_key, primary_key.capitalize())
        elif provider_status.get("mock"):
            primary = "demo"  # Demo Mode — no API key needed
        else:
            primary = "Offline"
        
        return {
            "service": "ERIS AI Assistant",
            "primary_provider": primary,
            "providers": provider_status,
            "active_sessions": len(conversations),
            "status": "online" if active_providers else "offline"
        }
    except Exception as e:
        # If ai_service fails to import (missing dependencies), return offline status
        return {
            "service": "ERIS AI Assistant",
            "primary_provider": "Offline",
            "providers": {
                "groq": False,
                "gemini": False,
                "openrouter": False,
                "ollama": False,
                "mock": False
            },
            "active_sessions": 0,
            "status": "offline",
            "error": "AI service dependencies not available"
        }

@router.get("/semantic-layer")
async def get_semantic_layer_info():
    """
    Get semantic layer configuration and capabilities
    """
    from app.services.semantic_layer import semantic_layer
    
    return {
        "service": "ERIS Semantic Layer",
        "capabilities": {
            "business_terms_count": len(semantic_layer.definitions),
            "schema_tables_count": len(semantic_layer.schema),
            "query_templates_count": len(semantic_layer.templates),
            "validation_rules_count": len(semantic_layer.rules)
        },
        "templates": list(semantic_layer.templates.keys()),
        "tables": list(semantic_layer.schema.keys()),
        "status": "active"
    }

@router.post("/validate-sql")
async def validate_sql(request: dict):
    """
    Validate a SQL query against semantic layer rules
    """
    from app.services.semantic_layer import semantic_layer
    
    sql = request.get("sql", "")
    if not sql:
        raise HTTPException(status_code=400, detail="SQL query required")
    
    is_valid, issues = semantic_layer.validate_sql(sql)
    
    return {
        "is_valid": is_valid,
        "issues": issues,
        "sql_length": len(sql)
    }

