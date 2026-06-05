"""
RAG-related Celery tasks
"""

from app.api.celery_app import celery_app
from app.database import SessionLocal
from app.ml.rag.pipeline import ERISRAGPipeline
import redis


@celery_app.task
def refresh_knowledge_base_task(outlet_id: int):
    """
    Refresh knowledge base for a specific outlet
    """
    db = SessionLocal()
    redis_client = redis.Redis(decode_responses=True)

    try:
        pipeline = ERISRAGPipeline(db, outlet_id, redis_client)
        pipeline.refresh_knowledge_base()
    except Exception as e:
        print(f"Error in refresh task for outlet {outlet_id}: {e}")
        raise
    finally:
        db.close()