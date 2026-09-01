import os
import random
import logging
import json
import requests
from typing import Dict, Any, Optional
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables — try project root .env first, then fallback
_root_env = Path(__file__).parent.parent.parent / ".env"
_api_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env, override=False)  # load root .env
load_dotenv(_api_env, override=False)   # load api/.env (merges, no override)

# Configure logging
logger = logging.getLogger(__name__)

from app.database import AsyncSessionLocal
from sqlalchemy import text

class AIService:
    """
    Multi-Provider AI Service
    Routes requests between Groq (Primary), Gemini (Secondary), OpenRouter (Backup), and Ollama (Offline).
    """
    
    def __init__(self):
        # Load API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Initialize Clients
        self.groq_client = Groq(api_key=self.groq_key) if self.groq_key else None
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_key
        ) if self.openrouter_key else None

        # Routing Weights
        self.weights = {
            "openrouter": 1.0, # 100% Traffic (User Preference: Llama 3)
            "groq": 0.0,
            "gemini": 0.0
        }

    def _get_provider(self, context_length: str = "short") -> str:
        """
        Determines which provider to use based on availability and priority.
        """
        statuses = self.get_provider_status()
        
        # Priority order: ollama (local), groq (fast), openrouter, gemini
        for prov in ["ollama", "groq", "openrouter", "gemini"]:
            if statuses.get(prov):
                return prov
                
        return "mock"

    async def generate_response(
        self, 
        message: str, 
        system_prompt: str, 
        session_history: list = [],
        execute_templates: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point to get AI response.
        Now includes database results if template matches.
        """
        # Determine paths based on simple heuristics
        import re
        msg_lower = message.lower()
        needs_vector = bool(re.search(r"why|explain|reason|policy|terms|description|notes|impact|what caused", msg_lower))
        needs_sql = True  # Always try structured matching as primary
        
        # Try to match and execute template query
        database_context = ""
        query_result_data = None
        if execute_templates and needs_sql:
            try:
                from app.services.semantic_layer import semantic_layer
                from app.services.query_executor import query_executor
                
                template_match = semantic_layer.match_template(message)
                if template_match:
                    template_name, template_sql = template_match
                    logger.info(f"Template matched: {template_name}")
                    
                    # Execute query
                    result = query_executor.execute_template_query(template_sql, semantic_layer)
                    
                    if result.get("success"):
                        # Format results for LLM context
                        database_context = query_executor.format_results_for_llm(result)
                        query_result_data = {
                            "success": True,
                            "data": result.get("data", []),
                            "row_count": result.get("row_count", 0),
                            "execution_time_ms": result.get("execution_time_ms", 0),
                            "template_matched": template_name
                        }
                        logger.info(f"Database results: {result.get('row_count')} rows")
                    else:
                        logger.warning(f"Query execution failed: {result.get('error')}")
                        
            except Exception as e:
                logger.warning(f"Template execution disabled or failed: {str(e)}")
        
        # Try to get unstructured context from vector DB
        vector_context = ""
        if needs_vector:
            try:
                from app.services.hybrid_rag import vector_rag_service
                rag_results = vector_rag_service.search(message, top_k=3)
                if rag_results:
                    context_texts = [r["document"] for r in rag_results]
                    vector_context = "\n".join(context_texts)
                    logger.info("Successfully retrieved vector context")
            except Exception as e:
                logger.error(f"Vector RAG failed: {e}")
        
        # Inject database context into system prompt
        if database_context:
            system_prompt += f"\n\nREAL DATABASE RESULTS:\n{database_context}"
            
        if vector_context:
            system_prompt += f"\n\nKNOWLEDGE BASE CONTEXT (Unstructured Data):\n{vector_context}"
        
        # specialized logic for long context queries could go here
        # Get base provider
        provider = self._get_provider(context_length="short" if len(message) < 5000 else "long")
        
        statuses = self.get_provider_status()
        
        # Build priority queue of available providers
        available_providers = [p for p in ["ollama", "groq", "openrouter", "gemini"] if statuses.get(p)]
        if not available_providers:
            available_providers = ["mock"]
            
        # Ensure the selected provider is first
        if provider in available_providers:
            available_providers.remove(provider)
            available_providers.insert(0, provider)
            
        last_error = None
        for p in available_providers:
            try:
                resp = await self._call_provider(p, message, system_prompt, session_history)
                resp["query_result"] = query_result_data
                return resp
            except Exception as e:
                logger.error(f"Provider {p} failed: {e}. Failing over...")
                last_error = e
                
        # If all fail, return generic message without exposing raw exception
        logger.error(f"All AI providers failed. Last error: {last_error}")
        return {
            "text": "All AI providers are currently unavailable. Please try again later.",
            "action": None,
            "provider": "error",
            "query_result": query_result_data
        }

    async def _call_provider(self, provider: str, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        """
        Dispatches call to specific provider implementation.
        """
        logger.info(f"Routing request to: {provider}")
        
        if provider == "groq":
            return self._call_groq(message, system_prompt, history)
        elif provider == "gemini":
            return self._call_gemini(message, system_prompt, history)
        elif provider == "openrouter":
            return self._call_openrouter(message, system_prompt, history)
        elif provider == "ollama":
            return self._call_ollama(message, system_prompt, history)
        elif provider == "mock":
            return await self._call_mock_provider(message, system_prompt, history)
        else:
            raise ValueError("Unknown provider")



    def _call_openrouter(self, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        if not self.openrouter_client: raise Exception("OpenRouter not configured")
        
        # Robust list of verified free models (Llama 3 family and strong backups)
        models = [
            "openrouter/free", # Auto-select best free model
            "meta-llama/llama-3.3-70b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "openai/gpt-oss-120b:free",
            "qwen/qwen3-coder:free"
        ]
        
        last_error = None
        
        for model in models:
            try:
                # print(f"Trying OpenRouter model: {model}")
                completion = self.openrouter_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    extra_headers={
                        "HTTP-Referer": "http://localhost:5173", # Recommended by OpenRouter
                        "X-Title": "ERIS AI Assistant"
                    }
                )
                
                raw_text = completion.choices[0].message.content
                text, action_data = self._extract_action(raw_text)
                
                # Simplify provider name for UI
                model_name = model.split('/')[1].split(':')[0] if '/' in model else model
                return {"text": text, "action": action_data, "provider": f"OpenRouter ({model_name})"}
                
            except Exception as e:
                # print(f"Model {model} failed: {e}")
                last_error = e
                continue
        
        # If all models fail
        raise last_error or Exception("All OpenRouter models failed")

    def _extract_action(self, text: str) -> tuple[str, Optional[Dict]]:
        """
        Extracts structured JSON actions from identifying tags.
        """
        import re
        action_payload = None
        clean_text = text
        
        # Regex for <<ACTION>>...<<END_ACTION>>
        match = re.search(r"<<ACTION>>(.*?)<<END_ACTION>>", text, re.DOTALL)
        if match:
            try:
                action_json = match.group(1)
                action_payload = json.loads(action_json)
                clean_text = text.replace(match.group(0), "").strip()
            except Exception as e:
                logger.error(f"Failed to parse action: {e}")
                
        return clean_text, action_payload

    def _call_groq(self, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        if not self.groq_client: raise Exception("Groq not configured")
        
        # Construct messages
        messages = [{"role": "system", "content": system_prompt}]
        # Convert history format if needed (assuming incoming is compatible)
        # Simplified for brevity -> assuming history is [{"role": "user", "content": ...}]
        # ... logic to convert history ...
        messages.append({"role": "user", "content": message})
        
        completion = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        raw_text = completion.choices[0].message.content
        text, action = self._extract_action(raw_text)
        
        return {"text": text, "action": action, "provider": "Groq Llama 3.3"}

    def _call_gemini(self, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        if not self.gemini_key: raise Exception("Gemini not configured")
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Gemini handles conversation history differently (object based), implementing simplified version
        full_prompt = f"{system_prompt}\n\nUser: {message}" 
        
        response = model.generate_content(full_prompt)
        text, action = self._extract_action(response.text)
        
        return {"text": text, "action": action, "provider": "Gemini 1.5 Flash"}



    def _call_ollama(self, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        # Simple REST call to local Ollama
        payload = {
            "model": "llama3",
            "prompt": f"{system_prompt}\n\nUser: {message}",
            "stream": False
        }
        
        try:
            response = requests.post(f"{self.ollama_base_url}/api/generate", json=payload)
            if response.status_code == 200:
                raw_text = response.json().get("response", "")
                text, action = self._extract_action(raw_text)
                return {"text": text, "action": action, "provider": "Ollama (Local)"}
            else:
                raise Exception(f"Ollama Error: {response.text}")
        except Exception as e:
             # If Ollama fails, return a simulated offline response
             return {
                 "text": "Offline Mode: AI Service is unreachable. (Ollama connection failed)",
                 "action": None,
                 "provider": "Offline"
             }

    async def _call_mock_provider(self, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        """
        Simulates AI responses using ACTUAL DATABASE DATA for demo purposes.
        """
        lower_msg = message.lower()
        
        try:
            async with AsyncSessionLocal() as session:
                # 1. Greetings
                if any(w in lower_msg for w in ['hello', 'hi', 'hey', 'namaste']):
                    total_orders = await session.scalar(text("SELECT COUNT(*) FROM sales")) or 0
                    return {
                        "text": f"Hello! I am ERIS AI Assistant. I'm running in **Demo Mode** with actual data from {total_orders:,} orders. Ask me about:\n\n- 'What is the total revenue?'\n- 'Show me low stock items'\n- 'What are the top selling products?'",
                        "action": None,
                        "provider": "Demo Mode (Real Data)"
                    }
                    
                # 2. Revenue Queries - USE ACTUAL DATA
                if 'revenue' in lower_msg or 'sales' in lower_msg:
                    total_revenue = float(await session.scalar(text("SELECT COALESCE(SUM(total_amount), 0) FROM sales")))
                    total_orders = await session.scalar(text("SELECT COUNT(*) FROM sales")) or 0
                    avg_order = total_revenue / total_orders if total_orders else 0
                    
                    # Get top categories from products based on sales
                    top_cats_res = await session.execute(text("SELECT c.name, SUM(si.quantity) as q FROM sale_items si JOIN products p ON si.product_id = p.id LEFT JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY q DESC LIMIT 3"))
                    cat_list = [f"{i+1}. {row[0].title() if row[0] else 'Uncategorized'}: {row[1]:,} items sold" for i, row in enumerate(top_cats_res)]
                    top_cat_text = "\n".join(cat_list)
                    
                    return {
                        "text": f"📊 **Revenue Analysis** (from {total_orders:,} actual orders):\n\n**Total Revenue:** ₹{total_revenue:,.2f} (₹{total_revenue/10000000:.2f} Crore)\n**Total Orders:** {total_orders:,}\n**Average Order Value:** ₹{avg_order:,.2f}\n\n**Top 3 Categories:**\n{top_cat_text}\n\nWould you like a detailed breakdown by month or category?",
                        "action": None,
                        "provider": "Demo Mode (Real Data)"
                    }
                    
                # 3. Low Stock Queries - USE ACTUAL DATA
                if 'low' in lower_msg and 'stock' in lower_msg:
                    low_stock_res = await session.execute(text("SELECT p.name, i.current_stock FROM inventory i JOIN products p ON i.product_id = p.id WHERE i.current_stock < 50 LIMIT 5"))
                    low_stock_rows = low_stock_res.fetchall()
                    low_count = await session.scalar(text("SELECT COUNT(*) FROM inventory WHERE current_stock < 50")) or 0
                    
                    items_text = "\n".join([f"{i+1}. **{r[0]}**: {r[1]} units" for i, r in enumerate(low_stock_rows)])
                    
                    action_json = '{"type": "navigate", "data": {"page": "/inventory"}}'
                    msg = f"🚨 **Low Stock Analysis**\n\nFound **{low_count:,} items** running low (below 50 units).\n\n**Sample Items:**\n{items_text}\n\n**Recommendation:** Restock these items to prevent stockouts.\n\n<<ACTION>>{action_json}<<END_ACTION>>"
                    
                    return {
                        "text": msg,
                        "action": {"type": "navigate", "data": {"page": "/inventory"}},
                        "provider": "Demo Mode (Real Data)"
                    }
                
                # 4. Top Products/Selling - USE ACTUAL DATA
                if any(phrase in lower_msg for phrase in ['top product', 'top selling', 'best seller', 'popular', 'categories']):
                    top_cats_res = await session.execute(text("SELECT c.name, SUM(si.quantity) as q FROM sale_items si JOIN products p ON si.product_id = p.id LEFT JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY q DESC LIMIT 5"))
                    products_text = "\n".join([f"{i+1}. **{row[0].title() if row[0] else 'Uncategorized'}**: {row[1]:,} items sold" for i, row in enumerate(top_cats_res)])
                    
                    return {
                        "text": f"🏆 **Top 5 Product Categories** (by sales volume):\n\n{products_text}\n\nThese categories represent the highest volume in our catalog. Would you like sales performance for these categories?",
                        "action": None,
                        "provider": "Demo Mode (Real Data)"
                    }
                
                # 5. Inventory/Stock General
                if 'stock' in lower_msg or 'inventory' in lower_msg:
                    total_products = await session.scalar(text("SELECT COUNT(*) FROM products")) or 0
                    low_stock = await session.scalar(text("SELECT COUNT(*) FROM inventory WHERE current_stock < 50")) or 0
                    
                    return {
                        "text": f"📦 **Inventory Status**\n\n**Total Products:** {total_products:,}\n**Low Stock Items:** {low_stock:,} (below 50 units)\n\nInventory health is **moderate**. Recommend reviewing low stock items.",
                        "action": None,
                        "provider": "Demo Mode (Real Data)"
                    }
                
                # 6. Customer Queries
                if 'customer' in lower_msg or 'credit' in lower_msg:
                    total_customers = await session.scalar(text("SELECT COUNT(*) FROM customers")) or 0
                    
                    msg = f"👥 **Customer Insights**\n\n**Total Customers:** {total_customers:,}\n"
                    
                    # Preferences
                    sms = await session.scalar(text("SELECT COUNT(*) FROM customers WHERE allow_sms = true")) or 0
                    calls = await session.scalar(text("SELECT COUNT(*) FROM customers WHERE allow_calls = true")) or 0
                    
                    max_pref_count = max(sms, calls)
                    if max_pref_count > 0:
                        if max_pref_count == sms: max_pref = "SMS"
                        else: max_pref = "Calls"
                        pct = (max_pref_count / total_customers) * 100 if total_customers else 0
                        msg += f"\nMost customers prefer {max_pref} communication ({pct:.1f}%)."
                        
                    return {
                        "text": msg,
                        "action": None,
                        "provider": "Demo Mode (Real Data)"
                    }
                
                # 7. General Fallback
                total_orders = await session.scalar(text("SELECT COUNT(*) FROM sales")) or 0
                fallback_msg = f"I understand you're asking about **\"{message}\"**.\n\nI'm running in **Demo Mode** with access to {total_orders:,} real orders. Try asking:\n- \"What is the total revenue?\"\n- \"Show me low stock items\"\n- \"What are the top selling products?\"\n- \"How many customers have credit?\""
                return {
                    "text": fallback_msg,
                    "action": None,
                    "provider": "Demo Mode (Real Data)"
                }
        except Exception as e:
            logger.error(f"Mock provider DB failure: {e}")
            return {
                "text": "I don't have access to current data right now.",
                "action": None,
                "provider": "Mock (Unavailable)"
            }

    def get_provider_status(self) -> Dict[str, bool]:
        """
        Returns the availability status of all providers.
        'mock' is always True — it is the built-in Demo Mode that requires no API key.
        """
        # Check if Ollama is actually reachable
        ollama_alive = False
        try:
            import requests as _req
            r = _req.get(f"{self.ollama_base_url}/api/tags", timeout=1)
            ollama_alive = r.status_code == 200
        except Exception:
            pass

        return {
            "groq": bool(self.groq_client),
            "gemini": bool(self.gemini_key),
            "openrouter": bool(self.openrouter_client),
            "ollama": ollama_alive,
            "mock": True  # Always available — no API key required (Demo Mode)
        }

# Singleton Instance
ai_service = AIService()
