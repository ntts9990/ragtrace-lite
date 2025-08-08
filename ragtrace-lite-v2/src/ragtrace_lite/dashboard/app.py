"""
RAGTrace Dashboard - Interactive Web Interface
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional
import logging
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "ragtrace.db"
RESULTS_PATH = Path(__file__).parent.parent.parent.parent / "results"

class DashboardService:
    """Dashboard business logic"""
    
    @staticmethod
    def get_all_reports() -> List[Dict]:
        """Get all evaluation reports from database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    run_id,
                    dataset_name,
                    timestamp,
                    ragas_score,
                    dataset_items,
                    status,
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                    answer_correctness
                FROM evaluations
                ORDER BY timestamp DESC
                LIMIT 100
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                report = dict(row)
                # Format timestamp for display
                report['timestamp_display'] = datetime.fromisoformat(
                    report['timestamp']
                ).strftime('%Y-%m-%d %H:%M')
                
                # Calculate status based on score
                score = report.get('ragas_score', 0)
                if score >= 0.8:
                    report['status_badge'] = 'success'
                    report['status_text'] = '우수'
                elif score >= 0.6:
                    report['status_badge'] = 'warning'
                    report['status_text'] = '양호'
                else:
                    report['status_badge'] = 'danger'
                    report['status_text'] = '개선필요'
                
                reports.append(report)
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Error fetching reports: {e}")
            return []
    
    @staticmethod
    def get_report_details(run_id: str) -> Optional[Dict]:
        """Get detailed report data"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get main evaluation data
            cursor.execute("""
                SELECT * FROM evaluations WHERE run_id = ?
            """, (run_id,))
            
            eval_data = cursor.fetchone()
            if not eval_data:
                return None
            
            result = dict(eval_data)
            
            # Get environment data
            cursor.execute("""
                SELECT key, value FROM evaluation_env WHERE run_id = ?
            """, (run_id,))
            
            env_data = cursor.fetchall()
            result['environment'] = {row['key']: row['value'] for row in env_data}
            
            # Get sample details if available
            cursor.execute("""
                SELECT * FROM evaluation_items 
                WHERE run_id = ? 
                LIMIT 20
            """, (run_id,))
            
            details = cursor.fetchall()
            result['details'] = [dict(row) for row in details]
            
            conn.close()
            
            # Calculate statistics
            result['statistics'] = DashboardService._calculate_statistics(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching report details: {e}")
            return None
    
    @staticmethod
    def _calculate_statistics(data: Dict) -> Dict:
        """Calculate statistical metrics"""
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                  'context_recall', 'answer_correctness']
        
        scores = []
        for metric in metrics:
            if metric in data and data[metric] is not None:
                scores.append(data[metric])
        
        if not scores:
            return {}
        
        return {
            'mean': np.mean(scores),
            'std': np.std(scores),
            'min': min(scores),
            'max': max(scores),
            'median': np.median(scores),
            'q1': np.percentile(scores, 25),
            'q3': np.percentile(scores, 75),
            'cv': np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else 0
        }
    
    @staticmethod
    def compare_reports(run_ids: List[str]) -> Dict:
        """Compare multiple reports statistically"""
        if len(run_ids) < 2:
            return {'error': '비교하려면 최소 2개의 보고서가 필요합니다'}
        
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            reports = []
            for run_id in run_ids[:4]:  # Max 4 reports for comparison
                cursor.execute("""
                    SELECT * FROM evaluations WHERE run_id = ?
                """, (run_id,))
                
                data = cursor.fetchone()
                if data:
                    reports.append(dict(data))
            
            conn.close()
            
            if len(reports) < 2:
                return {'error': '유효한 보고서를 찾을 수 없습니다'}
            
            # Perform comparison analysis
            comparison = {
                'reports': reports,
                'metrics': {}
            }
            
            metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                      'context_recall', 'answer_correctness', 'ragas_score']
            
            for metric in metrics:
                values = [r.get(metric, 0) for r in reports if r.get(metric) is not None]
                if values:
                    comparison['metrics'][metric] = {
                        'values': values,
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'improvement': values[-1] - values[0] if len(values) >= 2 else 0,
                        'improvement_pct': ((values[-1] - values[0]) / values[0] * 100) if values[0] > 0 else 0
                    }
            
            # Statistical test (if exactly 2 reports)
            if len(reports) == 2:
                from scipy import stats
                
                scores_a = []
                scores_b = []
                
                for metric in metrics[:-1]:  # Exclude ragas_score
                    if reports[0].get(metric) is not None:
                        scores_a.append(reports[0][metric])
                    if reports[1].get(metric) is not None:
                        scores_b.append(reports[1][metric])
                
                if scores_a and scores_b:
                    # Perform t-test
                    t_stat, p_value = stats.ttest_ind(scores_a, scores_b)
                    comparison['statistical_test'] = {
                        'type': 't-test',
                        't_statistic': float(t_stat),
                        'p_value': float(p_value),
                        'significant': p_value < 0.05,
                        'interpretation': '통계적으로 유의미한 차이' if p_value < 0.05 else '유의미한 차이 없음'
                    }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing reports: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_trend_data(days: int = 30) -> Dict:
        """Get trend data for the last N days"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(ragas_score) as avg_score,
                    COUNT(*) as count
                FROM evaluations
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            
            trend = {
                'dates': [],
                'scores': [],
                'counts': []
            }
            
            for row in rows:
                trend['dates'].append(row['date'])
                trend['scores'].append(row['avg_score'])
                trend['counts'].append(row['count'])
            
            conn.close()
            return trend
            
        except Exception as e:
            logger.error(f"Error fetching trend data: {e}")
            return {'dates': [], 'scores': [], 'counts': []}

    @staticmethod
    def get_question_details(run_id: str) -> List[Dict]:
        """Get individual question analysis"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get evaluation details
            cursor.execute("""
                SELECT * FROM evaluation_items 
                WHERE run_id = ?
                ORDER BY item_index
            """, (run_id,))
            
            details = cursor.fetchall()
            
            # Import analyzers
            from ..stats.question_analyzer import QuestionAnalyzer
            analyzer = QuestionAnalyzer()
            
            results = []
            for detail in details:
                detail_dict = dict(detail)
                
                # Parse contexts if it's a string
                if isinstance(detail_dict.get('contexts'), str):
                    try:
                        detail_dict['contexts'] = json.loads(detail_dict['contexts'])
                    except:
                        detail_dict['contexts'] = [detail_dict.get('contexts', '')]
                
                # Parse metrics
                metrics = {
                    'faithfulness': detail_dict.get('faithfulness', 0) or 0,
                    'answer_relevancy': detail_dict.get('answer_relevancy', 0) or 0,
                    'context_precision': detail_dict.get('context_precision', 0) or 0,
                    'context_recall': detail_dict.get('context_recall', 0) or 0,
                    'answer_correctness': detail_dict.get('answer_correctness', 0) or 0
                }
                
                # Analyze question
                analysis = analyzer.analyze_question(detail_dict, metrics)
                
                results.append({
                    'question_id': detail_dict.get('item_index', detail_dict.get('question_id')),
                    'question': analysis.question_text,
                    'answer': analysis.answer_text,
                    'contexts': analysis.contexts if isinstance(analysis.contexts, list) else [analysis.contexts],
                    'ground_truth': analysis.ground_truth or detail_dict.get('ground_truth', ''),
                    'metrics': metrics,
                    'overall_score': analysis.overall_score,
                    'status': analysis.status,
                    'issues': analysis.issues,
                    'recommendations': analysis.recommendations,
                    'interpretation': analysis.interpretation,
                    # Add raw data for debugging
                    'raw_question': detail_dict.get('question', ''),
                    'raw_answer': detail_dict.get('answer', ''),
                    'raw_contexts': detail_dict.get('contexts', [])
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error fetching question details: {e}")
            return []
    
    @staticmethod
    def get_time_series_stats(start_date: str, end_date: str, run_id: str = None) -> Dict:
        """Get time series statistics for a date range"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get data within date range
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    AVG(ragas_score) as avg_score,
                    AVG(faithfulness) as avg_faithfulness,
                    AVG(answer_relevancy) as avg_relevancy,
                    AVG(context_precision) as avg_precision,
                    AVG(context_recall) as avg_recall,
                    AVG(answer_correctness) as avg_correctness,
                    COUNT(*) as count,
                    MIN(ragas_score) as min_score,
                    MAX(ragas_score) as max_score,
                    GROUP_CONCAT(ragas_score) as scores
                FROM evaluations
                WHERE timestamp >= ? AND timestamp <= ?
            """
            
            params = [start_date, end_date + ' 23:59:59']
            
            if run_id:
                query += " AND run_id = ?"
                params.append(run_id)
            
            query += " GROUP BY DATE(timestamp) ORDER BY date"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    'dates': [],
                    'values': [],
                    'dataPoints': 0,
                    'trend': 'No data',
                    'volatility': 0,
                    'forecast': 'N/A'
                }
            
            # Extract data
            dates = []
            values = []
            all_scores = []
            
            for row in rows:
                dates.append(row['date'])
                values.append(float(row['avg_score']) if row['avg_score'] else 0)
                if row['scores']:
                    scores_list = [float(s) for s in row['scores'].split(',') if s]
                    all_scores.extend(scores_list)
            
            # Calculate statistics
            import numpy as np
            from scipy import stats as scipy_stats
            
            values_array = np.array(values)
            
            # Calculate trend
            if len(values) > 1:
                x = np.arange(len(values))
                slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, values_array)
                
                if slope > 0.01:
                    trend = f'↗ 상승 추세 ({slope:.3f}/일)'
                elif slope < -0.01:
                    trend = f'↘ 하락 추세 ({abs(slope):.3f}/일)'
                else:
                    trend = f'→ 안정적 ({slope:.3f}/일)'
            else:
                trend = '데이터 부족'
                slope = 0
                intercept = values[0] if values else 0
            
            # Calculate volatility
            volatility = np.std(values_array) / np.mean(values_array) if np.mean(values_array) > 0 else 0
            
            # Simple forecast (linear regression projection)
            forecast_values = []
            if len(values) >= 3:
                # Project next 7 days
                for i in range(len(values), len(values) + 7):
                    forecast_val = slope * i + intercept
                    forecast_val = max(0, min(1, forecast_val))  # Clamp between 0 and 1
                    forecast_values.append(forecast_val)
                
                forecast_avg = np.mean(forecast_values)
                forecast = f'{forecast_avg:.3f} (다음 7일 평균)'
            else:
                forecast = '예측 불가 (데이터 부족)'
            
            # Calculate moving average
            window = min(3, len(values))
            moving_avg = []
            for i in range(len(values)):
                start_idx = max(0, i - window + 1)
                moving_avg.append(np.mean(values[start_idx:i+1]))
            
            # Prepare forecast data for chart
            forecast_chart_data = [None] * len(values)  # Null for historical dates
            if forecast_values:
                forecast_chart_data.extend(forecast_values)
                # Extend dates for forecast
                from datetime import datetime, timedelta
                last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
                for i in range(1, 8):
                    dates.append((last_date + timedelta(days=i)).strftime('%Y-%m-%d'))
            
            conn.close()
            
            return {
                'dates': dates,
                'values': values + [None] * len(forecast_values),  # Pad with None for forecast dates
                'forecast_values': forecast_chart_data,
                'moving_avg': moving_avg + [None] * len(forecast_values),
                'dataPoints': len(values),
                'trend': trend,
                'volatility': float(volatility),
                'forecast': forecast,
                'statistics': {
                    'mean': float(np.mean(all_scores)) if all_scores else 0,
                    'std': float(np.std(all_scores)) if all_scores else 0,
                    'min': float(min(all_scores)) if all_scores else 0,
                    'max': float(max(all_scores)) if all_scores else 0,
                    'median': float(np.median(all_scores)) if all_scores else 0,
                    'q1': float(np.percentile(all_scores, 25)) if all_scores else 0,
                    'q3': float(np.percentile(all_scores, 75)) if all_scores else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting time series stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                'dates': [],
                'values': [],
                'dataPoints': 0,
                'trend': 'Error',
                'volatility': 0,
                'forecast': 'Error',
                'error': str(e)
            }
    
    @staticmethod
    def perform_ab_test(run_id_a: str, run_id_b: str) -> Dict:
        """Perform A/B testing between two evaluations"""
        try:
            from ..stats.advanced_analyzer import AdvancedStatisticalAnalyzer
            analyzer = AdvancedStatisticalAnalyzer()
            
            # Get metrics for both runs
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get detailed metrics for A
            cursor.execute("""
                SELECT faithfulness, answer_relevancy, context_precision,
                       context_recall, answer_correctness
                FROM evaluation_items
                WHERE run_id = ?
            """, (run_id_a,))
            
            data_a = cursor.fetchall()
            
            # Get detailed metrics for B
            cursor.execute("""
                SELECT faithfulness, answer_relevancy, context_precision,
                       context_recall, answer_correctness
                FROM evaluation_items
                WHERE run_id = ?
            """, (run_id_b,))
            
            data_b = cursor.fetchall()
            
            conn.close()
            
            if not data_a or not data_b:
                return {'error': 'Insufficient data for A/B testing'}
            
            # Perform tests for each metric
            results = {}
            metrics = ['faithfulness', 'answer_relevancy', 'context_precision',
                      'context_recall', 'answer_correctness']
            
            for metric in metrics:
                values_a = [row[metric] for row in data_a if row[metric] is not None]
                values_b = [row[metric] for row in data_b if row[metric] is not None]
                
                if values_a and values_b:
                    test_result = analyzer.analyze_comparison(values_a, values_b)
                    
                    results[metric] = {
                        'test_name': test_result.test_name,
                        'statistic': float(test_result.statistic),
                        'p_value': float(test_result.p_value),
                        'significant': bool(test_result.significant),
                        'effect_size': float(test_result.effect_size),
                        'confidence_interval': [float(x) for x in test_result.confidence_interval] if test_result.confidence_interval else None,
                        'interpretation': test_result.interpretation,
                        'mean_a': float(np.mean(values_a)),
                        'mean_b': float(np.mean(values_b)),
                        'std_a': float(np.std(values_a)),
                        'std_b': float(np.std(values_b))
                    }
            
            # Overall comparison
            overall_a = []
            overall_b = []
            
            for row in data_a:
                scores = [row[m] for m in metrics if row[m] is not None]
                if scores:
                    overall_a.append(np.mean(scores))
            
            for row in data_b:
                scores = [row[m] for m in metrics if row[m] is not None]
                if scores:
                    overall_b.append(np.mean(scores))
            
            if overall_a and overall_b:
                overall_result = analyzer.analyze_comparison(overall_a, overall_b)
                results['overall'] = {
                    'test_name': overall_result.test_name,
                    'statistic': float(overall_result.statistic),
                    'p_value': float(overall_result.p_value),
                    'significant': bool(overall_result.significant),
                    'effect_size': float(overall_result.effect_size),
                    'confidence_interval': [float(x) for x in overall_result.confidence_interval] if overall_result.confidence_interval else None,
                    'interpretation': overall_result.interpretation,
                    'mean_a': float(np.mean(overall_a)),
                    'mean_b': float(np.mean(overall_b))
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing A/B test: {e}")
            return {'error': str(e)}

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard_v2.html')

@app.route('/api/reports')
def get_reports():
    """API endpoint for fetching all reports"""
    reports = DashboardService.get_all_reports()
    return jsonify(reports)

@app.route('/api/report/<run_id>')
def get_report(run_id):
    """API endpoint for fetching single report"""
    report = DashboardService.get_report_details(run_id)
    if report:
        return jsonify(report)
    return jsonify({'error': 'Report not found'}), 404

@app.route('/api/compare', methods=['POST'])
def compare_reports():
    """API endpoint for comparing reports"""
    data = request.get_json()
    run_ids = data.get('run_ids', [])
    
    if not run_ids:
        return jsonify({'error': 'No run_ids provided'}), 400
    
    comparison = DashboardService.compare_reports(run_ids)
    return jsonify(comparison)

@app.route('/api/trend/<int:days>')
def get_trend(days):
    """API endpoint for trend data"""
    trend = DashboardService.get_trend_data(days)
    return jsonify(trend)

@app.route('/api/questions/<run_id>')
def get_questions(run_id):
    """API endpoint for fetching question details"""
    questions = DashboardService.get_question_details(run_id)
    return jsonify(questions)

@app.route('/api/ab-test', methods=['POST'])
def ab_test():
    """API endpoint for A/B testing"""
    data = request.get_json()
    run_id_a = data.get('run_id_a')
    run_id_b = data.get('run_id_b')
    
    if not run_id_a or not run_id_b:
        return jsonify({'error': 'Both run_id_a and run_id_b are required'}), 400
    
    results = DashboardService.perform_ab_test(run_id_a, run_id_b)
    return jsonify(results)

@app.route('/api/time-series', methods=['POST'])
def time_series():
    """Get time series statistics for a date range"""
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    run_id = data.get('run_id')
    
    result = DashboardService.get_time_series_stats(start_date, end_date, run_id)
    return jsonify(result)

@app.route('/api/export/<run_id>')
def export_report(run_id):
    """Export report as HTML"""
    # Check if HTML file exists
    html_files = list(RESULTS_PATH.glob(f"*{run_id}*.html"))
    if html_files:
        return send_from_directory(RESULTS_PATH, html_files[0].name)
    
    # Generate HTML if not exists
    report = DashboardService.get_report_details(run_id)
    if report:
        # Generate HTML using the Korean generator
        from ..report.korean_html_generator import KoreanHTMLReportGenerator
        generator = KoreanHTMLReportGenerator()
        
        html_content = generator.generate_evaluation_report(
            run_id=run_id,
            results={'metrics': {
                'faithfulness': report.get('faithfulness', 0),
                'answer_relevancy': report.get('answer_relevancy', 0),
                'context_precision': report.get('context_precision', 0),
                'context_recall': report.get('context_recall', 0),
                'answer_correctness': report.get('answer_correctness', 0),
                'ragas_score': report.get('ragas_score', 0)
            }, 'details': report.get('details', [])},
            environment=report.get('environment', {}),
            dataset_name=report.get('dataset_name', '')
        )
        
        # Save and return
        output_path = RESULTS_PATH / f"{run_id}_export.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return send_from_directory(RESULTS_PATH, output_path.name)
    
    return jsonify({'error': 'Report not found'}), 404

def run_dashboard(host='127.0.0.1', port=8080, debug=True):
    """Run the dashboard server"""
    logger.info(f"Starting RAGTrace Dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_dashboard()