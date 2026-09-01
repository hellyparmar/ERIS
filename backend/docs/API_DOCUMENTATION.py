"""
Enhanced RAG System - API Documentation
Complete REST API documentation for the conversational assistant

Endpoints:
1. POST /api/v1/assistant/smart-chat
2. GET /api/v1/assistant/suggestions
3. GET /api/v1/assistant/history
4. POST /api/v1/assistant/feedback
5. POST /api/v1/assistant/index-products
6. GET /api/v1/assistant/rag-stats
"""


class APIDocumentation:
    """Complete API documentation."""
    
    @staticmethod
    def endpoint_smart_chat():
        """Smart Chat endpoint documentation."""
        return {
            "endpoint": "POST /api/v1/assistant/smart-chat",
            "description": "Send a natural language query and get an AI-synthesized answer with sources",
            "authentication": "Bearer token required",
            "rate_limit": "100 requests/minute per user",
            "timeout": "30 seconds",
            
            "request": {
                "content_type": "application/json",
                "body": {
                    "query": {
                        "type": "string",
                        "description": "User's natural language question",
                        "example": "What were sales last week?",
                        "required": True
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional conversation context",
                        "properties": {
                            "conversation_id": "unique conversation identifier",
                            "previous_queries": "list of previous questions in this conversation",
                            "user_preferences": "user-specific preferences"
                        },
                        "required": False
                    },
                    "options": {
                        "type": "object",
                        "description": "Advanced options",
                        "properties": {
                            "include_rag_context": {"type": "boolean", "default": True},
                            "include_sources": {"type": "boolean", "default": True},
                            "confidence_threshold": {"type": "float", "default": 0.7},
                            "max_sources": {"type": "integer", "default": 5}
                        },
                        "required": False
                    }
                },
                "example_request": {
                    "query": "What were sales last week?",
                    "context": {
                        "conversation_id": "conv_12345",
                        "previous_queries": ["Show me March data"]
                    },
                    "options": {
                        "include_sources": True,
                        "max_sources": 3
                    }
                }
            },
            
            "response": {
                "content_type": "application/json",
                "status_codes": {
                    "200": "Success",
                    "400": "Invalid request",
                    "401": "Unauthorized",
                    "429": "Rate limit exceeded",
                    "500": "Server error"
                },
                "body": {
                    "answer": {
                        "type": "string",
                        "description": "AI-synthesized answer to the user's question"
                    },
                    "query_type": {
                        "type": "string",
                        "enum": ["factual", "analytical", "forecast", "recommendation", "comparison"],
                        "description": "Detected query intent"
                    },
                    "entities": {
                        "type": "object",
                        "description": "Extracted entities from the question",
                        "properties": {
                            "product_name": "identified product",
                            "outlet": "identified outlet/store",
                            "metric": "business metric",
                            "date_range": "temporal range",
                            "time_period": "relative time period"
                        }
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": "source type (database/rag/forecast)",
                                "collection": "data collection source",
                                "relevance_score": "0-1 similarity score",
                                "snippet": "relevant data snippet"
                            }
                        },
                        "description": "Data sources used to generate the answer"
                    },
                    "confidence": {
                        "type": "float",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence score of the answer"
                    },
                    "sql_query": {
                        "type": "string",
                        "description": "Generated SQL (if applicable)"
                    },
                    "response_time_ms": {
                        "type": "integer",
                        "description": "Time taken to generate response"
                    }
                },
                "example_response": {
                    "answer": "Based on our data, last week's total sales were ₹125,450 across 284 transactions, with Mumbai outlet leading at ₹52,300. This represents a 12% increase from the previous week.",
                    "query_type": "factual",
                    "entities": {
                        "time_period": "last_week",
                        "metric": "sales"
                    },
                    "sources": [
                        {
                            "type": "database",
                            "collection": "sales",
                            "relevance_score": 0.98,
                            "snippet": "Total sales: ₹125,450"
                        },
                        {
                            "type": "rag",
                            "collection": "insights",
                            "relevance_score": 0.85,
                            "snippet": "Week-over-week growth analysis"
                        }
                    ],
                    "confidence": 0.96,
                    "response_time_ms": 1243
                }
            },
            
            "curl_example": """
curl -X POST http://localhost:8000/api/v1/assistant/smart-chat \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "What were sales last week?",
    "context": {
      "conversation_id": "conv_123"
    },
    "options": {
      "include_sources": true,
      "max_sources": 5
    }
  }'
""",
            
            "python_example": """
import requests

response = requests.post(
    "http://localhost:8000/api/v1/assistant/smart-chat",
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "query": "What were sales last week?",
        "context": {"conversation_id": "conv_123"},
        "options": {"include_sources": True}
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Query Type: {result['query_type']}")
"""
        }
    
    @staticmethod
    def endpoint_suggestions():
        """Suggestions endpoint documentation."""
        return {
            "endpoint": "GET /api/v1/assistant/suggestions",
            "description": "Get context-aware suggestions for the user",
            "authentication": "Bearer token required",
            "rate_limit": "200 requests/minute",
            "timeout": "5 seconds",
            
            "query_parameters": {
                "context": {
                    "type": "string",
                    "description": "Current conversation context",
                    "example": "sales analysis",
                    "required": False
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of suggestions (default: 8)",
                    "min": 1,
                    "max": 20,
                    "default": 8
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID for context-aware suggestions"
                }
            },
            
            "response": {
                "body": {
                    "suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "suggestion": "suggested question",
                                "type": "type of suggestion",
                                "relevance": "relevance score 0-1",
                                "explanation": "why this suggestion is relevant"
                            }
                        }
                    },
                    "context_info": {
                        "type": "object",
                        "description": "Information about the current context"
                    }
                },
                "example_response": {
                    "suggestions": [
                        {
                            "suggestion": "Compare sales across outlets",
                            "type": "comparison",
                            "relevance": 0.92,
                            "explanation": "You recently viewed sales data; comparing outlets is a natural next step"
                        },
                        {
                            "suggestion": "What is the trend for this period?",
                            "type": "analytical",
                            "relevance": 0.88,
                            "explanation": "Trends help understand patterns in your sales"
                        },
                        {
                            "suggestion": "Forecast next week's sales",
                            "type": "forecast",
                            "relevance": 0.85,
                            "explanation": "Based on historical data, forecasts can help planning"
                        }
                    ],
                    "context_info": {
                        "last_query": "What were sales last week?",
                        "query_type": "factual",
                        "suggestions_count": 3
                    }
                }
            }
        }
    
    @staticmethod
    def endpoint_history():
        """Conversation history endpoint documentation."""
        return {
            "endpoint": "GET /api/v1/assistant/history",
            "description": "Retrieve conversation history",
            "authentication": "Bearer token required",
            
            "query_parameters": {
                "conversation_id": {
                    "type": "string",
                    "description": "Get specific conversation history",
                    "required": False
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to retrieve (default: 50)",
                    "default": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "Offset for pagination",
                    "default": 0
                }
            },
            
            "response": {
                "example_response": {
                    "conversation_id": "conv_12345",
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2026-03-28T10:30:00Z",
                            "role": "user",
                            "content": "What were sales last week?"
                        },
                        {
                            "id": "msg_2",
                            "timestamp": "2026-03-28T10:30:02Z",
                            "role": "assistant",
                            "content": "Based on our data...",
                            "query_type": "factual",
                            "confidence": 0.96
                        }
                    ],
                    "total_messages": 24,
                    "summary": "Sales analysis conversation from March 28"
                }
            }
        }
    
    @staticmethod
    def endpoint_feedback():
        """Feedback endpoint documentation."""
        return {
            "endpoint": "POST /api/v1/assistant/feedback",
            "description": "Submit feedback on assistant responses",
            "authentication": "Bearer token required",
            
            "request": {
                "body": {
                    "message_id": {
                        "type": "string",
                        "description": "ID of the message being rated"
                    },
                    "rating": {
                        "type": "integer",
                        "description": "Rating from 1-5",
                        "min": 1,
                        "max": 5
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional feedback comment"
                    },
                    "helpful": {
                        "type": "boolean",
                        "description": "Was the response helpful?"
                    }
                },
                "example_request": {
                    "message_id": "msg_2",
                    "rating": 5,
                    "comment": "Perfect! Exactly what I needed.",
                    "helpful": True
                }
            },
            
            "response": {
                "example_response": {
                    "success": True,
                    "feedback_id": "fb_123",
                    "message": "Feedback recorded successfully"
                }
            }
        }
    
    @staticmethod
    def endpoint_index_products():
        """Product indexing endpoint documentation."""
        return {
            "endpoint": "POST /api/v1/assistant/index-products",
            "description": "Trigger product re-indexing for RAG",
            "authentication": "Bearer token with admin role",
            
            "request": {
                "body": {
                    "products": {
                        "type": "array",
                        "description": "List of products to index",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": "product ID",
                                "name": "product name",
                                "category": "product category",
                                "description": "product description",
                                "price": "current price",
                                "stock": "current stock"
                            }
                        }
                    },
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Force complete re-indexing",
                        "default": False
                    }
                }
            },
            
            "response": {
                "example_response": {
                    "success": True,
                    "indexed_count": 450,
                    "collection": "products",
                    "timestamp": "2026-03-28T10:30:00Z"
                }
            }
        }
    
    @staticmethod
    def endpoint_rag_stats():
        """RAG statistics endpoint documentation."""
        return {
            "endpoint": "GET /api/v1/assistant/rag-stats",
            "description": "Get RAG system statistics",
            "authentication": "Bearer token required",
            
            "response": {
                "example_response": {
                    "collections": {
                        "products": {
                            "count": 450,
                            "last_updated": "2026-03-28T10:00:00Z"
                        },
                        "sales": {
                            "count": 15234,
                            "last_updated": "2026-03-27T23:00:00Z"
                        },
                        "insights": {
                            "count": 234,
                            "last_updated": "2026-03-28T09:00:00Z"
                        }
                    },
                    "total_documents": 15918,
                    "db_size_mb": 156.4,
                    "last_rebuild": "2026-03-28T00:00:00Z",
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            }
        }


def print_api_docs():
    """Print complete API documentation."""
    docs = APIDocumentation()
    
    print("\n" + "="*80)
    print("ENHANCED RAG SYSTEM - API DOCUMENTATION")
    print("="*80)
    
    endpoints = [
        ("Smart Chat", docs.endpoint_smart_chat()),
        ("Suggestions", docs.endpoint_suggestions()),
        ("History", docs.endpoint_history()),
        ("Feedback", docs.endpoint_feedback()),
        ("Index Products", docs.endpoint_index_products()),
        ("RAG Stats", docs.endpoint_rag_stats())
    ]
    
    for name, doc in endpoints:
        print(f"\n{'='*80}")
        print(f"ENDPOINT: {name}")
        print(f"{'='*80}")
        print(f"URL: {doc['endpoint']}")
        print(f"Description: {doc['description']}")
        if 'authentication' in doc:
            print(f"Authentication: {doc['authentication']}")
        if 'rate_limit' in doc:
            print(f"Rate Limit: {doc['rate_limit']}")
        
        if 'request' in doc:
            print("\n--- REQUEST ---")
            import json
            print(json.dumps(doc['request'].get('example_request', doc['request']), indent=2))
        
        if 'query_parameters' in doc:
            print("\n--- QUERY PARAMETERS ---")
            for param, spec in doc['query_parameters'].items():
                print(f"  {param}: {spec.get('description', 'N/A')}")
        
        print("\n--- RESPONSE ---")
        import json
        response = doc.get('response', {})
        print(json.dumps(response.get('example_response', response), indent=2))


if __name__ == "__main__":
    print_api_docs()
