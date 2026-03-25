from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field("user", description="Role of the message author (user or assistant)")
    content: str = Field(..., description="Text content of the message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "user",
                "content": "What are my top 3 products by revenue?"
            }
        }
    }

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's natural language query")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Previous messages in the conversation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Give me a summary of yesterday's sales.",
                "history": [
                    {"role": "user", "content": "Hello assistant."},
                    {"role": "assistant", "content": "Hello! How can I help you today?"}
                ]
            }
        }
    }

class ChatResponse(BaseModel):
    response: str = Field(..., description="The AI assistant's natural language response")
    provider: str = Field(..., description="The LLM provider used (e.g., ollama, anthropic, openai)")
    rag_enhanced: bool = Field(False, description="Whether the response was generated using RAG (Retrieval Augmented Generation)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "Your total sales yesterday were $12,500 across 45 transactions.",
                "provider": "anthropic",
                "rag_enhanced": True
            }
        }
    }

class AssistantStatusResponse(BaseModel):
    available: bool = Field(..., description="Whether the AI assistant is currently reachable")
    provider: str = Field(..., description="The configured AI provider")
    model: str = Field(..., description="The specific model being used")
    ollama_url: Optional[str] = Field(None, description="URL of the local Ollama instance if applicable")

    model_config = {
        "json_schema_extra": {
            "example": {
                "available": True,
                "provider": "ollama",
                "model": "llama3",
                "ollama_url": "http://localhost:11434"
            }
        }
    }
