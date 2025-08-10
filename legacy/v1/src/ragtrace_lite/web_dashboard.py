"""
RAGTrace Lite Web Dashboard
동적 HTML 대시보드 생성 - 모든 테스트 결과를 통합 조회
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template

from .db_manager import DatabaseManager


class WebDashboard:
    """RAGTrace Lite 웹 대시보드 생성기"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """웹 대시보드 초기화"""
        self.db = db_manager or DatabaseManager()
        self.output_dir = Path("reports/web")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_dashboard(self) -> str:
        """통합 웹 대시보드 생성"""
        print("📊 통합 웹 대시보드 생성 중...")
        
        # 데이터 수집
        dashboard_data = self._collect_dashboard_data()
        
        # HTML 템플릿 생성
        html_content = self._generate_html_template(dashboard_data)
        
        # 파일 저장
        dashboard_path = self.output_dir / "dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 웹 대시보드 생성 완료: {dashboard_path}")
        return str(dashboard_path)
    
    def _collect_dashboard_data(self) -> Dict[str, Any]:
        """대시보드용 데이터 수집"""
        cursor = self.db.conn.cursor()
        
        # 모든 평가 실행 조회
        cursor.execute("""
        SELECT run_id, timestamp, llm_provider, llm_model, dataset_name, 
               total_items, status, metrics, config_data
        FROM evaluations 
        ORDER BY timestamp DESC
        """)
        
        evaluations = []
        for row in cursor.fetchall():
            run_id, timestamp, llm_provider, llm_model, dataset_name, total_items, status, metrics, config_data = row
            
            # 설정 파싱
            embedding_provider = "unknown"
            batch_size = "unknown"
            if config_data:
                try:
                    config = json.loads(config_data)
                    embedding_provider = config.get('embedding', {}).get('provider', 'unknown')
                    batch_size = config.get('evaluation', {}).get('batch_size', 'unknown')
                except:
                    pass
            
            # 메트릭 결과 조회
            cursor.execute("""
            SELECT metric_name, AVG(metric_score) as avg_score, COUNT(*) as count
            FROM evaluation_results 
            WHERE run_id = ? AND metric_score IS NOT NULL
            GROUP BY metric_name
            """, (run_id,))
            
            metrics_data = {}
            total_score = 0
            valid_metrics = 0
            
            for metric_row in cursor.fetchall():
                metric_name, avg_score, count = metric_row
                metrics_data[metric_name] = {
                    'score': round(avg_score, 4),
                    'count': count
                }
                total_score += avg_score
                valid_metrics += 1
            
            overall_score = round(total_score / valid_metrics, 4) if valid_metrics > 0 else 0
            
            evaluations.append({
                'run_id': run_id,
                'timestamp': timestamp,
                'llm_provider': llm_provider,
                'llm_model': llm_model,
                'embedding_provider': embedding_provider,
                'dataset_name': dataset_name or 'evaluation_data.json',
                'total_items': total_items,
                'status': status,
                'batch_size': batch_size,
                'metrics': metrics_data,
                'overall_score': overall_score,
                'success': len(metrics_data) > 0
            })
        
        # 통계 계산
        successful_runs = [e for e in evaluations if e['success']]
        
        # 기술 조합별 통계
        combinations = {}
        for eval_data in successful_runs:
            combo_key = f"{eval_data['embedding_provider'].upper()}+{eval_data['llm_provider'].upper()}"
            if combo_key not in combinations:
                combinations[combo_key] = {
                    'name': f"{eval_data['embedding_provider'].upper()} + {eval_data['llm_provider'].upper()}",
                    'embedding': eval_data['embedding_provider'],
                    'llm': eval_data['llm_provider'],
                    'scores': [],
                    'count': 0
                }
            combinations[combo_key]['scores'].append(eval_data['overall_score'])
            combinations[combo_key]['count'] += 1
        
        # 조합별 평균 계산
        for combo in combinations.values():
            combo['avg_score'] = round(sum(combo['scores']) / len(combo['scores']), 4)
            combo['best_score'] = round(max(combo['scores']), 4)
        
        # 메트릭별 전체 통계
        all_metrics = {}
        for eval_data in successful_runs:
            for metric_name, metric_data in eval_data['metrics'].items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(metric_data['score'])
        
        metric_stats = {}
        for metric_name, scores in all_metrics.items():
            metric_stats[metric_name] = {
                'avg': round(sum(scores) / len(scores), 4),
                'min': round(min(scores), 4),
                'max': round(max(scores), 4),
                'count': len(scores)
            }
        
        return {
            'evaluations': evaluations,
            'successful_runs': len(successful_runs),
            'total_runs': len(evaluations),
            'combinations': list(combinations.values()),
            'metric_stats': metric_stats,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_html_template(self, data: Dict[str, Any]) -> str:
        """HTML 템플릿 생성"""
        
        html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAGTrace Lite Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f7fa; 
            color: #333;
            line-height: 1.6;
        }
        
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 2rem; 
            text-align: center; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 { 
            font-size: 2.5rem; 
            margin-bottom: 0.5rem; 
            font-weight: 300;
        }
        
        .header p { 
            font-size: 1.1rem; 
            opacity: 0.9; 
        }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 2rem; 
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 1.5rem; 
            margin-bottom: 2rem; 
        }
        
        .stat-card { 
            background: white; 
            padding: 1.5rem; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            border-left: 4px solid #667eea;
            transition: transform 0.2s ease;
        }
        
        .stat-card:hover { 
            transform: translateY(-2px); 
        }
        
        .stat-card h3 { 
            color: #667eea; 
            font-size: 0.9rem; 
            text-transform: uppercase; 
            letter-spacing: 1px; 
            margin-bottom: 0.5rem; 
        }
        
        .stat-card .value { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #333; 
        }
        
        .section { 
            background: white; 
            margin: 2rem 0; 
            border-radius: 12px; 
            overflow: hidden; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        
        .section-header { 
            background: #667eea; 
            color: white; 
            padding: 1rem 1.5rem; 
            font-size: 1.2rem; 
            font-weight: 600; 
        }
        
        .section-content { 
            padding: 1.5rem; 
        }
        
        .chart-container { 
            position: relative; 
            height: 400px; 
            margin: 1rem 0; 
        }
        
        .evaluation-grid { 
            display: grid; 
            gap: 1rem; 
        }
        
        .evaluation-card { 
            border: 1px solid #e1e8ed; 
            border-radius: 8px; 
            padding: 1rem; 
            transition: all 0.2s ease;
        }
        
        .evaluation-card:hover { 
            border-color: #667eea; 
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        }
        
        .evaluation-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 0.5rem; 
        }
        
        .run-id { 
            font-family: monospace; 
            background: #f8f9fa; 
            padding: 0.25rem 0.5rem; 
            border-radius: 4px; 
            font-size: 0.8rem; 
        }
        
        .status { 
            padding: 0.25rem 0.75rem; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            font-weight: 600; 
        }
        
        .status.completed { 
            background: #d4edda; 
            color: #155724; 
        }
        
        .status.running { 
            background: #fff3cd; 
            color: #856404; 
        }
        
        .status.failed { 
            background: #f8d7da; 
            color: #721c24; 
        }
        
        .config-info { 
            display: flex; 
            gap: 1rem; 
            margin: 0.5rem 0; 
            font-size: 0.9rem; 
        }
        
        .config-tag { 
            background: #e9ecef; 
            padding: 0.25rem 0.5rem; 
            border-radius: 4px; 
        }
        
        .metrics-row { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); 
            gap: 0.5rem; 
            margin-top: 0.5rem; 
        }
        
        .metric-score { 
            text-align: center; 
            padding: 0.5rem; 
            background: #f8f9fa; 
            border-radius: 4px; 
        }
        
        .metric-name { 
            font-size: 0.8rem; 
            color: #666; 
            margin-bottom: 0.25rem; 
        }
        
        .metric-value { 
            font-weight: bold; 
            font-size: 1rem; 
        }
        
        .overall-score { 
            font-size: 1.2rem; 
            font-weight: bold; 
            color: #667eea; 
            text-align: center; 
            margin-top: 0.5rem; 
        }
        
        .no-data { 
            text-align: center; 
            color: #666; 
            font-style: italic; 
            padding: 2rem; 
        }
        
        .filter-controls { 
            margin-bottom: 1rem; 
            display: flex; 
            gap: 1rem; 
            flex-wrap: wrap; 
        }
        
        .filter-btn { 
            padding: 0.5rem 1rem; 
            border: 1px solid #667eea; 
            background: white; 
            color: #667eea; 
            border-radius: 20px; 
            cursor: pointer; 
            transition: all 0.2s ease; 
        }
        
        .filter-btn:hover, .filter-btn.active { 
            background: #667eea; 
            color: white; 
        }
        
        .timestamp { 
            color: #666; 
            font-size: 0.9rem; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 RAGTrace Lite Dashboard</h1>
        <p>실시간 RAG 평가 결과 대시보드 | 생성일: {{ data.generated_at }}</p>
    </div>
    
    <div class="container">
        <!-- 통계 요약 -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>총 평가 실행</h3>
                <div class="value">{{ data.total_runs }}</div>
            </div>
            <div class="stat-card">
                <h3>성공한 실행</h3>
                <div class="value">{{ data.successful_runs }}</div>
            </div>
            <div class="stat-card">
                <h3>성공률</h3>
                <div class="value">{{ "%.1f"|format((data.successful_runs / data.total_runs * 100) if data.total_runs > 0 else 0) }}%</div>
            </div>
            <div class="stat-card">
                <h3>테스트 조합</h3>
                <div class="value">{{ data.combinations|length }}</div>
            </div>
        </div>
        
        <!-- 기술 조합 성능 -->
        <div class="section">
            <div class="section-header">📊 기술 조합별 성능</div>
            <div class="section-content">
                <div class="chart-container">
                    <canvas id="combinationChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 메트릭 분석 -->
        <div class="section">
            <div class="section-header">🎯 메트릭별 성능 분석</div>
            <div class="section-content">
                <div class="chart-container">
                    <canvas id="metricsChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 평가 실행 목록 -->
        <div class="section">
            <div class="section-header">📋 평가 실행 기록</div>
            <div class="section-content">
                <div class="filter-controls">
                    <button class="filter-btn active" onclick="filterEvaluations('all')">전체</button>
                    <button class="filter-btn" onclick="filterEvaluations('completed')">완료됨</button>
                    <button class="filter-btn" onclick="filterEvaluations('running')">실행중</button>
                    <button class="filter-btn" onclick="filterEvaluations('bge_m3')">BGE-M3</button>
                    <button class="filter-btn" onclick="filterEvaluations('hcx')">HCX</button>
                    <button class="filter-btn" onclick="filterEvaluations('gemini')">Gemini</button>
                </div>
                
                <div class="evaluation-grid" id="evaluationGrid">
                    {% for eval in data.evaluations %}
                    <div class="evaluation-card" data-status="{{ eval.status }}" data-embedding="{{ eval.embedding_provider }}" data-llm="{{ eval.llm_provider }}">
                        <div class="evaluation-header">
                            <span class="run-id">{{ eval.run_id }}</span>
                            <span class="status {{ eval.status }}">{{ eval.status.upper() }}</span>
                        </div>
                        
                        <div class="config-info">
                            <span class="config-tag">🤖 {{ eval.llm_provider.upper() }} / {{ eval.llm_model }}</span>
                            <span class="config-tag">📁 {{ eval.embedding_provider.upper() }}</span>
                            <span class="config-tag">📊 {{ eval.total_items }}개 항목</span>
                            <span class="timestamp">{{ eval.timestamp }}</span>
                        </div>
                        
                        {% if eval.success %}
                        <div class="metrics-row">
                            {% for metric_name, metric_data in eval.metrics.items() %}
                            <div class="metric-score">
                                <div class="metric-name">{{ metric_name }}</div>
                                <div class="metric-value">{{ "%.3f"|format(metric_data.score) }}</div>
                            </div>
                            {% endfor %}
                        </div>
                        <div class="overall-score">🏆 RAGAS Score: {{ "%.4f"|format(eval.overall_score) }}</div>
                        {% else %}
                        <div class="no-data">평가 결과 없음</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 차트 데이터 준비
        const combinationData = {{ data.combinations | tojson }};
        const metricStats = {{ data.metric_stats | tojson }};
        
        // 기술 조합 차트
        const ctx1 = document.getElementById('combinationChart').getContext('2d');
        new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: combinationData.map(c => c.name),
                datasets: [{
                    label: 'RAGAS Score',
                    data: combinationData.map(c => c.avg_score),
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        title: {
                            display: true,
                            text: 'RAGAS Score'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '기술 조합별 평균 RAGAS Score'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // 메트릭 차트
        const ctx2 = document.getElementById('metricsChart').getContext('2d');
        new Chart(ctx2, {
            type: 'radar',
            data: {
                labels: Object.keys(metricStats),
                datasets: [{
                    label: '평균 점수',
                    data: Object.values(metricStats).map(m => m.avg),
                    fill: true,
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                elements: {
                    line: {
                        borderWidth: 3
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            display: false
                        },
                        suggestedMin: 0,
                        suggestedMax: 1
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '메트릭별 평균 성능'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // 필터링 기능
        function filterEvaluations(filter) {
            const cards = document.querySelectorAll('.evaluation-card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // 버튼 상태 업데이트
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 카드 필터링
            cards.forEach(card => {
                let show = false;
                
                switch(filter) {
                    case 'all':
                        show = true;
                        break;
                    case 'completed':
                        show = card.dataset.status === 'completed';
                        break;
                    case 'running':
                        show = card.dataset.status === 'running';
                        break;
                    case 'bge_m3':
                        show = card.dataset.embedding === 'bge_m3';
                        break;
                    case 'hcx':
                        show = card.dataset.llm === 'hcx';
                        break;
                    case 'gemini':
                        show = card.dataset.llm === 'gemini';
                        break;
                }
                
                card.style.display = show ? 'block' : 'none';
            });
        }
        
        // 자동 새로고침 (옵션)
        // setInterval(() => {
        //     location.reload();
        // }, 30000); // 30초마다 새로고침
    </script>
</body>
</html>
        """
        
        # Jinja2 템플릿 렌더링
        template = Template(html_template)
        return template.render(data=data)


def generate_web_dashboard() -> str:
    """웹 대시보드 생성 헬퍼 함수"""
    dashboard = WebDashboard()
    return dashboard.generate_dashboard()


if __name__ == "__main__":
    dashboard_path = generate_web_dashboard()
    print(f"🌐 대시보드 URL: file://{os.path.abspath(dashboard_path)}")