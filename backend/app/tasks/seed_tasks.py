import asyncio
import logging
from app.api.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.seed_tasks.run_historical_seed")
def run_historical_seed(self):
    from app.database import AsyncSessionLocal
    from app.seed_database import generate_historical_data
    from app.seed_rag import seed_unstructured_data
    
    async def _run():
        async with AsyncSessionLocal() as session:
            try:
                self.update_state(state='PROGRESS', meta={'message': 'Starting historical data generation'})
                stats = await generate_historical_data(session)
                
                if stats["status"] == "skipped":
                    return stats
                
                # Verification step
                self.update_state(state='PROGRESS', meta={'message': 'Verifying seeded data'})
                from sqlalchemy import text
                
                # Assert admin exists
                res = await session.execute(text("SELECT COUNT(*) FROM users WHERE username='admin'"))
                if res.scalar() == 0:
                    raise Exception("Validation failed: admin user is missing")
                    
                # Assert sales row counts are within expected ranges for 365 days * 5 outlets
                res = await session.execute(text("SELECT COUNT(*) FROM sales"))
                sales_count = res.scalar()
                if sales_count < 10000:
                    raise Exception(f"Validation failed: expected >10000 sales, got {sales_count}")
                
                # Seed RAG database
                self.update_state(state='PROGRESS', meta={'message': 'Ingesting RAG knowledge...'})
                rag_stats = await seed_unstructured_data()
                stats["records"]["rag_documents"] = rag_stats.get("count", 0)
                
                return stats
            except Exception as e:
                logger.error(f"Seeding task failed: {e}", exc_info=True)
                return {"status": "failed", "error": str(e)}

    return asyncio.run(_run())
