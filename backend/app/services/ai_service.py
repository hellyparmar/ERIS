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
        execute_templates: bool = True,
        outlet_ids: list = None,
        tenant_id: str = None,
    ) -> Dict[str, Any]:
        """
        Main entry point to get AI response.
        Includes database results when a semantic-layer template matches.

        outlet_ids -- list of outlet IDs the requesting user may access
                      (from get_outlet_scope).  Templates that touch `sales`
                      are scoped to these IDs before execution.
        tenant_id  -- user's organization_id (str).  Used to open a
                      get_db_sync(tenant_id=...) session so that PostgreSQL
                      FORCE ROW LEVEL SECURITY policies are satisfied.
                      Must be supplied together with outlet_ids.
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

                    if outlet_ids is not None and tenant_id is not None:
                        # ── Correct path: tenant-scoped session (enforces RLS) ──
                        from app.database import get_db_sync
                        scoped_sql, _scope_params = semantic_layer.inject_outlet_filter(
                            template_sql, outlet_ids
                        )
                        logger.info(
                            f"Executing scoped query tenant={tenant_id} "
                            f"outlet_ids={outlet_ids}"
                        )
                        with get_db_sync(tenant_id=tenant_id) as db:
                            result = query_executor.execute_template_query_with_session(
                                scoped_sql, semantic_layer, db, params=_scope_params
                            )
                    else:
                        # ── Legacy fallback: no tenant context, RLS bypassed ──
                        logger.warning(
                            "generate_response called without outlet_ids/tenant_id "
                            "— RLS will NOT be enforced on this query."
                        )
                        result = query_executor.execute_template_query(template_sql, semantic_layer)

                    if result.get("success"):
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
            raise Exception(f"Ollama connection failed: {e}")

    async def _call_mock_provider(self, message: str, system_prompt: str, history: list) -> Dict[str, Any]:
        """
        Strict fallback that raises an exception when no LLMs are configured.
        Delegates error messaging to the try-catch block in generate_response
        per REQ-AI-02 to explicitly state unavailability without fabricating data.
        """
        raise Exception("No AI providers configured or available.")

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
