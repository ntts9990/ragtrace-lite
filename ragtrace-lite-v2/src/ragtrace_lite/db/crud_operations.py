"""CRUD operations for database management"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class CRUDOperations:
    """Create, Read, Update, Delete operations for evaluations"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    def save_evaluation(self, evaluation_data: Dict[str, Any]) -> str:
        """Save evaluation results to database"""
        run_id = evaluation_data.get('run_id', f"run_{datetime.now().isoformat()}")
        
        with self.connection_manager.get_connection() as conn:
            # Save main evaluation record
            conn.execute("""
                INSERT INTO evaluations (
                    run_id, timestamp, dataset_name, dataset_items,
                    ragas_score, status, error_message, model_name,
                    temperature, llm_provider, embedding_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                datetime.now().isoformat(),
                evaluation_data.get('dataset_name', 'Unknown'),
                evaluation_data.get('dataset_items', 0),
                evaluation_data.get('ragas_score'),
                evaluation_data.get('status', 'completed'),
                evaluation_data.get('error_message'),
                evaluation_data.get('model_name'),
                evaluation_data.get('temperature'),
                evaluation_data.get('llm_provider'),
                evaluation_data.get('embedding_model')
            ))
            
            # Save metric summaries
            if 'metrics' in evaluation_data:
                self._save_metric_summary(conn, run_id, evaluation_data['metrics'])
            
            # Save evaluation items
            if 'items' in evaluation_data:
                self._save_evaluation_items(conn, run_id, evaluation_data['items'])
            
            logger.info(f"Saved evaluation {run_id} to database")
            return run_id
    
    def _save_metric_summary(self, conn, run_id: str, metrics: Dict[str, Any]):
        """Save metric summaries"""
        for metric_name, value in metrics.items():
            if value is not None:
                conn.execute("""
                    INSERT INTO metric_summary (
                        run_id, metric_name, mean_value, std_value,
                        min_value, max_value, median_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id, metric_name,
                    value if isinstance(value, (int, float)) else value.get('mean'),
                    value.get('std') if isinstance(value, dict) else None,
                    value.get('min') if isinstance(value, dict) else None,
                    value.get('max') if isinstance(value, dict) else None,
                    value.get('median') if isinstance(value, dict) else None
                ))
    
    def _save_evaluation_items(self, conn, run_id: str, items: List[Dict[str, Any]]):
        """Save individual evaluation items"""
        for idx, item in enumerate(items):
            # Save item
            cursor = conn.execute("""
                INSERT INTO evaluation_items (
                    run_id, item_index, question, answer,
                    ground_truth, contexts
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run_id, idx,
                item.get('question'),
                item.get('answer'),
                item.get('ground_truth'),
                json.dumps(item.get('contexts', []))
            ))
            item_id = cursor.lastrowid
            
            # Save item metrics
            metrics = item.get('metrics', {})
            for metric_name, value in metrics.items():
                if value is not None:
                    conn.execute("""
                        INSERT INTO item_metrics (
                            item_id, metric_name, metric_value
                        ) VALUES (?, ?, ?)
                    """, (item_id, metric_name, value))
    
    def update_evaluation_status(self, run_id: str, status: str, 
                                error_message: Optional[str] = None) -> bool:
        """Update evaluation status"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE evaluations 
                SET status = ?, error_message = ?
                WHERE run_id = ?
            """, (status, error_message, run_id))
            
            return cursor.rowcount > 0
    
    def delete_evaluation(self, run_id: str) -> bool:
        """Delete evaluation and all related data"""
        with self.connection_manager.get_connection() as conn:
            # Delete in reverse order of foreign key dependencies
            conn.execute("DELETE FROM item_metrics WHERE item_id IN "
                        "(SELECT id FROM evaluation_items WHERE run_id = ?)", (run_id,))
            conn.execute("DELETE FROM evaluation_items WHERE run_id = ?", (run_id,))
            conn.execute("DELETE FROM metric_summary WHERE run_id = ?", (run_id,))
            cursor = conn.execute("DELETE FROM evaluations WHERE run_id = ?", (run_id,))
            
            return cursor.rowcount > 0