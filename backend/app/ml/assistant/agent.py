import logging
from typing import List, Dict
from app.ml.assistant.llm_provider import llm
from app.ml.rag.rag_service import rag_service

logger = logging.getLogger(__name__)

class RetailAssistant:
    def __init__(self):
        self.llm = llm
        self.rag = rag_service

    async def chat(self, question: str, history: List[Dict[str, str]] = None) -> dict:
        """Main chat endpoint enriched by local RAG vectors"""
        if history is None:
            history = []
            
        # 1. Ask RAG for context
        context = self.rag.retrieve_context(question, k=3)
        
        # 2. Re-contextualize the Prompt Grounded on RAG output
        prompt = f"""You are the Enterprise Retail Intelligence AI Assistant.
Use ONLY the following context retrieved from the database to definitively answer the user's question. 
If the answer is NOT strictly contained within the context below, state clearly that you don't have enough verified data, but do your best to assist safely. DO NOT hallucinate prices, quantities, or product names!

{context}

===
User Question: {question}
"""
        
        # Prepare final message payload
        messages = history.copy()
        messages.append({"role": "user", "content": prompt})
        
        # 3. Call the configured LLMProvider (Ollama / Claude / OpenAI)
        try:
            answer = await self.llm.chat(messages)
            
            return {
                "response": answer,
                "provider": self.llm.provider,
                "rag_enhanced": True
            }
        except Exception as e:
            logger.error(f"Chat execution failed: {e}")
            raise

# Initialize globally
retail_agent = RetailAssistant()
