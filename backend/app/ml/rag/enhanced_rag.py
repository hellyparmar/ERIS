"""
Enhanced RAG System for Retail AI Assistant
Multi-source retrieval: products, sales, insights, forecasts
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import logging

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """
    Enhanced Retrieval-Augmented Generation system for retail assistant.
    Indexes and retrieves from: products, sales, insights, forecasts
    """

    def __init__(self, db_path: str = "./chroma_db", embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG service.
        
        Args:
            db_path: ChromaDB persistence directory
            embedding_model: Sentence transformer model for embeddings
        """
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        
        # Initialize sentence transformer
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB with new client API
        if chromadb is None:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")
        
        # Use new ChromaDB client API
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create collections for different data types
        self.product_collection = self.client.get_or_create_collection(
            name="products",
            metadata={"description": "Product catalog with metadata"}
        )
        self.sales_collection = self.client.get_or_create_collection(
            name="sales",
            metadata={"description": "Sales transactions and patterns"}
        )
        self.insights_collection = self.client.get_or_create_collection(
            name="insights",
            metadata={"description": "Forecast insights, anomalies, recommendations"}
        )

    def index_products(self, products: List[Dict[str, Any]]) -> None:
        """
        Index products with rich metadata.
        
        Args:
            products: List of product dicts with name, category, description, price, stock
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for product in products:
                product_id = str(product.get('id', hash(product['name'])))
                
                # Create rich text representation
                text_content = f"""
                Product: {product.get('name', 'Unknown')}
                Category: {product.get('category', 'General')}
                Description: {product.get('description', 'No description')}
                Price: ₹{product.get('price', 0)}
                Stock Level: {product.get('stock', 0)} units
                Margin: {product.get('margin', 0)}%
                Last Sold: {product.get('last_sold', 'Unknown')}
                """
                
                documents.append(text_content)
                metadatas.append({
                    "type": "product",
                    "product_id": product_id,
                    "name": product.get('name', ''),
                    "category": product.get('category', ''),
                    "price": str(product.get('price', 0)),
                    "stock": str(product.get('stock', 0)),
                })
                ids.append(f"product_{product_id}")
            
            self.product_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Indexed {len(products)} products")
            
        except Exception as e:
            logger.error(f"Error indexing products: {e}")
            raise

    def index_sales(self, sales: List[Dict[str, Any]]) -> None:
        """
        Index sales transactions and extract patterns.
        
        Args:
            sales: List of sales records
        """
        try:
            if not sales:
                return
            
            documents = []
            metadatas = []
            ids = []
            
            for i, sale in enumerate(sales):
                sale_id = str(sale.get('id', i))
                
                # Create rich text with sale patterns
                text_content = f"""
                Sales Transaction
                Date: {sale.get('date', 'Unknown')}
                Amount: ₹{sale.get('total_amount', 0)}
                Outlet: {sale.get('outlet', 'Unknown')}
                Products: {sale.get('product_count', 0)} items
                Customer Type: {sale.get('customer_type', 'Regular')}
                Payment: {sale.get('payment_method', 'Cash')}
                Items: {sale.get('items_description', 'General goods')}
                """
                
                documents.append(text_content)
                metadatas.append({
                    "type": "sale",
                    "sale_id": sale_id,
                    "outlet": sale.get('outlet', ''),
                    "date": str(sale.get('date', '')),
                    "amount": str(sale.get('total_amount', 0)),
                    "customer_type": sale.get('customer_type', ''),
                })
                ids.append(f"sale_{sale_id}")
            
            self.sales_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Indexed {len(sales)} sales records")
            
        except Exception as e:
            logger.error(f"Error indexing sales: {e}")
            raise

    def index_insights(self, insights: List[Dict[str, Any]]) -> None:
        """
        Index insights: forecasts, anomalies, recommendations.
        
        Args:
            insights: List of insight dicts
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, insight in enumerate(insights):
                insight_id = str(insight.get('id', i))
                
                text_content = f"""
                {insight.get('type', 'Insight').title()}
                Product: {insight.get('product', 'General')}
                Metric: {insight.get('metric', 'Unknown')}
                
                Observation: {insight.get('observation', 'No details')}
                Confidence: {insight.get('confidence', 0)}%
                Recommendation: {insight.get('recommendation', 'Monitor closely')}
                
                Timeline: {insight.get('timeline', 'Immediate')}
                Priority: {insight.get('priority', 'Medium')}
                """
                
                documents.append(text_content)
                metadatas.append({
                    "type": "insight",
                    "insight_id": insight_id,
                    "insight_type": insight.get('type', 'general'),
                    "product": insight.get('product', ''),
                    "metric": insight.get('metric', ''),
                    "priority": insight.get('priority', 'medium'),
                })
                ids.append(f"insight_{insight_id}")
            
            self.insights_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Indexed {len(insights)} insights")
            
        except Exception as e:
            logger.error(f"Error indexing insights: {e}")
            raise

    def search(self, query: str, top_k: int = 5, collection: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Semantic search across indexed data.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            collection: Specific collection to search ('products', 'sales', 'insights' or None for all)
        
        Returns:
            List of search results with scores and metadata
        """
        try:
            results = []
            
            # Search specified collection or all
            collections = [collection] if collection else ['products', 'sales', 'insights']
            
            # Ensure collections exist
            collections_map = {
                'products': self.product_collection,
                'sales': self.sales_collection,
                'insights': self.insights_collection
            }
            
            for coll_name in collections:
                if coll_name not in collections_map:
                    logger.warning(f"Collection {coll_name} not found")
                    continue
                    
                coll = collections_map[coll_name]
                
                search_results = coll.query(
                    query_texts=[query],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )
                
                if search_results and search_results['documents']:
                    for i, doc in enumerate(search_results['documents'][0]):
                        # Convert distance to similarity score (0-1)
                        distance = search_results['distances'][0][i]
                        similarity = 1 / (1 + distance)
                        
                        result = {
                            "collection": coll_name,
                            "document": doc,
                            "similarity": round(similarity, 3),
                            "metadata": search_results['metadatas'][0][i] if search_results['metadatas'] else {},
                        }
                        results.append(result)
            
            # Sort by similarity and return top_k
            results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:top_k]
            
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def answer_question(self, question: str, llm_fn, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate answer using LLM + retrieved context.
        
        Args:
            question: User's question
            llm_fn: Function to call LLM (should accept prompt and return response)
            context: Optional additional context dict
        
        Returns:
            Dict with answer, sources, confidence
        """
        try:
            # Search for relevant context
            search_results = self.search(question, top_k=5)
            
            # Build context from search results
            context_text = "\n".join([
                f"- {r['document'][:200]}... (relevance: {r['similarity']})"
                for r in search_results
            ])
            
            # Build prompt with context
            prompt = f"""
You are a retail intelligence assistant. Answer the following question using the provided context.
Be concise, factual, and cite sources when relevant.

Question: {question}

Relevant Context:
{context_text if context_text else 'No specific context found. Use general retail knowledge.'}

Answer:
"""
            
            # Call LLM
            answer = llm_fn(prompt)
            
            # Extract sources from metadata
            sources = [
                {
                    "type": r['metadata'].get('type', 'unknown'),
                    "id": r['metadata'].get('product_id', r['metadata'].get('sale_id', '')),
                    "relevance": r['similarity']
                }
                for r in search_results[:3]
            ]
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": np.mean([r['similarity'] for r in search_results]) if search_results else 0.0,
                "search_results_count": len(search_results),
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": "I encountered an error processing your question. Please try again.",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
            }

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics on indexed data."""
        try:
            return {
                "products": self.product_collection.count(),
                "sales": self.sales_collection.count(),
                "insights": self.insights_collection.count(),
                "total": self.product_collection.count() + self.sales_collection.count() + self.insights_collection.count(),
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def clear_collections(self) -> None:
        """Clear all indexed data."""
        try:
            self.client.delete_collection("products")
            self.client.delete_collection("sales")
            self.client.delete_collection("insights")
            
            # Recreate
            self.product_collection = self.client.get_or_create_collection("products")
            self.sales_collection = self.client.get_or_create_collection("sales")
            self.insights_collection = self.client.get_or_create_collection("insights")
            
            logger.info("Collections cleared")
        except Exception as e:
            logger.error(f"Error clearing collections: {e}")
