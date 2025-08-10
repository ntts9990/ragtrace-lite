"""Data retrieval service for dashboard"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataService:
    """Handle all database queries and data fetching operations"""
    
    def __init__(self, db_manager):
        """
        Initialize data service with database manager
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
    
    def get_all_reports(self) -> List[Dict[str, Any]]:
        """
        Get all evaluation reports with summary metrics
        
        Returns:
            List of reports with their metrics
        """
        try:
            # Get all runs
            runs = self.db_manager.get_all_runs()
            
            # Add metrics to each run
            for run in runs:
                run_id = run['run_id']
                metrics = self.db_manager.get_metric_summaries(run_id)
                
                # Flatten metrics for easier display
                for metric_name, metric_data in metrics.items():
                    run[f"metric_{metric_name}"] = metric_data.get('mean', 0)
            
            return runs
            
        except Exception as e:
            logger.error(f"Error fetching reports: {e}")
            return []
    
    def get_report_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed report information
        
        Args:
            run_id: Run identifier
            
        Returns:
            Detailed report data or None
        """
        try:
            # Get basic run info
            run = self.db_manager.get_run_by_id(run_id)
            if not run:
                return None
            
            # Add detailed metrics
            run['metrics'] = self.db_manager.get_metric_summaries(run_id)
            
            # Add evaluation items
            run['items'] = self.db_manager.get_evaluation_items(run_id)
            
            return run
            
        except Exception as e:
            logger.error(f"Error fetching report details: {e}")
            return None
    
    def get_question_details(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get question-level details for a run
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of question details with analysis
        """
        try:
            items = self.db_manager.get_evaluation_items(run_id)
            
            # Analyze each question
            analyzed_items = []
            for item in items:
                metrics = item.get('metrics', {})
                
                # Calculate average score
                scores = [v for v in metrics.values() if v is not None]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                # Determine status
                if avg_score >= 0.8:
                    status = "good"
                    status_text = "우수"
                elif avg_score >= 0.6:
                    status = "warning"
                    status_text = "보통"
                else:
                    status = "poor"
                    status_text = "개선 필요"
                
                analyzed_items.append({
                    'question': item.get('question', ''),
                    'answer': item.get('answer', ''),
                    'contexts': item.get('contexts', []),
                    'metrics': metrics,
                    'average_score': avg_score,
                    'status': status,
                    'status_text': status_text
                })
            
            return analyzed_items
            
        except Exception as e:
            logger.error(f"Error fetching question details: {e}")
            return []
    
    def get_runs_by_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        Get all runs for a specific dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            List of runs for the dataset
        """
        try:
            all_runs = self.db_manager.get_all_runs()
            return [run for run in all_runs if run.get('dataset_name') == dataset_name]
        except Exception as e:
            logger.error(f"Error fetching runs by dataset: {e}")
            return []
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent evaluation runs
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of recent runs
        """
        try:
            runs = self.db_manager.get_all_runs()
            # Runs are already sorted by timestamp desc from DB
            return runs[:limit]
        except Exception as e:
            logger.error(f"Error fetching recent runs: {e}")
            return []