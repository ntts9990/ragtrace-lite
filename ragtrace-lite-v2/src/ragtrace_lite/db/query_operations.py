"""Query operations for database management"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class QueryOperations:
    """Read and query operations for evaluations"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all evaluation runs"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM evaluations 
                ORDER BY timestamp DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get specific evaluation run by ID"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM evaluations WHERE run_id = ?", 
                (run_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_runs_by_ids(self, run_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple runs by IDs"""
        if not run_ids:
            return []
        
        with self.connection_manager.get_connection() as conn:
            placeholders = ','.join('?' * len(run_ids))
            cursor = conn.execute(
                f"SELECT * FROM evaluations WHERE run_id IN ({placeholders})",
                run_ids
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_runs_by_window(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        """Get runs within time window"""
        cutoff_time = (datetime.now() - timedelta(hours=window_hours)).isoformat()
        
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT e.*, 
                       GROUP_CONCAT(ms.metric_name || ':' || ms.mean_value) as metrics
                FROM evaluations e
                LEFT JOIN metric_summary ms ON e.run_id = ms.run_id
                WHERE e.timestamp > ?
                GROUP BY e.run_id
                ORDER BY e.timestamp DESC
            """, (cutoff_time,))
            
            results = []
            for row in cursor.fetchall():
                run = dict(row)
                # Parse metrics
                if run.get('metrics'):
                    metrics_dict = {}
                    for metric_str in run['metrics'].split(','):
                        if ':' in metric_str:
                            name, value = metric_str.split(':', 1)
                            try:
                                metrics_dict[name] = float(value)
                            except ValueError:
                                metrics_dict[name] = value
                    run['metrics'] = metrics_dict
                results.append(run)
            
            return results
    
    def get_metric_values_for_runs(self, run_ids: List[str], 
                                  metric_name: str) -> Dict[str, float]:
        """Get specific metric values for multiple runs"""
        if not run_ids:
            return {}
        
        with self.connection_manager.get_connection() as conn:
            placeholders = ','.join('?' * len(run_ids))
            cursor = conn.execute(f"""
                SELECT run_id, mean_value 
                FROM metric_summary 
                WHERE run_id IN ({placeholders}) AND metric_name = ?
            """, run_ids + [metric_name])
            
            return {row['run_id']: row['mean_value'] for row in cursor.fetchall()}
    
    def get_metric_summaries(self, run_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all metric summaries for a run"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM metric_summary 
                WHERE run_id = ?
            """, (run_id,))
            
            summaries = {}
            for row in cursor.fetchall():
                summaries[row['metric_name']] = {
                    'mean': row['mean_value'],
                    'std': row['std_value'],
                    'min': row['min_value'],
                    'max': row['max_value'],
                    'median': row['median_value']
                }
            return summaries
    
    def get_evaluation_items(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all evaluation items for a run"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT ei.*, 
                       GROUP_CONCAT(im.metric_name || ':' || im.metric_value) as metrics
                FROM evaluation_items ei
                LEFT JOIN item_metrics im ON ei.id = im.item_id
                WHERE ei.run_id = ?
                GROUP BY ei.id
                ORDER BY ei.item_index
            """, (run_id,))
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Parse contexts
                if item.get('contexts'):
                    item['contexts'] = json.loads(item['contexts'])
                # Parse metrics
                if item.get('metrics'):
                    metrics_dict = {}
                    for metric_str in item['metrics'].split(','):
                        if ':' in metric_str:
                            name, value = metric_str.split(':', 1)
                            try:
                                metrics_dict[name] = float(value)
                            except ValueError:
                                metrics_dict[name] = value
                    item['metrics'] = metrics_dict
                items.append(item)
            
            return items
    
    def get_environment_stats(self) -> Dict[str, Any]:
        """Get environment statistics"""
        with self.connection_manager.get_connection() as conn:
            # Count evaluations by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM evaluations 
                GROUP BY status
            """)
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Count by provider
            cursor = conn.execute("""
                SELECT llm_provider, COUNT(*) as count 
                FROM evaluations 
                WHERE llm_provider IS NOT NULL
                GROUP BY llm_provider
            """)
            provider_counts = {row['llm_provider']: row['count'] for row in cursor.fetchall()}
            
            # Get total counts
            cursor = conn.execute("SELECT COUNT(*) as total FROM evaluations")
            total_evaluations = cursor.fetchone()['total']
            
            cursor = conn.execute("SELECT COUNT(*) as total FROM evaluation_items")
            total_items = cursor.fetchone()['total']
            
            return {
                'total_evaluations': total_evaluations,
                'total_items': total_items,
                'status_distribution': status_counts,
                'provider_distribution': provider_counts
            }