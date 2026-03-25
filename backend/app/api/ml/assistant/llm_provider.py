import os
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from app.api.config import settings

logger = logging.getLogger(__name__)

class LLMProvider:
    """Unified provider interface for LLMs (Ollama, Anthropic, OpenAI)"""

    def __init__(self):
        self.priority = settings.AI_PROVIDER_PRIORITY
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.openai_key = settings.OPENAI_API_KEY

    def _check_ollama(self) -> bool:
        """Check if local Ollama is reachable"""
        try:
            # We check /api/tags which is lightweight
            response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    async def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Auto-detect and call the best available provider"""
        
        for provider in self.priority:
            if provider == "ollama" and self._check_ollama():
                return await self._call_ollama(prompt, system_prompt)
            
            if provider == "anthropic" and self.anthropic_key:
                return await self._call_anthropic(prompt, system_prompt)
            
            if provider == "openai" and self.openai_key:
                return await self._call_openai(prompt, system_prompt)
        
        return {
            "text": "Fallback: AI Service is unreachable. (No providers configured or reachable)",
            "provider": "none",
            "success": False
        }

    async def _call_ollama(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Local Ollama (Free/Student Friendly)"""
        logger.info("Calling Ollama (Local)")
        payload = {
            "model": "llama3",
            "prompt": f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt,
            "stream": False
        }
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            if response.status_code == 200:
                return {
                    "text": response.json().get("response", ""),
                    "provider": "ollama",
                    "success": True
                }
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
        
        return {"success": False}

    async def _call_anthropic(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Anthropic Claude API"""
        logger.info("Calling Anthropic Claude")
        # For simplicity, using requests directly or if library installed, but requests is safer for 'student-friendly'
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307", # Haiku is cheaper/student friendly
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
            if response.status_code == 200:
                return {
                    "text": response.json()["content"][0]["text"],
                    "provider": "anthropic",
                    "success": True
                }
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")
            
        return {"success": False}

    async def _call_openai(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """OpenAI API"""
        logger.info("Calling OpenAI")
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo", # Student friendly cost
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                return {
                    "text": response.json()["choices"][0]["message"]["content"],
                    "provider": "openai",
                    "success": True
                }
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            
        return {"success": False}

llm_provider = LLMProvider()
