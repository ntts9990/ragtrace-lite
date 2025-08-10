"""
Dashboard services - unified interface using modular services

This module maintains backward compatibility while using the new modular structure.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..db.manager import DatabaseManager
from .data_service import DataService
from .stats_service import StatsService
from .report_service import ReportService
from .utils_service import UtilsService

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Unified dashboard service combining all functionality
    
    This class acts as a facade for the modular services,
    maintaining backward compatibility with existing code.
    """
    
    def __init__(self, db_path: str = "data/ragtrace.db"):
        """
        Initialize dashboard service with all sub-services
        
        Args:
            db_path: Path to database file
        """
        # Initialize database manager
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize sub-services
        self.data_service = DataService(self.db_manager)
        self.stats_service = StatsService(self.db_manager)
        self.report_service = ReportService()
        self.utils_service = UtilsService()
        
        logger.info(f"Dashboard service initialized with DB: {db_path}")
    
    # === Data Service Methods (delegated) ===
    
    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get all evaluation reports with summary metrics"""
        return self.data_service.get_all_reports()
    
    def get_report_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed report information"""
        return self.data_service.get_report_details(run_id)
    
    def get_question_details(self, run_id: str) -> List[Dict[str, Any]]:
        """Get question-level details for a run"""
        return self.data_service.get_question_details(run_id)
    
    def get_runs_by_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Get all runs for a specific dataset"""
        return self.data_service.get_runs_by_dataset(dataset_name)
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent evaluation runs"""
        return self.data_service.get_recent_runs(limit)
    
    # === Stats Service Methods (delegated) ===
    
    def get_time_series_stats(self, window_hours: int = 24) -> Dict[str, Any]:
        """Get time series statistics for recent evaluations"""
        return self.stats_service.get_time_series_stats(window_hours)
    
    def perform_ab_test(self, group_a_ids: List[str], group_b_ids: List[str]) -> Dict[str, Any]:
        """Perform A/B test between two groups of runs"""
        return self.stats_service.perform_ab_test(group_a_ids, group_b_ids)
    
    # === Report Service Methods (delegated) ===
    
    def generate_synthetic_ab_data(
        self, 
        num_runs: int = 10, 
        improvement: float = 0.1
    ) -> Tuple[List[Dict], List[Dict]]:
        """Generate synthetic A/B test data for demo purposes"""
        return self.report_service.generate_synthetic_ab_data(num_runs, improvement)
    
    def generate_synthetic_questions(
        self, 
        num_questions: int = 20,
        language: str = 'ko'
    ) -> List[Dict[str, Any]]:
        """Generate synthetic question-answer pairs for testing"""
        return self.report_service.generate_synthetic_questions(num_questions, language)
    
    def generate_demo_report(self, language: str = 'ko') -> Dict[str, Any]:
        """Generate a complete demo report for testing"""
        return self.report_service.generate_demo_report(language)
    
    # === Utils Service Methods (delegated) ===
    
    def analyze_question_scores(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze question-level scores and provide insights"""
        return self.utils_service.analyze_question_scores(items)
    
    def calculate_improvement_rate(
        self,
        old_scores: Dict[str, float], 
        new_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate improvement rate between two score sets"""
        return self.utils_service.calculate_improvement_rate(old_scores, new_scores)
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string"""
        return self.utils_service.format_duration(seconds)
    
    def get_status_color(self, score: float) -> str:
        """Get color code based on score"""
        return self.utils_service.get_status_color(score)
    
    # === Additional convenience methods ===
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get overall summary statistics for all evaluations
        
        Returns:
            Summary statistics including counts, averages, trends
        """
        try:
            all_runs = self.get_all_reports()
            
            if not all_runs:
                return {
                    'total_evaluations': 0,
                    'average_score': 0,
                    'best_run': None,
                    'worst_run': None,
                    'recent_trend': 'stable'
                }
            
            # Calculate average scores
            scores = []
            for run in all_runs:
                run_scores = []
                for key, value in run.items():
                    if key.startswith('metric_') and value is not None:
                        run_scores.append(value)
                if run_scores:
                    scores.append(sum(run_scores) / len(run_scores))
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Find best and worst runs
            runs_with_scores = [(run, score) for run, score in zip(all_runs, scores)]
            runs_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            best_run = runs_with_scores[0][0] if runs_with_scores else None
            worst_run = runs_with_scores[-1][0] if runs_with_scores else None
            
            # Get recent trend
            recent_stats = self.get_time_series_stats(24)
            trend = recent_stats.get('overall_trend', 'stable')
            
            return {
                'total_evaluations': len(all_runs),
                'average_score': avg_score,
                'best_run': best_run,
                'worst_run': worst_run,
                'recent_trend': trend
            }
            
        except Exception as e:
            logger.error(f"Error getting summary statistics: {e}")
            return {
                'total_evaluations': 0,
                'average_score': 0,
                'best_run': None,
                'worst_run': None,
                'recent_trend': 'unknown',
                'error': str(e)
            }


# For backward compatibility, create a default instance
_default_service = None


def get_dashboard_service(db_path: str = "data/ragtrace.db") -> DashboardService:
    """
    Get or create dashboard service instance
    
    Args:
        db_path: Path to database file
        
    Returns:
        DashboardService instance
    """
    global _default_service
    if _default_service is None:
        _default_service = DashboardService(db_path)
    return _default_service