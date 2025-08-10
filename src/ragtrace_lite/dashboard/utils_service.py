"""Utility service for dashboard operations"""

import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class UtilsService:
    """Common utilities and analysis helpers"""
    
    @staticmethod
    def analyze_question_scores(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze question-level scores and provide insights
        
        Args:
            items: List of evaluation items with metrics
            
        Returns:
            Analysis results with categorization and recommendations
        """
        if not items:
            return {
                'total': 0,
                'categories': {},
                'recommendations': [],
                'worst_performing': [],
                'best_performing': []
            }
        
        # Categorize items by performance
        excellent = []
        good = []
        poor = []
        
        for item in items:
            metrics = item.get('metrics', {})
            scores = [v for v in metrics.values() if v is not None]
            
            if not scores:
                continue
            
            avg_score = sum(scores) / len(scores)
            
            item_summary = {
                'question': item.get('question', '')[:100],
                'answer': item.get('answer', '')[:100],
                'score': avg_score,
                'metrics': metrics
            }
            
            if avg_score >= 0.8:
                excellent.append(item_summary)
            elif avg_score >= 0.6:
                good.append(item_summary)
            else:
                poor.append(item_summary)
        
        # Sort by score
        excellent.sort(key=lambda x: x['score'], reverse=True)
        good.sort(key=lambda x: x['score'], reverse=True)
        poor.sort(key=lambda x: x['score'])
        
        # Generate recommendations
        recommendations = []
        
        if len(poor) > len(excellent):
            recommendations.append({
                'type': 'warning',
                'message': '많은 항목이 개선이 필요합니다. 컨텍스트 품질을 검토해주세요.',
                'message_en': 'Many items need improvement. Please review context quality.'
            })
        
        if poor:
            worst_metrics = {}
            for item in poor:
                for metric, score in item['metrics'].items():
                    if score is not None:
                        if metric not in worst_metrics:
                            worst_metrics[metric] = []
                        worst_metrics[metric].append(score)
            
            # Find worst performing metric
            worst_metric = None
            worst_avg = 1.0
            for metric, scores in worst_metrics.items():
                avg = sum(scores) / len(scores)
                if avg < worst_avg:
                    worst_avg = avg
                    worst_metric = metric
            
            if worst_metric:
                recommendations.append({
                    'type': 'improvement',
                    'metric': worst_metric,
                    'message': f'{worst_metric} 메트릭이 가장 낮은 성능을 보입니다.',
                    'message_en': f'{worst_metric} metric shows the lowest performance.'
                })
        
        return {
            'total': len(items),
            'categories': {
                'excellent': len(excellent),
                'good': len(good),
                'poor': len(poor)
            },
            'excellent_items': excellent[:3],
            'good_items': good[:3],
            'poor_items': poor[:3],
            'recommendations': recommendations,
            'worst_performing': poor[:5],
            'best_performing': excellent[:5]
        }
    
    @staticmethod
    def calculate_improvement_rate(
        old_scores: Dict[str, float], 
        new_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate improvement rate between two score sets
        
        Args:
            old_scores: Previous scores
            new_scores: Current scores
            
        Returns:
            Improvement rates for each metric
        """
        improvements = {}
        
        for metric in old_scores:
            if metric in new_scores:
                old_val = old_scores[metric]
                new_val = new_scores[metric]
                
                if old_val > 0:
                    improvement = ((new_val - old_val) / old_val) * 100
                    improvements[metric] = round(improvement, 2)
        
        return improvements
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in seconds to human-readable string
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}초"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}분"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}시간"
    
    @staticmethod
    def get_status_color(score: float) -> str:
        """
        Get color code based on score
        
        Args:
            score: Score value (0-1)
            
        Returns:
            Color code for UI display
        """
        if score >= 0.8:
            return '#27ae60'  # Green
        elif score >= 0.6:
            return '#f39c12'  # Orange
        else:
            return '#e74c3c'  # Red