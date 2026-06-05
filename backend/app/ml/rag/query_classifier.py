"""
Query Classifier for Retail Assistant
Classifies query types and extracts entities
"""

import re
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Classify retail queries and extract relevant entities."""

    # Query type patterns
    QUERY_PATTERNS = {
        "factual": [
            r"what (is|are|was|were)\b",
            r"tell.*about",
            r"how many",
            r"which",
            r"list",
        ],
        "analytical": [
            r"why (did|do|has|have)",
            r"what (caused|driven|led to)",
            r"explain",
            r"reason for",
            r"impact of",
        ],
        "forecast": [
            r"will|shall|predict|forecast|expect|anticipate",
            r"what will.*be",
            r"how will",
            r"when will",
            r"projection",
        ],
        "recommendation": [
            r"should.*do|should.*order|should.*stock",
            r"recommend|suggest|advice",
            r"best.*action|best.*way",
            r"what to do",
            r"next step",
        ],
        "comparison": [
            r"compare|versus|vs|better|worse",
            r"difference between",
            r"how (does|do).*compare",
            r"which.*better",
        ],
    }

    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "product_name": r"\b(?:product|item)\s+([A-Za-z0-9\s]+?)(?:\s+(?:sales|stock|price|revenue)|\?|$)",
        "date_range": r"(?:last|past|previous)\s+(day|week|month|quarter|year)|(?:from|between).*?(?:to|and)",
        "outlet": r"(?:outlet|store|shop|branch|location)\s+([A-Za-z0-9\s]+?)(?:\s+(?:had|has|sold)|\?|$)",
        "metric": r"(?:sales|revenue|stock|inventory|profit|margin|volume|units|qty)",
        "time_period": r"(?:today|yesterday|last week|last month|last quarter|last year|this week)",
    }

    def classify_query(self, question: str) -> str:
        """
        Classify query into one of: factual, analytical, forecast, recommendation, comparison.
        
        Args:
            question: User's question
        
        Returns:
            Query type string
        """
        question_lower = question.lower().strip()
        
        # Check patterns in priority order (more specific first)
        # Check comparison first since it can contain "which"
        for pattern in self.QUERY_PATTERNS.get("comparison", []):
            if re.search(pattern, question_lower, re.IGNORECASE):
                logger.info(f"Query classified as 'comparison': {question[:50]}")
                return "comparison"
        
        # Then check forecast
        for pattern in self.QUERY_PATTERNS.get("forecast", []):
            if re.search(pattern, question_lower, re.IGNORECASE):
                logger.info(f"Query classified as 'forecast': {question[:50]}")
                return "forecast"
        
        # Then check recommendation
        for pattern in self.QUERY_PATTERNS.get("recommendation", []):
            if re.search(pattern, question_lower, re.IGNORECASE):
                logger.info(f"Query classified as 'recommendation': {question[:50]}")
                return "recommendation"
        
        # Then check analytical
        for pattern in self.QUERY_PATTERNS.get("analytical", []):
            if re.search(pattern, question_lower, re.IGNORECASE):
                logger.info(f"Query classified as 'analytical': {question[:50]}")
                return "analytical"
        
        # Then check factual (default catch-all)
        for pattern in self.QUERY_PATTERNS.get("factual", []):
            if re.search(pattern, question_lower, re.IGNORECASE):
                logger.info(f"Query classified as 'factual': {question[:50]}")
                return "factual"
        
        # Default to factual if no match
        return "factual"

    def extract_entities(self, question: str) -> Dict[str, any]:
        """
        Extract named entities from question.
        
        Args:
            question: User's question
        
        Returns:
            Dict with extracted entities: product_name, outlet, metric, date_range, time_period
        """
        entities = {
            "product_name": None,
            "outlet": None,
            "metric": None,
            "date_range": None,
            "time_period": None,
            "raw_query": question,
        }
        
        try:
            # Product name extraction
            product_match = re.search(
                self.ENTITY_PATTERNS["product_name"],
                question,
                re.IGNORECASE
            )
            if product_match:
                entities["product_name"] = product_match.group(1).strip()
            
            # Outlet extraction
            outlet_match = re.search(
                self.ENTITY_PATTERNS["outlet"],
                question,
                re.IGNORECASE
            )
            if outlet_match:
                entities["outlet"] = outlet_match.group(1).strip()
            
            # Metric extraction
            metric_match = re.search(
                self.ENTITY_PATTERNS["metric"],
                question,
                re.IGNORECASE
            )
            if metric_match:
                entities["metric"] = metric_match.group(0).lower()
            
            # Time period extraction
            time_match = re.search(
                self.ENTITY_PATTERNS["time_period"],
                question,
                re.IGNORECASE
            )
            if time_match:
                entities["time_period"] = time_match.group(0).lower()
                entities["date_range"] = self._parse_time_period(time_match.group(0))
            
            # Date range extraction
            if not entities["date_range"]:
                date_match = re.search(
                    self.ENTITY_PATTERNS["date_range"],
                    question,
                    re.IGNORECASE
                )
                if date_match:
                    entities["date_range"] = date_match.group(0).lower()
            
            logger.info(f"Extracted entities: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return entities

    def _parse_time_period(self, time_str: str) -> Dict[str, str]:
        """
        Parse time period string to start and end dates.
        
        Args:
            time_str: Time period string (e.g., "last week")
        
        Returns:
            Dict with 'start_date' and 'end_date'
        """
        today = datetime.now().date()
        
        if "today" in time_str:
            return {"start_date": str(today), "end_date": str(today)}
        elif "yesterday" in time_str:
            yesterday = today - timedelta(days=1)
            return {"start_date": str(yesterday), "end_date": str(yesterday)}
        elif "last week" in time_str:
            start = today - timedelta(days=7)
            return {"start_date": str(start), "end_date": str(today)}
        elif "last month" in time_str:
            start = today - timedelta(days=30)
            return {"start_date": str(start), "end_date": str(today)}
        elif "last quarter" in time_str:
            start = today - timedelta(days=90)
            return {"start_date": str(start), "end_date": str(today)}
        elif "last year" in time_str:
            start = today - timedelta(days=365)
            return {"start_date": str(start), "end_date": str(today)}
        else:
            return {}

    def get_query_intent(self, question: str) -> Dict[str, any]:
        """
        Get complete query intent: type + entities.
        
        Args:
            question: User's question
        
        Returns:
            Dict with query_type and entities
        """
        return {
            "query_type": self.classify_query(question),
            "entities": self.extract_entities(question),
            "question": question,
        }
