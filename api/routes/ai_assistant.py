"""
AI Assistant API Routes
Handles chat interactions with Google Gemini API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import google.generativeai as genai

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])

# Configure Gemini API
# Note: API key should be set in environment variable GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

class ChatResponse(BaseModel):
    message: Message
    session_id: str
    action: Optional[ActionData] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI assistant using Multi-Provider Routing
    """
    try:
        from api.services.ai_service import ai_service
        
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
        
        # Import and use semantic layer for enhanced context
        from api.services.semantic_layer import semantic_layer
        
        # Check for pre-approved template match first
        template_match = semantic_layer.match_template(request.message.text)
        if template_match:
            template_name, template_sql = template_match
            # If we have a template match, provide it directly
            template_hint = f"""
IMPORTANT: For this query, use this pre-approved SQL template:
```sql
{template_sql}
```
You may present the results naturally in your response.
"""
        else:
            template_hint = ""
        
        # Get enhanced context from semantic layer
        schema_context = semantic_layer.get_schema_context()
        terms_context = semantic_layer.get_business_terms_context()
        
        # Enhanced System Prompt for Actions
        action_instructions = """
        IMPORTANT: If the user indicates they want to create, draft, or make a Purchase Order (PO), you MUST include a structured action in your response.
        
        Format your response like this:
        [Your natural language response here]
        <<ACTION>>{"type": "draft_po", "data": {"item": "Item Name", "quantity": 100, "vendor": "Vendor Name", "delivery_date": "YYYY-MM-DD"}}<<END_ACTION>>
        
        Extract as much information as possible from the user's request. Use intelligent defaults if missing.
        """
        
        full_system_prompt = f"""{base_system_prompt}

{schema_context}

{terms_context}

## SQL Generation Rules:
1. Only use tables: sales, products, customers, inventory
2. Always specify columns explicitly (no SELECT *)
3. Use DATE() for date comparisons
4. For date columns, use 'transaction_date' not 'date'
5. Join products table when you need product names
6. Use COALESCE for nullable columns

{template_hint}

{action_instructions}
"""
        
        # Call AI Service
        result = await ai_service.generate_response(
            message=request.message.text,
            system_prompt=full_system_prompt,
            session_history=conversations[request.session_id][:-1]
        )
        
        response_text = result["text"]
        action_payload = None
        
        if result.get("action"):
             action_payload = ActionData(type=result["action"]["type"], data=result["action"]["data"])

        # Add AI response to history
        conversations[request.session_id].append({
            "role": "model",
            "parts": [response_text]
        })

        # Create response message
        ai_message = Message(
            text=response_text,
            language=request.message.language,
            script='native',
            timestamp=datetime.utcnow().isoformat()
        )
        
        # We append provider name to message for UI visibility (optional hack or Schema update)
        # Choosing to prepend to text for immediate feedback without schema change
        provider_badge = f"[Provider: {result['provider']}]\n"
        ai_message.text = provider_badge + ai_message.text

        return ChatResponse(
            message=ai_message,
            session_id=request.session_id,
            action=action_payload
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
    from api.services.ai_service import ai_service
    
    provider_status = ai_service.get_provider_status()
    
    # Determine primary active provider for display
    active_providers = [k for k, v in provider_status.items() if v]
    primary = active_providers[0] if active_providers else "Offline"
    
    return {
        "service": "R-DIOS AI Assistant",
        "primary_provider": primary,
        "providers": provider_status,
        "active_sessions": len(conversations),
        "status": "online" if active_providers else "offline"
    }

@router.get("/semantic-layer")
async def get_semantic_layer_info():
    """
    Get semantic layer configuration and capabilities
    """
    from api.services.semantic_layer import semantic_layer
    
    return {
        "service": "R-DIOS Semantic Layer",
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
    from api.services.semantic_layer import semantic_layer
    
    sql = request.get("sql", "")
    if not sql:
        raise HTTPException(status_code=400, detail="SQL query required")
    
    is_valid, issues = semantic_layer.validate_sql(sql)
    
    return {
        "is_valid": is_valid,
        "issues": issues,
        "sql_length": len(sql)
    }

