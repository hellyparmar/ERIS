import logging
import json
from typing import Dict, Any, Optional, List
from app.api.ml.assistant.llm_provider import llm_provider

logger = logging.getLogger(__name__)

class AssistantAgent:
    """R-DIOS AI Assistant Agent"""

    def __init__(self):
        self.system_prompt = """
        You are R-DIOS, an advanced Enterprise Retail Intelligence Assistant.
        Your goal is to help users manage their retail business effectively.
        You have access to sales, inventory, customers, and employee data.
        
        Keep your responses concise, professional, and data-driven.
        If results contain sensitive information, summarize effectively.
        
        Output format:
        - Use Markdown for formatting.
        - Use 📊 for charts reference.
        - Use 🚨 for alerts.
        """

    async def ask(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query and return an AI response"""
        
        full_system_prompt = self.system_prompt
        if context:
            full_system_prompt += f"\n\nCURRENT CONTEXT:\n{context}"
        
        response = await llm_provider.generate(query, full_system_prompt)
        
        # Extract structured actions if present
        text, action = self._parse_enhanced_response(response.get("text", ""))
        
        return {
            "answer": text,
            "action": action,
            "provider": response.get("provider", "unknown"),
            "success": response.get("success", False)
        }

    def _parse_enhanced_response(self, text: str) -> tuple[str, Optional[Dict]]:
        """Extract instructions like <<ACTION>>...<<END_ACTION>>"""
        import re
        action = None
        clean_text = text
        
        match = re.search(r"<<ACTION>>(.*?)<<END_ACTION>>", text, re.DOTALL)
        if match:
            try:
                action = json.loads(match.group(1))
                clean_text = text.replace(match.group(0), "").strip()
            except:
                logger.warning("Failed to parse action JSON from AI response")
                
        return clean_text, action

# Singleton Instance
assistant_agent = AssistantAgent()
