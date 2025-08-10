"""Statistical analysis service for dashboard"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats

logger = logging.getLogger(__name__)


class StatsService:
    """Handle time series analysis, forecasting, and A/B testing"""
    
    def __init__(self, db_manager):
        """
        Initialize stats service with database manager
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
    
    def get_time_series_stats(self, window_hours: int = 24) -> Dict[str, Any]:
        """
        Get time series statistics for recent evaluations
        
        Args:
            window_hours: Time window in hours
            
        Returns:
            Time series statistics
        """
        try:
            runs = self.db_manager.get_runs_by_window(window_hours)
            
            if not runs:
                return self._get_empty_time_series_stats()
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(runs)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # Calculate statistics
            metrics = ['faithfulness', 'answer_relevancy', 'context_precision']
            stats_data = {}
            
            for metric in metrics:
                if f'metric_{metric}' in df.columns or metric in df.columns:
                    col_name = f'metric_{metric}' if f'metric_{metric}' in df.columns else metric
                    values = df[col_name].dropna()
                    
                    if len(values) > 0:
                        stats_data[metric] = {
                            'mean': float(values.mean()),
                            'std': float(values.std()),
                            'min': float(values.min()),
                            'max': float(values.max()),
                            'trend': self._calculate_trend(values),
                            'values': values.tolist(),
                            'timestamps': values.index.strftime('%Y-%m-%d %H:%M').tolist()
                        }
            
            # Calculate overall performance
            overall_scores = []
            for _, row in df.iterrows():
                scores = []
                for metric in metrics:
                    col_name = f'metric_{metric}' if f'metric_{metric}' in df.columns else metric
                    if col_name in row and pd.notna(row[col_name]):
                        scores.append(row[col_name])
                if scores:
                    overall_scores.append(np.mean(scores))
            
            # Generate forecast
            forecast = self._calculate_forecast(overall_scores) if len(overall_scores) > 2 else None
            
            return {
                'window_hours': window_hours,
                'total_runs': len(runs),
                'metrics': stats_data,
                'overall_trend': self._calculate_trend(pd.Series(overall_scores)) if overall_scores else 'stable',
                'forecast': forecast,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating time series stats: {e}")
            return self._get_empty_time_series_stats()
    
    def _get_empty_time_series_stats(self) -> Dict[str, Any]:
        """Return empty time series stats structure"""
        return {
            'window_hours': 0,
            'total_runs': 0,
            'metrics': {},
            'overall_trend': 'stable',
            'forecast': None,
            'last_update': datetime.now().isoformat()
        }
    
    def _calculate_trend(self, series: pd.Series) -> str:
        """
        Calculate trend direction from time series
        
        Args:
            series: Pandas series of values
            
        Returns:
            Trend direction: 'improving', 'declining', or 'stable'
        """
        if len(series) < 2:
            return 'stable'
        
        # Linear regression
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series.values, 1)
        
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_forecast(self, values: List[float], periods: int = 5) -> List[float]:
        """
        Simple moving average forecast
        
        Args:
            values: Historical values
            periods: Number of periods to forecast
            
        Returns:
            Forecasted values
        """
        if len(values) < 3:
            return []
        
        # Use simple exponential smoothing
        alpha = 0.3
        forecast = []
        last_value = values[-1]
        
        for _ in range(periods):
            # Exponential smoothing
            next_value = alpha * last_value + (1 - alpha) * np.mean(values[-3:])
            forecast.append(float(next_value))
            last_value = next_value
        
        return forecast
    
    def perform_ab_test(self, group_a_ids: List[str], group_b_ids: List[str]) -> Dict[str, Any]:
        """
        Perform A/B test between two groups of runs
        
        Args:
            group_a_ids: Run IDs for group A
            group_b_ids: Run IDs for group B
            
        Returns:
            A/B test results with statistical significance
        """
        try:
            # Get runs for both groups
            group_a_runs = self.db_manager.get_runs_by_ids(group_a_ids)
            group_b_runs = self.db_manager.get_runs_by_ids(group_b_ids)
            
            if not group_a_runs or not group_b_runs:
                return {
                    'error': 'Insufficient data for A/B test',
                    'group_a_size': len(group_a_runs),
                    'group_b_size': len(group_b_runs)
                }
            
            # Extract metrics
            metrics_a = self._extract_metrics_from_runs(group_a_runs)
            metrics_b = self._extract_metrics_from_runs(group_b_runs)
            
            results = {}
            
            for metric in ['faithfulness', 'answer_relevancy', 'context_precision']:
                if metric in metrics_a and metric in metrics_b:
                    values_a = metrics_a[metric]
                    values_b = metrics_b[metric]
                    
                    if len(values_a) > 0 and len(values_b) > 0:
                        # Perform t-test
                        t_stat, p_value = stats.ttest_ind(values_a, values_b)
                        
                        # Calculate effect size (Cohen's d)
                        cohens_d = self._calculate_cohens_d(values_a, values_b)
                        
                        results[metric] = {
                            'group_a_mean': float(np.mean(values_a)),
                            'group_a_std': float(np.std(values_a)),
                            'group_b_mean': float(np.mean(values_b)),
                            'group_b_std': float(np.std(values_b)),
                            'difference': float(np.mean(values_b) - np.mean(values_a)),
                            't_statistic': float(t_stat),
                            'p_value': float(p_value),
                            'significant': p_value < 0.05,
                            'cohens_d': float(cohens_d),
                            'effect_size': self._interpret_cohens_d(cohens_d)
                        }
            
            return {
                'group_a_size': len(group_a_runs),
                'group_b_size': len(group_b_runs),
                'metrics': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error performing A/B test: {e}")
            return {'error': str(e)}
    
    def _extract_metrics_from_runs(self, runs: List[Dict]) -> Dict[str, List[float]]:
        """Extract metric values from runs"""
        metrics = {}
        
        for run in runs:
            for key, value in run.items():
                if key.startswith('metric_') and value is not None:
                    metric_name = key.replace('metric_', '')
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    metrics[metric_name].append(float(value))
        
        return metrics
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0
        
        return (np.mean(group2) - np.mean(group1)) / pooled_std
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d value"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"