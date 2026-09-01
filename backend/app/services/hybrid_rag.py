import logging
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
import os

logger = logging.getLogger(__name__)

class VectorRAGService:
    def __init__(self, db_path="./chroma_db", collection_name="eris_rag"):
        # Make path relative to backend root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, "chroma_db")
        
        self.client = chromadb.PersistentClient(path=full_path)
        self.collection_name = collection_name
        self._embedder = None
        self._collection = None
        
        # Ensure HuggingFace uses a writable directory for downloading models in Docker
        os.environ['HF_HOME'] = '/tmp/hf_cache'
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp/hf_cache'
        logger.info("VectorRAGService initialized (lazy loading embedder).")
        
    def _init_collection(self):
        if self._collection is None:
            # Use DefaultEmbeddingFunction (ONNX) instead of sentence-transformers (PyTorch) 
            # to prevent OOM kills (exit code 137) in the 1GB memory-limited container
            self._embedder = embedding_functions.DefaultEmbeddingFunction()
            
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedder,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        if not documents:
            return
        collection = self._init_collection()
        embeddings = self._embedder(documents)
        collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Upserted {len(documents)} documents to VectorRAGService.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        collection = self._init_collection()
        query_embedding = self._embedder([query])
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        output = []
        if results and results.get("documents") and results["documents"]:
            for i in range(len(results["documents"][0])):
                output.append({
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0
                })
        return output

vector_rag_service = VectorRAGService()
