"""
Offline Transaction Sync Service
Processes queued POS transactions when back online
Per CLAUDE.md Part 2.4
"""
import logging
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.services.pos_service import complete_sale

logger = logging.getLogger(__name__)

def sync_offline_transactions(transactions: List[Dict], db: Session) -> Dict:
    """
    Process batch of offline transactions
    
    Args:
        transactions: List of {cart, payment, cashier_id, offline_timestamp, client_transaction_id}
        db: Database session
    
    Returns:
        {
            'total': int,
            'successful': int,
            'failed': int,
            'results': [{transaction_id, status, error}]
        }
    """
    results = []
    successful = 0
    failed = 0
    
    for txn in transactions:
        try:
            # Check for duplicate transaction_id
            client_txn_id = txn.get('client_transaction_id')
            if client_txn_id:
                existing = db.execute(
                    text("SELECT id FROM sales WHERE transaction_id = :txn_id"),
                    {"txn_id": client_txn_id}
                ).first()
                
                if existing:
                    logger.warning(f"Duplicate transaction {client_txn_id} - skipping")
                    results.append({
                        'client_transaction_id': client_txn_id,
                        'status': 'duplicate',
                        'error': 'Transaction already processed'
                    })
                    failed += 1
                    continue
            
            # Process transaction with ACID guarantees
            result = complete_sale(
                cart=txn['cart'],
                payment=txn['payment'],
                cashier_id=txn['cashier_id'],
                db=db
            )
            
            results.append({
                'client_transaction_id': client_txn_id,
                'server_transaction_id': result['transaction_id'],
                'sale_id': result['sale_id'],
                'status': 'success'
            })
            successful += 1
            logger.info(f"✅ Synced offline transaction: {client_txn_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync transaction {client_txn_id}: {e}")
            results.append({
                'client_transaction_id': client_txn_id,
                'status': 'failed',
                'error': str(e)
            })
            failed += 1
    
    return {
        'total': len(transactions),
        'successful': successful,
        'failed': failed,
        'results': results,
        'synced_at': datetime.now().isoformat()
    }
