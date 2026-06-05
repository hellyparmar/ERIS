"""
ERIS RAG Pipeline
Retrieval-Augmented Generation for Retail Intelligence
"""

import os
import json
import hashlib
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, text
import redis
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from app.models import (
    SaleTransaction as Sale, Product, Inventory, Alert, Forecast, ForecastResult,
    PurchaseOrder, PurchaseOrderItem, User
)
from app.models.sale import SaleItem
from app.models.employee_models import Employee
from app.models.users import UserStore


class ERISRAGPipeline:
    """
    RAG Pipeline for ERIS AI Assistant
    Provides contextual retail intelligence using vector search
    """

    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    LLM_MODEL = 'mistral'
    OLLAMA_HOST = os.getenv('RAG_OLLAMA_HOST', 'http://localhost:11434')
    TOP_K = 5

    def __init__(self, db: Session, outlet_id: int, redis_client: redis.Redis):
        self.db = db
        self.outlet_id = outlet_id
        self.redis_client = redis_client
        self.embedder = SentenceTransformer(self.EMBEDDING_MODEL)
        self.chroma_client = chromadb.HttpClient(
            host=os.getenv('CHROMA_HOST', 'localhost'),
            port=int(os.getenv('CHROMA_PORT', 8000))
        )
        self.collection_name = f"eris_outlet_{self.outlet_id}"

    def build_knowledge_chunks(self) -> List[Dict[str, Any]]:
        """
        Build knowledge chunks from various data sources
        """
        chunks = []
        today = datetime.now().date()

        try:
            # 1. Today's sales summary
            sales_query = self.db.query(
                func.sum(Sale.total_amount).label('total_revenue'),
                func.count(Sale.id).label('transaction_count')
            ).filter(
                func.date(Sale.created_at) == today,
                Sale.outlet_id == self.outlet_id
            ).first()

            top_products = self.db.query(
                Product.name,
                func.sum(SaleItem.quantity).label('total_quantity'),
                func.sum(SaleItem.total_price).label('total_revenue')
            ).join(SaleItem, SaleItem.product_id == Product.id)\
             .join(Sale, Sale.id == SaleItem.sale_id)\
             .filter(
                 func.date(Sale.created_at) == today,
                 Sale.outlet_id == self.outlet_id
             ).group_by(Product.id)\
             .order_by(desc('total_revenue'))\
             .limit(5).all()

            if sales_query.total_revenue:
                sales_text = f"Today's sales summary: Total revenue ₹{sales_query.total_revenue:.2f}, {sales_query.transaction_count} transactions. Top 5 products: " + ", ".join([f"{p.name} (₹{p.total_revenue:.2f})" for p in top_products])
                chunks.append({
                    'text': sales_text,
                    'source': 'sales_summary',
                    'outlet_id': self.outlet_id,
                    'date': str(today)
                })

            # 2. Inventory alerts
            alerts = self.db.query(Alert)\
                .filter(
                    Alert.outlet_id == self.outlet_id,
                    Alert.acknowledged == False
                ).all()

            for alert in alerts:
                alert_text = f"Inventory alert: {alert.message} (Severity: {alert.severity}, Type: {alert.alert_type})"
                chunks.append({
                    'text': alert_text,
                    'source': 'inventory_alert',
                    'outlet_id': self.outlet_id,
                    'date': str(today)
                })

            # 3. Forecast for next 7 days
            forecast_end = today + timedelta(days=7)
            forecasts = self.db.query(Forecast)\
                .filter(
                    Forecast.outlet_id == self.outlet_id,
                    Forecast.forecast_date.between(today, forecast_end)
                ).all()

            if forecasts:
                forecast_text = "7-day forecast: " + ", ".join([f"{f.forecast_date}: ₹{f.predicted_sales:.2f}" for f in forecasts])
                chunks.append({
                    'text': forecast_text,
                    'source': 'forecast',
                    'outlet_id': self.outlet_id,
                    'date': str(today)
                })

            # 4. Top 5 suppliers
            thirty_days_ago = today - timedelta(days=30)
            top_suppliers = self.db.query(
                PurchaseOrder.supplier_id,
                func.count(PurchaseOrder.id).label('order_count')
            ).filter(
                PurchaseOrder.outlet_id == self.outlet_id,
                func.date(PurchaseOrder.created_at) >= thirty_days_ago
            ).group_by(PurchaseOrder.supplier_id)\
             .order_by(desc('order_count'))\
             .limit(5).all()

            if top_suppliers:
                supplier_text = "Top suppliers (last 30 days): " + ", ".join([f"Supplier {s.supplier_id} ({s.order_count} orders)" for s in top_suppliers])
                chunks.append({
                    'text': supplier_text,
                    'source': 'suppliers',
                    'outlet_id': self.outlet_id,
                    'date': str(today)
                })

            # 5. Employee count and active shifts
            employee_count = self.db.query(func.count(Employee.id))\
                .filter(Employee.outlet_id == self.outlet_id).scalar()

            active_shifts = self.db.query(func.count(UserStore.id))\
                .filter(
                    UserStore.outlet_id == self.outlet_id,
                    UserStore.is_active == True
                ).scalar()

            employee_text = f"Employee information: {employee_count} total employees, {active_shifts} active shifts"
            chunks.append({
                'text': employee_text,
                'source': 'employees',
                'outlet_id': self.outlet_id,
                'date': str(today)
            })

            # 6. GST HSN rates
            try:
                with open('data/hsn_rates.json', 'r') as f:
                    hsn_data = json.load(f)

                for hsn, details in hsn_data.items():
                    hsn_text = f"HSN {hsn}: {details.get('description', 'N/A')} - GST Rate: {details.get('gst_rate', 'N/A')}%"
                    chunks.append({
                        'text': hsn_text,
                        'source': 'hsn_rates',
                        'outlet_id': self.outlet_id,
                        'date': 'static'
                    })
            except FileNotFoundError:
                chunks.append({
                    'text': 'HSN rates data not available',
                    'source': 'hsn_rates',
                    'outlet_id': self.outlet_id,
                    'date': 'static'
                })

        except Exception as e:
            # Log error but don't fail the entire pipeline
            print(f"Error building knowledge chunks: {e}")
            chunks.append({
                'text': 'Error retrieving some knowledge data',
                'source': 'error',
                'outlet_id': self.outlet_id,
                'date': str(today)
            })

        return chunks

    def upsert_to_chromadb(self, chunks: List[Dict[str, Any]]):
        """
        Upsert knowledge chunks to ChromaDB
        """
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"outlet_id": str(self.outlet_id)}
            )

            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.encode(texts).tolist()

            ids = []
            metadatas = []
            for chunk in chunks:
                chunk_id = hashlib.md5(f"{chunk['source']}_{chunk['date']}_{chunk['outlet_id']}".encode()).hexdigest()
                ids.append(chunk_id)
                metadatas.append({
                    'source': chunk['source'],
                    'outlet_id': str(chunk['outlet_id']),
                    'date': chunk['date']
                })

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )

        except Exception as e:
            print(f"Error upserting to ChromaDB: {e}")
            raise

    def retrieve(self, query: str) -> List[str]:
        """
        Retrieve relevant knowledge chunks
        """
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            query_embedding = self.embedder.encode([query]).tolist()[0]

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=self.TOP_K
            )

            return results['documents'][0] if results['documents'] else []

        except Exception as e:
            print(f"Error retrieving from ChromaDB: {e}")
            return []

    def generate_response(self, query: str, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate AI response using RAG
        """
        try:
            # Retrieve relevant context
            context_chunks = self.retrieve(query)
            context = "\n".join(context_chunks)

            # Build conversation history (last 5 exchanges)
            history_text = ""
            if conversation_history:
                recent_history = conversation_history[-10:]  # Last 5 exchanges (user + assistant)
                history_text = "\n".join([f"User: {h.get('user', '')}\nAssistant: {h.get('assistant', '')}" for h in recent_history])

            # Build prompt
            system_prompt = "You are ERIS, an AI assistant for retail businesses. Answer questions using ONLY the provided context. If the answer is not in the context, say so clearly. Never make up numbers or facts."

            full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nConversation History:\n{history_text}\n\nUser: {query}\n\nAssistant:"

            # Call Ollama
            response = requests.post(
                f"{self.OLLAMA_HOST}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get('response', 'No response generated')
            else:
                return "The AI assistant is temporarily unavailable. Please try again in a moment."

        except requests.exceptions.RequestException:
            return "The AI assistant is temporarily unavailable. Please try again in a moment."
        except Exception as e:
            print(f"Error generating response: {e}")
            return "An error occurred while processing your request."

    def refresh_knowledge_base(self):
        """
        Refresh the knowledge base (called nightly by Celery)
        """
        try:
            chunks = self.build_knowledge_chunks()
            self.upsert_to_chromadb(chunks)
            print(f"Knowledge base refreshed for outlet {self.outlet_id}")
        except Exception as e:
            print(f"Error refreshing knowledge base: {e}")
            raise