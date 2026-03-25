import logging
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

logger = logging.getLogger(__name__)

class AdvancedRAGService:
    def __init__(self):
        self._embeddings = None
        self._vectorstore = None

    def _init_models(self):
        if self._vectorstore is not None:
            return
            
        logger.info("Initializing HuggingFace embeddings for RAG...")
        self._embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Determine the absolute path to chroma_db to ensure persistence
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        chroma_path = os.path.join(base_dir, "chroma_db")

        # Initialize the persistent Chroma VectorStore
        self._vectorstore = Chroma(
            persist_directory=chroma_path,
            embedding_function=self._embeddings
        )

    def retrieve_context(self, question: str, k: int = 5) -> str:
        """Retrieves semantically similar documents based on the question."""
        try:
            self._init_models()
            # Run similarity search directly against the database
            docs = self._vectorstore.similarity_search(question, k=k)

            
            if not docs:
                return "No contextual data available in the current database for this query."
            
            # Formatting the retrieved context
            context = "=== RELEVANT RETAIL INTELLIGENCE DATA ===\n"
            for i, doc in enumerate(docs):
                context += f"- Record {i+1}:\n{doc.page_content}\n"
                
            return context
        except Exception as e:
            logger.error(f"Failed to query Chroma RAG: {e}")
            return "Internal RAG retrieval failed."

# Singleton initialization
rag_service = AdvancedRAGService()
