"""
R-DIOS RAG (Retrieval-Augmented Generation) Engine
Uses ChromaDB as vector store + sentence-transformers for embeddings
Ollama (Mistral) for generation

Flow:
1. Ingest: Convert business data → text chunks → embeddings → ChromaDB
2. Query:  User question → embed → similarity search → retrieve top-K chunks
3. Generate: Build context prompt → Ollama → response
"""
import os
import json
from typing import List, Optional
from datetime import date, timedelta

CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # Free, fast, runs locally


class RAGEngine:
    def __init__(self):
        self._collection = None
        self._embedder = None
        self._initialized = False

    def _init(self):
        """Lazy initialization — only load models when first used."""
        if self._initialized:
            return
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            client = chromadb.PersistentClient(path=CHROMA_PATH)
            self._collection = client.get_or_create_collection(
                name="rdios_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            self._embedder = SentenceTransformer(EMBEDDING_MODEL)
            self._initialized = True
        except ImportError as e:
            print(f"RAG dependencies not installed: {e}")
            self._initialized = False

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using sentence-transformers."""
        self._init()
        if not self._initialized or not self._embedder:
            return [[0.0] * 384] * len(texts)
        return self._embedder.encode(texts, convert_to_numpy=True).tolist()

    def ingest_business_context(self, db) -> int:
        """
        Build the knowledge base from live database data.
        Call this once at startup and periodically (e.g. daily via Celery).
        Returns number of documents ingested.
        """
        self._init()
        if not self._initialized:
            return 0

        from app.models.schema import Sale, Product, Outlet, Inventory, Alert, Invoice
        from sqlalchemy import func

        documents = []
        doc_ids = []
        metadatas = []

        # 1. Outlet profiles (static facts)
        outlets = db.query(Outlet).filter(Outlet.is_active == True).all()
        for o in outlets:
            text = (
                f"Outlet '{o.name}' is a {o.outlet_type} store located in {o.city}, {o.state}. "
                f"It is {'currently active' if o.is_active else 'inactive'}."
            )
            documents.append(text)
            doc_ids.append(f"outlet_{o.id}")
            metadatas.append({"type": "outlet", "outlet_id": o.id})

        # 2. Top products by revenue (past 30 days)
        top_products = (
            db.query(Product.name, Product.category, func.sum(Sale.total_amount).label("rev"))
            .join(Sale, Sale.product_id == Product.id)
            .filter(Sale.sale_date >= date.today() - timedelta(days=30))
            .group_by(Product.id, Product.name, Product.category)
            .order_by(func.sum(Sale.total_amount).desc())
            .limit(20).all()
        )
        for p in top_products:
            text = (
                f"Product '{p.name}' in category '{p.category}' generated ₹{p.rev:,.0f} "
                f"revenue in the last 30 days. It is a top-performing product."
            )
            documents.append(text)
            doc_ids.append(f"product_rev_{p.name.replace(' ', '_')}")
            metadatas.append({"type": "product_performance"})

        # 3. Low stock alerts (current)
        low_stock = (
            db.query(Inventory, Product.name, Outlet.name.label("oname"))
            .join(Product, Product.id == Inventory.product_id)
            .join(Outlet, Outlet.id == Inventory.outlet_id)
            .filter(Inventory.current_stock <= Inventory.reorder_level)
            .limit(30).all()
        )
        for inv, pname, oname in low_stock:
            severity = "OUT OF STOCK" if inv.current_stock == 0 else "LOW STOCK"
            text = (
                f"{severity}: '{pname}' at '{oname}' has only {inv.current_stock} units remaining "
                f"(reorder level: {inv.reorder_level} units). Immediate restocking needed."
            )
            documents.append(text)
            doc_ids.append(f"alert_inv_{inv.id}")
            metadatas.append({"type": "inventory_alert", "outlet_id": inv.outlet_id})

        # 4. Monthly revenue by outlet
        month_start = date.today().replace(day=1)
        outlet_rev = (
            db.query(Outlet.name, Outlet.city, func.sum(Sale.total_amount).label("rev"))
            .join(Sale, Sale.outlet_id == Outlet.id)
            .filter(Sale.sale_date >= month_start)
            .group_by(Outlet.id, Outlet.name, Outlet.city)
            .order_by(func.sum(Sale.total_amount).desc())
            .all()
        )
        if outlet_rev:
            rev_lines = "; ".join([f"{r.name} (₹{r.rev:,.0f})" for r in outlet_rev])
            text = f"This month's outlet revenue performance: {rev_lines}."
            documents.append(text)
            doc_ids.append("monthly_outlet_revenue")
            metadatas.append({"type": "monthly_summary"})

        # 5. GST compliance summary
        gst_invoices = db.query(func.count(Invoice.id), func.sum(Invoice.total_gst)).first()
        if gst_invoices:
            text = (
                f"GST compliance summary: Total {gst_invoices[0]} invoices processed, "
                f"total GST collected: ₹{(gst_invoices[1] or 0):,.0f}. "
                f"Next GST filing deadline is typically the 20th of the following month."
            )
            documents.append(text)
            doc_ids.append("gst_summary")
            metadatas.append({"type": "compliance"})

        # 6. Indian retail knowledge base (static domain knowledge)
        STATIC_KNOWLEDGE = [
            ("india_gst_basics", "gst", "In India, GST rates for FMCG products are: 0% for fresh produce, 5% for essential foods (atta, dal, milk, salt), 12% for processed foods and beverages, 18% for personal care products, 28% for luxury items. GSTR-3B must be filed by the 20th of each month."),
            ("india_retail_seasons", "seasonality", "Indian retail sales peak during: Diwali season (Oct-Nov, +100-110% uplift), Holi (March, +65%), Summer months (April-June, beverages +35%), Independence Day (August, +40%). The slowest months are February and July."),
            ("inventory_best_practices", "operations", "Best practices for Indian retail inventory: maintain 2-3 weeks of safety stock for fast-moving items, use ABC analysis (A=top 20% products=80% revenue), reorder when stock reaches 2 weeks of daily average sales, track expiry dates for perishables."),
            ("payment_modes_india", "payments", "Indian retail payment modes: UPI is the most popular (45-50% of transactions), cash remains significant (25%), card payments (15-20%), credit terms for B2B. UPI apps: PhonePe, Google Pay, Paytm."),
            ("tally_integration", "technology", "Tally Prime is India's most popular accounting software. R-DIOS can sync invoices to Tally via its REST API. Tally maintains ledgers, vouchers, and generates Form 26AS, GSTR reports automatically."),
            ("petpooja_context", "system", "R-DIOS is built for multi-outlet retail businesses similar to PetPooja's ecosystem. It handles inventory across outlets, allows managers to view their outlet-specific data, while upper management sees all outlets in the Enterprise view."),
        ]
        for doc_id, doc_type, text in STATIC_KNOWLEDGE:
            documents.append(text)
            doc_ids.append(doc_id)
            metadatas.append({"type": doc_type})

        if not documents:
            return 0

        # Embed and upsert into ChromaDB
        embeddings = self._embed(documents)
        self._collection.upsert(
            ids=doc_ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(documents)

    def retrieve(self, query: str, n_results: int = 5) -> List[str]:
        """Find the most relevant knowledge chunks for a query."""
        self._init()
        if not self._initialized or not self._collection:
            return []
        try:
            query_embedding = self._embed([query])[0]
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self._collection.count()),
            )
            return results["documents"][0] if results["documents"] else []
        except Exception:
            return []

    def generate(self, query: str, context_chunks: List[str], outlet_name: Optional[str] = None) -> str:
        """Generate a response using Ollama with retrieved context."""
        import requests

        context_text = "\n".join([f"• {chunk}" for chunk in context_chunks])
        outlet_line = f" You are answering for the store manager of '{outlet_name}'." if outlet_name else ""

        prompt = f"""You are R-DIOS, an AI assistant for an Enterprise Retail Intelligence System used by Indian retailers.{outlet_line}

RELEVANT BUSINESS CONTEXT (from live data):
{context_text}

INSTRUCTIONS:
- Answer based on the context above when relevant
- Use Indian number formatting (₹, lakhs, crores)
- Be specific and actionable
- Keep response to 3-5 sentences
- If the context doesn't cover the question, use your general retail knowledge

USER QUESTION: {query}

ANSWER:"""

        try:
            res = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": "mistral", "prompt": prompt, "stream": False, "options": {"temperature": 0.2, "num_predict": 300}},
                timeout=30,
            )
            if res.ok:
                return res.json().get("response", "").strip()
        except Exception:
            pass
        return "I'm currently unable to generate a response. Please ensure Ollama is running (`ollama serve`)."

    def query(self, user_question: str, db=None, outlet_name: Optional[str] = None) -> dict:
        """Full RAG pipeline: retrieve + generate."""
        chunks = self.retrieve(user_question, n_results=5) if self._initialized else []
        answer = self.generate(user_question, chunks, outlet_name)
        return {
            "answer": answer,
            "sources_used": len(chunks),
            "rag_enabled": self._initialized,
            "chunks_preview": [c[:100] + "..." for c in chunks[:2]] if chunks else [],
        }


# Global singleton
rag_engine = RAGEngine()
