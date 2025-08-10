"""Database manager - Facade for all database operations"""

import logging
from typing import Dict, List, Optional, Any

from .connection_manager import ConnectionManager
from .crud_operations import CRUDOperations
from .query_operations import QueryOperations

logger = logging.getLogger(__name__)

# Import Pydantic models if available
try:
    from ..models.evaluation import (
        EvaluationResult, EvaluationMetrics, EvaluationItem,
        EvaluationConfig, EvaluationEnvironment, EvaluationStatus
    )
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic models not available, using legacy dict-based approach")


class DatabaseManager:
    """Unified database manager using facade pattern"""
    
    def __init__(self, db_path: str = "data/ragtrace.db"):
        # Initialize managers
        self.connection_manager = ConnectionManager(db_path)
        self.crud = CRUDOperations(self.connection_manager)
        self.query = QueryOperations(self.connection_manager)
        
        # Expose connection manager methods
        self.get_connection = self.connection_manager.get_connection
        self.db_path = self.connection_manager.db_path
    
    # === CRUD Operations (delegated) ===
    
    def save_evaluation(self, evaluation_data: Dict[str, Any]) -> str:
        """Save evaluation results to database"""
        return self.crud.save_evaluation(evaluation_data)
    
    def update_evaluation_status(self, run_id: str, status: str,
                                error_message: Optional[str] = None) -> bool:
        """Update evaluation status"""
        return self.crud.update_evaluation_status(run_id, status, error_message)
    
    def delete_evaluation(self, run_id: str) -> bool:
        """Delete evaluation and all related data"""
        return self.crud.delete_evaluation(run_id)
    
    # === Query Operations (delegated) ===
    
    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all evaluation runs"""
        return self.query.get_all_runs()
    
    def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get specific evaluation run by ID"""
        return self.query.get_run_by_id(run_id)
    
    def get_runs_by_ids(self, run_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple runs by IDs"""
        return self.query.get_runs_by_ids(run_ids)
    
    def get_runs_by_window(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        """Get runs within time window"""
        return self.query.get_runs_by_window(window_hours)
    
    def get_metric_values_for_runs(self, run_ids: List[str],
                                  metric_name: str) -> Dict[str, float]:
        """Get specific metric values for multiple runs"""
        return self.query.get_metric_values_for_runs(run_ids, metric_name)
    
    def get_metric_summaries(self, run_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all metric summaries for a run"""
        return self.query.get_metric_summaries(run_id)
    
    def get_evaluation_items(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all evaluation items for a run"""
        return self.query.get_evaluation_items(run_id)
    
    def get_environment_stats(self) -> Dict[str, Any]:
        """Get environment statistics"""
        return self.query.get_environment_stats()
    
    # === Pydantic Model Support ===
    
    def save_evaluation_model(self, evaluation: 'EvaluationResult') -> str:
        """Save evaluation using Pydantic model"""
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic models not available")
        
        # Convert Pydantic model to dict
        evaluation_data = {
            'run_id': evaluation.run_id,
            'dataset_name': evaluation.dataset_name,
            'dataset_items': evaluation.dataset_items,
            'ragas_score': evaluation.metrics.ragas_score if evaluation.metrics else None,
            'status': evaluation.status.value if evaluation.status else 'completed',
            'error_message': evaluation.error_message,
            'model_name': evaluation.environment.model_name if evaluation.environment else None,
            'temperature': evaluation.environment.temperature if evaluation.environment else None,
            'llm_provider': evaluation.environment.llm_provider if evaluation.environment else None,
            'embedding_model': evaluation.environment.embedding_model if evaluation.environment else None,
            'metrics': evaluation.metrics.dict() if evaluation.metrics else {},
            'items': [self._evaluation_item_to_dict(item) for item in evaluation.items]
        }
        
        return self.save_evaluation(evaluation_data)
    
    def load_evaluation_model(self, run_id: str) -> Optional['EvaluationResult']:
        """Load evaluation as Pydantic model"""
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic models not available")
        
        # Get evaluation data
        eval_data = self.get_run_by_id(run_id)
        if not eval_data:
            return None
        
        # Get metrics
        metrics_data = self.get_metric_summaries(run_id)
        
        # Get items
        items_data = self.get_evaluation_items(run_id)
        
        # Build Pydantic model
        environment = EvaluationEnvironment(
            model_name=eval_data.get('model_name'),
            temperature=eval_data.get('temperature'),
            llm_provider=eval_data.get('llm_provider'),
            embedding_model=eval_data.get('embedding_model')
        )
        
        metrics = EvaluationMetrics(
            ragas_score=eval_data.get('ragas_score'),
            **{k: v.get('mean') for k, v in metrics_data.items()}
        )
        
        items = [
            EvaluationItem(
                question=item.get('question'),
                answer=item.get('answer'),
                ground_truth=item.get('ground_truth'),
                contexts=item.get('contexts', []),
                metrics=item.get('metrics', {})
            )
            for item in items_data
        ]
        
        return EvaluationResult(
            run_id=eval_data['run_id'],
            timestamp=eval_data['timestamp'],
            dataset_name=eval_data['dataset_name'],
            dataset_items=eval_data['dataset_items'],
            metrics=metrics,
            items=items,
            environment=environment,
            status=EvaluationStatus(eval_data.get('status', 'completed')),
            error_message=eval_data.get('error_message')
        )
    
    @staticmethod
    def _evaluation_item_to_dict(item: 'EvaluationItem') -> Dict[str, Any]:
        """Convert EvaluationItem to dict"""
        return {
            'question': item.question,
            'answer': item.answer,
            'ground_truth': item.ground_truth,
            'contexts': item.contexts,
            'metrics': item.metrics
        }