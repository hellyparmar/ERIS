import logging
import httpx
from typing import List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    def __init__(self):
        # Use lazy detection — provider is set on first use, not at import time
        # This prevents blocking the server startup if Ollama is still booting
        self._provider: Optional[str] = None
        logger.info("LLMProvider initialized (provider will be auto-detected on first call)")

    @property
    def provider(self) -> str:
        if self._provider is None:
            detected = self._detect_provider()
            self._provider = detected
        return self._provider  # always str here

    def _detect_provider(self) -> str:
        """Auto-detect available provider: Ollama → Anthropic → OpenAI"""
        if settings.USE_OLLAMA:
            try:
                # Short timeout so it doesn't block startup
                with httpx.Client(timeout=2.0) as client:
                    response = client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                    if response.status_code == 200:
                        logger.info("Ollama detected and ready")
                        return "ollama"
            except Exception:
                logger.warning(
                    f"Ollama not reachable at {settings.OLLAMA_BASE_URL} — checking cloud fallbacks"
                )

        if settings.ANTHROPIC_API_KEY:
            logger.info("Using Anthropic as AI provider")
            return "anthropic"

        if settings.OPENAI_API_KEY:
            logger.info("Using OpenAI as AI provider")
            return "openai"

        logger.warning("No AI provider available. Start Ollama or add API keys to .env")
        return "none"

    def is_available(self) -> bool:
        """Check if any provider is working"""
        return self.provider != "none"

    async def chat(self, messages: List[dict]) -> str:
        """Call the appropriate provider's chat completion API"""
        p = self.provider
        if p == "ollama":
            return await self._chat_ollama(messages)
        elif p == "anthropic":
            return await self._chat_anthropic(messages)
        elif p == "openai":
            return await self._chat_openai(messages)
        else:
            return (
                "No AI provider is configured or reachable. "
                "Start Ollama (`ollama serve`) or add ANTHROPIC_API_KEY / OPENAI_API_KEY to backend/.env"
            )

    async def _chat_ollama(self, messages: List[dict]) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        model_name = getattr(settings, "OLLAMA_MODEL", "ibm/granite3.3:2b-base")
        if not model_name: 
            model_name = "ibm/granite3.3:2b-base"
            
        payload = {"model": model_name, "messages": messages, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            err_msg = e.response.text
            logger.error(f"Ollama HTTP error {e.response.status_code}: {err_msg}")
            self._provider = None
            return f"Ollama HTTP {e.response.status_code} Error: {err_msg}"
        except Exception as e:
            logger.error(f"Ollama chat error: {repr(e)}")
            # Reset so next call re-detects provider
            self._provider = None
            return f"Ollama Error: {repr(e)}"
        return ""

    async def _chat_anthropic(self, messages: List[dict]) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {"model": "claude-3-5-sonnet-20240620", "max_tokens": 1024, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json().get("content", [{}])[0].get("text", "")
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            return f"Anthropic Error: {e}"
        return ""

    async def _chat_openai(self, messages: List[dict]) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o", "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return f"OpenAI Error: {e}"
        return ""


# Singleton — provider detected lazily on first call
llm = LLMProvider()
