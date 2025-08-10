"""Utility functions for report generation"""

import json
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ReportUtils:
    """Shared utilities for report generation"""
    
    def calculate_summary_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate summary statistics from results
        
        Args:
            results: Evaluation results dictionary
            
        Returns:
            Dictionary with summary statistics
        """
        metrics = results.get("metrics", {})
        items = results.get("items", [])
        
        # Calculate average score
        valid_scores = [v for v in metrics.values() if v is not None]
        average_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        # Determine performance level
        if average_score >= 0.8:
            performance_level = "우수"
            performance_level_en = "Excellent"
            performance_class = "good"
        elif average_score >= 0.6:
            performance_level = "양호"
            performance_level_en = "Good"
            performance_class = "warning"
        else:
            performance_level = "개선 필요"
            performance_level_en = "Needs Improvement"
            performance_class = "poor"
        
        return {
            "total_items": len(items),
            "average_score": average_score,
            "performance_level": performance_level,
            "performance_level_en": performance_level_en,
            "performance_class": performance_class,
            "metrics_count": len(valid_scores)
        }
    
    def generate_json_report(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        dataset_name: str
    ) -> str:
        """
        Generate JSON format report
        
        Args:
            run_id: Evaluation run identifier
            results: Evaluation results
            environment: Environment information
            dataset_name: Name of the dataset
            
        Returns:
            JSON string
        """
        summary_stats = self.calculate_summary_stats(results)
        
        report = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "dataset_name": dataset_name,
            "summary": {
                "total_items": summary_stats["total_items"],
                "average_score": summary_stats["average_score"],
                "performance_level": summary_stats["performance_level_en"],
                "metrics_evaluated": summary_stats["metrics_count"]
            },
            "metrics": results.get("metrics", {}),
            "environment": environment,
            "items_sample": results.get("items", [])[:5]  # Include first 5 items as sample
        }
        
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def get_metric_display_names(self, language: str = "ko") -> Dict[str, str]:
        """
        Get metric display names for specified language
        
        Args:
            language: Language code (ko or en)
            
        Returns:
            Dictionary mapping metric keys to display names
        """
        if language == "ko":
            return {
                "faithfulness": "충실성",
                "answer_relevancy": "답변 관련성",
                "context_precision": "컨텍스트 정밀도",
                "context_recall": "컨텍스트 재현율",
                "answer_correctness": "답변 정확성",
                "ragas_score": "RAGAS 점수"
            }
        else:
            return {
                "faithfulness": "Faithfulness",
                "answer_relevancy": "Answer Relevancy",
                "context_precision": "Context Precision",
                "context_recall": "Context Recall",
                "answer_correctness": "Answer Correctness",
                "ragas_score": "RAGAS Score"
            }
    
    def format_score(self, score: float, precision: int = 3) -> str:
        """
        Format score with specified precision
        
        Args:
            score: Score value
            precision: Number of decimal places
            
        Returns:
            Formatted score string
        """
        if score is None:
            return "N/A"
        return f"{score:.{precision}f}"
    
    def truncate_text(self, text: str, max_length: int = 200) -> str:
        """
        Truncate text to specified length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text with ellipsis if needed
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length] + "..."