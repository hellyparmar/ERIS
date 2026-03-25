import os
import sys

# Ensure backend root is on python path for script execution
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models.multitenant_models import Product
from app.models.models import Sale

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_rag_database():
    db = SessionLocal()
    
    logger.info("Initializing Embeddings and Vector Store...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    chroma_path = os.path.join(base_dir, "chroma_db")
    
    vectorstore = Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings
    )
    
    documents = []
    
    logger.info("Extracting Products to contextual strings...")
    products = db.query(Product).all()
    for product in products:
        text = f"Product Name: {product.name}\nCategory: {product.category}\nSKU: {product.sku}\nUnit Price: {product.unit_price}\nDead Stock Status: {'Yes' if product.is_dead_stock else 'No'}\nDescription: {product.description if product.description else 'N/A'}"
        documents.append(Document(page_content=text, metadata={"source": "product", "id": str(product.id)}))
        
    logger.info("Extracting Sales to contextual strings...")
    sales = db.query(Sale).limit(500).all()
    for sale in sales:
        items_str = ", ".join([item.product.name for item in sale.items]) if sale.items else "Unknown"
        text = f"Sale Tracking ID: {sale.transaction_id}\nDate: {sale.transaction_date}\nTotal Amount Paid: {sale.total_amount}\nPayment Method: {sale.payment_method}\nItems Purchased: {items_str}"
        documents.append(Document(page_content=text, metadata={"source": "sale", "id": str(sale.id)}))

    if documents:
        logger.info(f"Ingesting {len(documents)} context chunks into Chroma DB...")
        vectorstore.add_documents(documents)
        logger.info("RAG Indexing successfully completed!")
    else:
        logger.warning("No records found in database to index. Try generating mock data first.")
        
    db.close()

if __name__ == "__main__":
    populate_rag_database()
