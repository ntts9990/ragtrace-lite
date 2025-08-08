"""HTML report generator for better visualization"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """HTML 형식 보고서 생성기"""
    
    def __init__(self):
        self.template = self._get_html_template()
    
    def generate_evaluation_html(
        self,
        run_id: str,
        results: Dict,
        environment: Dict,
        interpretation: str = ""
    ) -> str:
        """평가 결과를 HTML로 생성"""
        
        metrics = results.get('metrics', {})
        details = results.get('details', [])
        
        # 메트릭 테이블 생성
        metrics_html = self._create_metrics_table(metrics)
        
        # 환경 설정 테이블
        env_html = self._create_environment_table(environment)
        
        # 차트 데이터 준비
        chart_data = self._prepare_chart_data(metrics)
        
        # HTML 생성
        html = self.template.format(
            title=f"RAGTrace Evaluation Report - {run_id}",
            run_id=run_id,
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            metrics_table=metrics_html,
            environment_table=env_html,
            interpretation=interpretation or self._get_default_interpretation(metrics),
            chart_data=chart_data,
            sample_count=len(details)
        )
        
        return html
    
    def _create_metrics_table(self, metrics: Dict) -> str:
        """메트릭 테이블 HTML 생성"""
        rows = []
        for name, score in metrics.items():
            # 점수에 따른 색상 결정
            if score >= 0.8:
                color_class = 'success'
                icon = '✅'
            elif score >= 0.6:
                color_class = 'warning'
                icon = '⚠️'
            else:
                color_class = 'danger'
                icon = '❌'
            
            rows.append(f'''
                <tr>
                    <td>{name.replace('_', ' ').title()}</td>
                    <td>
                        <div class="progress">
                            <div class="progress-bar bg-{color_class}" 
                                 style="width: {score*100:.1f}%">
                                {score:.3f}
                            </div>
                        </div>
                    </td>
                    <td class="text-center">{icon}</td>
                </tr>
            ''')
        
        return '\n'.join(rows)
    
    def _create_environment_table(self, environment: Dict) -> str:
        """환경 설정 테이블 HTML 생성"""
        rows = []
        for key, value in sorted(environment.items()):
            rows.append(f'''
                <tr>
                    <td><strong>{key}</strong></td>
                    <td>{value}</td>
                </tr>
            ''')
        return '\n'.join(rows)
    
    def _prepare_chart_data(self, metrics: Dict) -> str:
        """차트용 데이터 준비"""
        labels = []
        values = []
        colors = []
        
        for name, score in metrics.items():
            if name != 'ragas_score':  # 종합 점수는 제외
                labels.append(name.replace('_', ' ').title())
                values.append(round(score, 3))
                
                # 점수별 색상
                if score >= 0.8:
                    colors.append('rgba(40, 167, 69, 0.8)')  # 녹색
                elif score >= 0.6:
                    colors.append('rgba(255, 193, 7, 0.8)')  # 노란색
                else:
                    colors.append('rgba(220, 53, 69, 0.8)')  # 빨간색
        
        return json.dumps({
            'labels': labels,
            'values': values,
            'colors': colors
        })
    
    def _get_default_interpretation(self, metrics: Dict) -> str:
        """기본 해석 생성"""
        avg_score = sum(metrics.values()) / len(metrics) if metrics else 0
        
        strengths = [k for k, v in metrics.items() if v >= 0.7 and k != 'ragas_score']
        weaknesses = [k for k, v in metrics.items() if v < 0.5 and k != 'ragas_score']
        
        interpretation = f"""
        <div class="alert alert-info">
            <h5>📊 Performance Summary</h5>
            <p><strong>Overall Score:</strong> {avg_score:.3f}/1.000</p>
            
            {f'<p><strong>✅ Strengths:</strong> {", ".join(strengths)}</p>' if strengths else ''}
            {f'<p><strong>⚠️ Areas for Improvement:</strong> {", ".join(weaknesses)}</p>' if weaknesses else ''}
            
            <hr>
            <p class="mb-0">
                <strong>Recommendation:</strong> 
                {'Focus on improving ' + min(metrics.items(), key=lambda x: x[1])[0] if weaknesses else 'Maintain current performance levels'}
            </p>
        </div>
        """
        return interpretation
    
    def _get_html_template(self) -> str:
        """HTML 템플릿 반환"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }}
        .container {{ 
            max-width: 1200px;
        }}
        .card {{ 
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .card-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0 !important;
            padding: 1.5rem;
        }}
        .progress {{
            height: 25px;
            border-radius: 10px;
        }}
        .progress-bar {{
            font-weight: bold;
            font-size: 14px;
        }}
        .metric-card {{
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 2rem 0;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .header-info {{
            background: white;
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-info">
            <h1 class="text-center mb-4">🎯 RAGTrace Evaluation Report</h1>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Run ID:</strong> <code>{run_id}</code></p>
                </div>
                <div class="col-md-6 text-end">
                    <p><strong>Date:</strong> {date}</p>
                </div>
            </div>
        </div>

        <!-- Metrics Card -->
        <div class="card metric-card">
            <div class="card-header">
                <h3 class="mb-0">📊 Evaluation Metrics</h3>
            </div>
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th style="width: 60%">Score</th>
                            <th class="text-center">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics_table}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Chart Card -->
        <div class="card">
            <div class="card-header">
                <h3 class="mb-0">📈 Performance Visualization</h3>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="metricsChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Interpretation Card -->
        <div class="card">
            <div class="card-header">
                <h3 class="mb-0">🤖 AI Analysis & Recommendations</h3>
            </div>
            <div class="card-body">
                {interpretation}
            </div>
        </div>

        <!-- Environment Card -->
        <div class="card">
            <div class="card-header">
                <h3 class="mb-0">⚙️ Environment Configuration</h3>
            </div>
            <div class="card-body">
                <table class="table table-striped">
                    <tbody>
                        {environment_table}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Statistics Card -->
        <div class="card">
            <div class="card-header">
                <h3 class="mb-0">📝 Evaluation Statistics</h3>
            </div>
            <div class="card-body">
                <p><strong>Total Samples Evaluated:</strong> {sample_count}</p>
                <p class="text-muted mb-0">Generated by RAGTrace Lite v2.0</p>
            </div>
        </div>
    </div>

    <script>
        // Chart.js configuration
        const chartData = {chart_data};
        
        const ctx = document.getElementById('metricsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'radar',
            data: {{
                labels: chartData.labels,
                datasets: [{{
                    label: 'Scores',
                    data: chartData.values,
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: chartData.colors,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: chartData.colors,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 1,
                        ticks: {{
                            stepSize: 0.2
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.label + ': ' + context.raw.toFixed(3);
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''