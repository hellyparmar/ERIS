"""Grounded, asynchronous AI provider orchestration for ERIS."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

import httpx


logger = logging.getLogger(__name__)


def _enabled(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AIService:
    """Answer retail questions using real ERIS data and optional LLM providers.

    Ollama is the preferred, fully local provider. Groq and OpenRouter are
    optional OpenAI-compatible fallbacks. Provider failures never replace real
    data with invented business figures.
    """

    def __init__(self) -> None:
        self.use_ollama = _enabled(os.getenv("USE_OLLAMA"), default=True)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self.timeout = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "60"))

    def configured_providers(self) -> list[str]:
        providers: list[str] = []
        if self.use_ollama:
            providers.append("ollama")
        if self.groq_key:
            providers.append("groq")
        if self.openrouter_key:
            providers.append("openrouter")
        return providers

    async def provider_status(self, probe_ollama: bool = False) -> dict[str, bool]:
        status = {
            "ollama": self.use_ollama,
            "groq": bool(self.groq_key),
            "openrouter": bool(self.openrouter_key),
            "semantic_layer": True,
        }
        if probe_ollama and self.use_ollama:
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    response = await client.get(f"{self.ollama_base_url}/api/tags")
                status["ollama"] = response.is_success
            except httpx.HTTPError:
                status["ollama"] = False
        return status

    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        session_history: Optional[list] = None,
        execute_templates: bool = True,
        outlet_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        """Generate a response, grounding matched business questions in SQL."""
        query_result, database_context = None, ""
        if execute_templates:
            query_result, database_context = await asyncio.to_thread(self._execute_grounded_query, message, outlet_ids)

        if database_context:
            system_prompt += f"\n\nVERIFIED DATABASE RESULTS:\n{database_context}"

        providers = self.configured_providers()
        if not providers:
            if query_result:
                return self._grounded_fallback(query_result)
            return {
                "text": "No AI provider is configured. Start Ollama locally or configure Groq or OpenRouter.",
                "action": None,
                "provider": "unavailable",
                "query_result": query_result,
            }

        last_provider = None
        for provider in providers:
            last_provider = provider
            try:
                response = await self._call_provider(provider, message, system_prompt, session_history or [])
                response["query_result"] = query_result
                return response
            except Exception as exc:
                logger.warning("AI provider %s failed: %s", provider, exc)

        logger.error("All configured AI providers failed; last attempted provider=%s", last_provider)
        if query_result:
            return self._grounded_fallback(query_result)
        return {
            "text": "All configured AI providers are currently unavailable. Please try again later.",
            "action": None,
            "provider": "error",
            "query_result": query_result,
        }

    @staticmethod
    def _grounded_fallback(query_result: dict[str, Any]) -> dict[str, Any]:
        rows = query_result.get("data", [])
        if not rows:
            text = "The verified database query returned no matching results."
        else:
            lines = [f"I found {len(rows)} verified result{'s' if len(rows) != 1 else ''} in ERIS:"]
            for index, row in enumerate(rows[:8], 1):
                summary = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in row.items())
                lines.append(f"{index}. {summary}")
            if len(rows) > 8:
                lines.append(f"Showing 8 of {len(rows)} results.")
            text = "\n".join(lines)
        return {
            "text": text,
            "provider": "ERIS semantic layer",
            "query_result": query_result,
        }

    @staticmethod
    def _execute_grounded_query(message: str, outlet_ids: Optional[list[int]]) -> tuple[Optional[dict[str, Any]], str]:
        try:
            from app.database import get_db_sync
            from app.services.query_executor import query_executor
            from app.services.semantic_layer import semantic_layer

            template_match = semantic_layer.match_template(message)
            if not template_match:
                return None, ""

            template_name, template_sql = template_match
            scoped_sql, scope_params = semantic_layer.inject_outlet_filter(template_sql, outlet_ids or [])
            with get_db_sync() as db:
                result = query_executor.execute_template_query_with_session(
                    scoped_sql, semantic_layer, db, params=scope_params
                )
            if not result.get("success"):
                logger.warning("Grounding query %s failed", template_name)
                return None, ""

            query_result = {
                "success": True,
                "data": result.get("data", []),
                "row_count": result.get("row_count", 0),
                "execution_time_ms": result.get("execution_time_ms", 0),
                "template_matched": template_name,
            }
            return query_result, query_executor.format_results_for_llm(result)
        except Exception as exc:
            logger.warning("Database grounding failed: %s", exc)
            return None, ""

    async def _call_provider(self, provider: str, message: str, system_prompt: str, history: list) -> dict[str, Any]:
        if provider == "ollama":
            return await self._call_ollama(message, system_prompt, history)
        if provider == "groq":
            return await self._call_openai_compatible(
                provider="Groq",
                url="https://api.groq.com/openai/v1/chat/completions",
                api_key=self.groq_key,
                model=self.groq_model,
                message=message,
                system_prompt=system_prompt,
                history=history,
            )
        if provider == "openrouter":
            return await self._call_openai_compatible(
                provider="OpenRouter",
                url="https://openrouter.ai/api/v1/chat/completions",
                api_key=self.openrouter_key,
                model=self.openrouter_model,
                message=message,
                system_prompt=system_prompt,
                history=history,
                extra_headers={"HTTP-Referer": "https://github.com/hellyparmar/ERIS", "X-Title": "ERIS"},
            )
        raise ValueError("Unsupported AI provider")

    @staticmethod
    def _messages(system_prompt: str, message: str, history: list) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for item in history[-12:]:
            role = "assistant" if item.get("role") in {"assistant", "model"} else "user"
            content = item.get("content")
            if not content and item.get("parts"):
                content = item["parts"][0]
            if isinstance(content, str) and content.strip():
                messages.append({"role": role, "content": content.strip()})
        messages.append({"role": "user", "content": message})
        return messages

    async def _call_openai_compatible(
        self,
        *,
        provider: str,
        url: str,
        api_key: str,
        model: str,
        message: str,
        system_prompt: str,
        history: list,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {api_key}", **(extra_headers or {})}
        payload = {
            "model": model,
            "messages": self._messages(system_prompt, message, history),
            "temperature": 0.2,
            "max_tokens": 900,
        }
        timeout = httpx.Timeout(self.timeout, connect=2)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
        if not response.is_success:
            raise RuntimeError(f"{provider} returned HTTP {response.status_code}")
        raw_text = response.json()["choices"][0]["message"]["content"] or ""
        return {"text": raw_text.strip(), "provider": f"{provider} ({model})"}

    async def _call_ollama(self, message: str, system_prompt: str, history: list) -> dict[str, Any]:
        payload = {
            "model": self.ollama_model,
            "messages": self._messages(system_prompt, message, history),
            "stream": False,
        }
        timeout = httpx.Timeout(self.timeout, connect=2)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{self.ollama_base_url}/api/chat", json=payload)
        if not response.is_success:
            raise RuntimeError(f"Ollama returned HTTP {response.status_code}")
        raw_text = response.json().get("message", {}).get("content", "")
        return {"text": raw_text.strip(), "provider": f"Ollama ({self.ollama_model})"}


ai_service = AIService()
