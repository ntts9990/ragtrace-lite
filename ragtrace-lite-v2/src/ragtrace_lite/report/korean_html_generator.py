"""Korean HTML report generator with clean design and detailed statistics"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import numpy as np

logger = logging.getLogger(__name__)


class KoreanHTMLReportGenerator:
    """한국어 HTML 보고서 생성기 - 깔끔한 디자인과 상세 통계 분석"""
    
    def __init__(self):
        self.template = self._get_html_template()
    
    def generate_evaluation_report(
        self,
        run_id: str,
        results: Dict,
        environment: Dict,
        dataset_name: str = "평가 데이터셋"
    ) -> str:
        """평가 보고서 생성"""
        
        metrics = results.get('metrics', {})
        details = results.get('details', [])
        
        # 통계 분석 수행
        stats_analysis = self._perform_statistical_analysis(metrics, details)
        
        # 섹션별 HTML 생성
        metrics_cards = self._create_metrics_cards(metrics)
        interpretation = self._create_korean_interpretation(metrics, stats_analysis)
        stats_section = self._create_statistics_section(stats_analysis)
        env_section = self._create_environment_section(environment)
        chart_data = self._prepare_chart_data(metrics)
        
        # HTML 조합
        html = self.template.format(
            run_id=run_id,
            date=datetime.now().strftime('%Y년 %m월 %d일 %H:%M'),
            dataset_name=dataset_name,
            total_samples=len(details),
            metrics_cards=metrics_cards,
            interpretation=interpretation,
            statistics_section=stats_section,
            environment_section=env_section,
            chart_data=chart_data,
            overall_score=metrics.get('ragas_score', sum(metrics.values())/len(metrics))
        )
        
        return html
    
    def _perform_statistical_analysis(self, metrics: Dict, details: List) -> Dict:
        """상세 통계 분석 수행"""
        analysis = {
            'overall': {},
            'by_metric': {},
            'correlations': {},
            'recommendations': []
        }
        
        # 전체 통계
        scores = list(metrics.values())
        analysis['overall'] = {
            'mean': np.mean(scores),
            'std': np.std(scores),
            'min': min(scores),
            'max': max(scores),
            'median': np.median(scores),
            'q1': np.percentile(scores, 25),
            'q3': np.percentile(scores, 75)
        }
        
        # 메트릭별 상세 분석
        for metric_name, score in metrics.items():
            if metric_name == 'ragas_score':
                continue
                
            # 샘플별 점수가 있다면 분석
            if details:
                sample_scores = [d.get(metric_name, 0) for d in details if metric_name in d]
                if sample_scores:
                    analysis['by_metric'][metric_name] = {
                        'mean': np.mean(sample_scores),
                        'std': np.std(sample_scores),
                        'min': min(sample_scores),
                        'max': max(sample_scores),
                        'cv': np.std(sample_scores) / np.mean(sample_scores) if np.mean(sample_scores) > 0 else 0
                    }
            else:
                analysis['by_metric'][metric_name] = {
                    'score': score,
                    'status': self._get_score_status(score)
                }
        
        # 권장사항 생성
        analysis['recommendations'] = self._generate_recommendations(metrics, analysis)
        
        return analysis
    
    def _get_score_status(self, score: float) -> str:
        """점수 상태 판정"""
        if score >= 0.8:
            return "우수"
        elif score >= 0.6:
            return "양호"
        elif score >= 0.4:
            return "보통"
        else:
            return "개선필요"
    
    def _create_metrics_cards(self, metrics: Dict) -> str:
        """메트릭 카드 생성"""
        cards = []
        
        metric_info = {
            'faithfulness': ('충실도', '답변이 컨텍스트에 근거한 정도', 'bi-shield-check'),
            'answer_relevancy': ('답변 관련성', '질문에 대한 답변의 적절성', 'bi-bullseye'),
            'context_precision': ('컨텍스트 정밀도', '검색된 컨텍스트의 품질', 'bi-search'),
            'context_recall': ('컨텍스트 재현율', '정답 대비 컨텍스트 커버리지', 'bi-collection'),
            'answer_correctness': ('답변 정확도', '정답 대비 답변의 정확성', 'bi-check-circle'),
            'ragas_score': ('종합 점수', 'RAG 시스템 전체 성능', 'bi-graph-up')
        }
        
        for metric_name, score in metrics.items():
            name_kr, description, icon = metric_info.get(
                metric_name, 
                (metric_name, '', 'bi-question-circle')
            )
            
            # 점수별 색상
            if score >= 0.8:
                color = '#10b981'  # 녹색
                status = '우수'
                badge_color = 'success'
            elif score >= 0.6:
                color = '#f59e0b'  # 주황색
                status = '양호'
                badge_color = 'warning'
            else:
                color = '#ef4444'  # 빨간색
                status = '개선필요'
                badge_color = 'danger'
            
            cards.append(f'''
                <div class="col-md-4 mb-4">
                    <div class="metric-card h-100">
                        <div class="metric-header">
                            <i class="bi {icon}"></i>
                            <span class="badge bg-{badge_color}">{status}</span>
                        </div>
                        <h5 class="metric-title">{name_kr}</h5>
                        <div class="metric-score" style="color: {color}">
                            {score:.3f}
                        </div>
                        <div class="metric-bar">
                            <div class="metric-bar-fill" style="width: {score*100:.1f}%; background: {color}"></div>
                        </div>
                        <p class="metric-description">{description}</p>
                    </div>
                </div>
            ''')
        
        return '\n'.join(cards)
    
    def _create_korean_interpretation(self, metrics: Dict, stats: Dict) -> str:
        """한국어 상세 해석 생성"""
        
        # 전체 성능 평가
        overall_score = stats['overall']['mean']
        if overall_score >= 0.8:
            overall_text = "매우 우수한 성능을 보이고 있습니다."
            overall_color = "success"
        elif overall_score >= 0.6:
            overall_text = "양호한 성능을 보이고 있으나, 일부 개선이 필요합니다."
            overall_color = "warning"
        else:
            overall_text = "전반적인 성능 개선이 필요합니다."
            overall_color = "danger"
        
        # 강점과 약점 분석
        strengths = []
        weaknesses = []
        critical = []
        
        for metric, score in metrics.items():
            if metric == 'ragas_score':
                continue
            
            metric_kr = {
                'faithfulness': '충실도',
                'answer_relevancy': '답변 관련성',
                'context_precision': '컨텍스트 정밀도',
                'context_recall': '컨텍스트 재현율',
                'answer_correctness': '답변 정확도'
            }.get(metric, metric)
            
            if score >= 0.8:
                strengths.append(f"{metric_kr} ({score:.3f})")
            elif score >= 0.5:
                weaknesses.append(f"{metric_kr} ({score:.3f})")
            else:
                critical.append(f"{metric_kr} ({score:.3f})")
        
        interpretation = f'''
        <div class="interpretation-section">
            <div class="alert alert-{overall_color}">
                <h5>📊 전체 평가</h5>
                <p class="mb-0">RAG 시스템이 <strong>{overall_text}</strong></p>
                <p class="mb-0">평균 점수: <strong>{overall_score:.3f}/1.000</strong></p>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card border-success">
                        <div class="card-header bg-success text-white">
                            <i class="bi bi-check-circle"></i> 강점 영역
                        </div>
                        <div class="card-body">
                            {self._format_list(strengths, "우수한 성능을 보이는 영역이 없습니다.")}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card border-warning">
                        <div class="card-header bg-warning text-dark">
                            <i class="bi bi-exclamation-triangle"></i> 개선 필요
                        </div>
                        <div class="card-body">
                            {self._format_list(weaknesses, "보통 수준의 개선 필요 영역이 없습니다.")}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card border-danger">
                        <div class="card-header bg-danger text-white">
                            <i class="bi bi-x-circle"></i> 긴급 개선
                        </div>
                        <div class="card-body">
                            {self._format_list(critical, "긴급 개선이 필요한 영역이 없습니다.")}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h5>🎯 상세 분석</h5>
                {self._generate_detailed_analysis(metrics)}
            </div>
            
            <div class="mt-4">
                <h5>💡 개선 권장사항</h5>
                {self._generate_recommendations_html(metrics, stats)}
            </div>
        </div>
        '''
        
        return interpretation
    
    def _format_list(self, items: List[str], empty_msg: str) -> str:
        """리스트 포맷팅"""
        if items:
            return '<ul class="mb-0">' + ''.join(f'<li>{item}</li>' for item in items) + '</ul>'
        return f'<p class="text-muted mb-0">{empty_msg}</p>'
    
    def _generate_detailed_analysis(self, metrics: Dict) -> str:
        """상세 분석 생성"""
        analysis = []
        
        # 검색 vs 생성 성능 비교
        retrieval_score = (metrics.get('context_precision', 0) + metrics.get('context_recall', 0)) / 2
        generation_score = (metrics.get('faithfulness', 0) + metrics.get('answer_relevancy', 0) + 
                          metrics.get('answer_correctness', 0)) / 3
        
        if retrieval_score > generation_score + 0.1:
            analysis.append('''
                <div class="alert alert-info">
                    <strong>검색 > 생성:</strong> 컨텍스트 검색은 잘 되고 있으나 
                    답변 생성 품질이 상대적으로 낮습니다. LLM 프롬프트 최적화가 필요합니다.
                </div>
            ''')
        elif generation_score > retrieval_score + 0.1:
            analysis.append('''
                <div class="alert alert-info">
                    <strong>생성 > 검색:</strong> 답변 생성 능력은 좋으나 
                    관련 컨텍스트 검색이 부족합니다. 임베딩 모델이나 검색 전략 개선이 필요합니다.
                </div>
            ''')
        
        # 정확도 vs 관련성 분석
        if metrics.get('answer_correctness', 1) < 0.5 and metrics.get('answer_relevancy', 1) < 0.5:
            analysis.append('''
                <div class="alert alert-warning">
                    <strong>품질 경고:</strong> 답변의 정확도와 관련성이 모두 낮습니다. 
                    전체적인 시스템 재검토가 필요합니다.
                </div>
            ''')
        
        return '\n'.join(analysis) if analysis else '<p>시스템이 균형잡힌 성능을 보이고 있습니다.</p>'
    
    def _generate_recommendations_html(self, metrics: Dict, stats: Dict) -> str:
        """권장사항 HTML 생성"""
        recommendations = stats.get('recommendations', [])
        
        if not recommendations:
            # 기본 권장사항 생성
            lowest_metric = min(metrics.items(), key=lambda x: x[1] if x[0] != 'ragas_score' else 1)
            recommendations = [
                f"가장 낮은 점수를 보이는 '{lowest_metric[0]}'부터 개선하세요.",
                "정기적인 평가를 통해 성능 변화를 모니터링하세요.",
                "다양한 테스트 데이터로 평가를 수행하세요."
            ]
        
        html = '<ol>'
        for rec in recommendations[:5]:  # 최대 5개 권장사항
            html += f'<li>{rec}</li>'
        html += '</ol>'
        
        return html
    
    def _generate_recommendations(self, metrics: Dict, analysis: Dict) -> List[str]:
        """권장사항 생성"""
        recs = []
        
        # 가장 낮은 메트릭
        lowest = min(metrics.items(), key=lambda x: x[1] if x[0] != 'ragas_score' else 1)
        if lowest[1] < 0.5:
            metric_kr = {
                'faithfulness': '충실도',
                'answer_relevancy': '답변 관련성',
                'context_precision': '컨텍스트 정밀도',
                'context_recall': '컨텍스트 재현율',
                'answer_correctness': '답변 정확도'
            }.get(lowest[0], lowest[0])
            
            recs.append(f"<strong>긴급:</strong> {metric_kr}({lowest[1]:.3f}) 개선이 시급합니다.")
        
        # 답변 정확도가 낮은 경우
        if metrics.get('answer_correctness', 1) < 0.5:
            recs.append("<strong>LLM 튜닝:</strong> 답변 생성 프롬프트를 조정하거나 파인튜닝을 고려하세요.")
        
        # 컨텍스트 문제
        if metrics.get('context_precision', 1) < 0.6:
            recs.append("<strong>검색 개선:</strong> 청킹 전략이나 임베딩 모델 변경을 검토하세요.")
        
        # 높은 변동성
        if analysis['overall'].get('std', 0) > 0.2:
            recs.append("<strong>안정성:</strong> 메트릭 간 편차가 큽니다. 균형잡힌 개선이 필요합니다.")
        
        # 전체 성능
        if analysis['overall'].get('mean', 0) < 0.6:
            recs.append("<strong>전체 개선:</strong> RAG 파이프라인 전체를 재검토하세요.")
        elif analysis['overall'].get('mean', 0) > 0.8:
            recs.append("<strong>유지:</strong> 우수한 성능을 유지하면서 엣지 케이스를 개선하세요.")
        
        return recs
    
    def _create_statistics_section(self, stats: Dict) -> str:
        """통계 섹션 생성"""
        overall = stats['overall']
        
        html = f'''
        <div class="statistics-section">
            <div class="row">
                <div class="col-md-6">
                    <h6>📈 기술 통계</h6>
                    <table class="table table-sm">
                        <tr><td>평균 (Mean)</td><td class="text-end"><strong>{overall['mean']:.4f}</strong></td></tr>
                        <tr><td>표준편차 (Std)</td><td class="text-end">{overall['std']:.4f}</td></tr>
                        <tr><td>중앙값 (Median)</td><td class="text-end">{overall['median']:.4f}</td></tr>
                        <tr><td>최소값 (Min)</td><td class="text-end">{overall['min']:.4f}</td></tr>
                        <tr><td>최대값 (Max)</td><td class="text-end">{overall['max']:.4f}</td></tr>
                        <tr><td>Q1 (25%)</td><td class="text-end">{overall['q1']:.4f}</td></tr>
                        <tr><td>Q3 (75%)</td><td class="text-end">{overall['q3']:.4f}</td></tr>
                    </table>
                </div>
                
                <div class="col-md-6">
                    <h6>📊 분포 분석</h6>
                    <div class="distribution-chart">
                        <canvas id="distributionChart"></canvas>
                    </div>
                </div>
            </div>
            
            {self._create_metric_details_table(stats.get('by_metric', {}))}
        </div>
        '''
        
        return html
    
    def _create_metric_details_table(self, by_metric: Dict) -> str:
        """메트릭별 상세 테이블"""
        if not by_metric:
            return ""
        
        html = '''
        <div class="mt-4">
            <h6>📋 메트릭별 상세 분석</h6>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>메트릭</th>
                        <th>점수/평균</th>
                        <th>상태</th>
                        <th>변동계수</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for metric, data in by_metric.items():
            metric_kr = {
                'faithfulness': '충실도',
                'answer_relevancy': '답변 관련성',
                'context_precision': '컨텍스트 정밀도',
                'context_recall': '컨텍스트 재현율',
                'answer_correctness': '답변 정확도'
            }.get(metric, metric)
            
            score = data.get('score', data.get('mean', 0))
            status = data.get('status', self._get_score_status(score))
            cv = data.get('cv', 0)
            
            status_badge = {
                '우수': 'success',
                '양호': 'warning',
                '보통': 'secondary',
                '개선필요': 'danger'
            }.get(status, 'secondary')
            
            html += f'''
                <tr>
                    <td>{metric_kr}</td>
                    <td>{score:.4f}</td>
                    <td><span class="badge bg-{status_badge}">{status}</span></td>
                    <td>{cv:.2%} {self._get_cv_indicator(cv)}</td>
                </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return html
    
    def _get_cv_indicator(self, cv: float) -> str:
        """변동계수 지표"""
        if cv < 0.1:
            return '<span class="text-success">✓ 안정적</span>'
        elif cv < 0.2:
            return '<span class="text-warning">~ 보통</span>'
        else:
            return '<span class="text-danger">⚠ 불안정</span>'
    
    def _create_environment_section(self, environment: Dict) -> str:
        """환경 설정 섹션"""
        html = '<div class="row">'
        
        for i, (key, value) in enumerate(environment.items()):
            if i % 2 == 0 and i > 0:
                html += '</div><div class="row">'
            
            key_kr = {
                'model': '모델',
                'temperature': '온도',
                'dataset': '데이터셋',
                'embeddings': '임베딩',
                'batch_size': '배치 크기',
                'rate_limit': '속도 제한',
                'evaluation_time': '평가 시간'
            }.get(key, key)
            
            html += f'''
                <div class="col-md-6 mb-2">
                    <div class="env-item">
                        <span class="env-key">{key_kr}</span>
                        <span class="env-value">{value}</span>
                    </div>
                </div>
            '''
        
        html += '</div>'
        return html
    
    def _prepare_chart_data(self, metrics: Dict) -> str:
        """차트 데이터 준비"""
        labels = []
        values = []
        
        metric_order = ['faithfulness', 'answer_relevancy', 'context_precision', 
                       'context_recall', 'answer_correctness']
        
        for metric in metric_order:
            if metric in metrics:
                labels.append({
                    'faithfulness': '충실도',
                    'answer_relevancy': '답변 관련성',
                    'context_precision': '컨텍스트 정밀도',
                    'context_recall': '컨텍스트 재현율',
                    'answer_correctness': '답변 정확도'
                }.get(metric, metric))
                values.append(round(metrics[metric], 3))
        
        return json.dumps({
            'labels': labels,
            'values': values
        })
    
    def _get_html_template(self) -> str:
        """HTML 템플릿"""
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAGTrace 평가 보고서 - {run_id}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary-color: #4f46e5;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --bg-light: #f9fafb;
            --border-color: #e5e7eb;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-light);
            color: #1f2937;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* 헤더 */
        .report-header {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
        }}
        
        .report-title {{
            font-size: 2rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 1rem;
        }}
        
        .report-meta {{
            display: flex;
            gap: 2rem;
            color: #6b7280;
            font-size: 0.95rem;
        }}
        
        .report-meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        /* 요약 카드 */
        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .summary-score {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color), #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        /* 메트릭 카드 */
        .metric-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .metric-header i {{
            font-size: 1.5rem;
            color: var(--primary-color);
        }}
        
        .metric-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.5rem;
        }}
        
        .metric-score {{
            font-size: 2.5rem;
            font-weight: 700;
            margin: 1rem 0;
        }}
        
        .metric-bar {{
            height: 8px;
            background: var(--border-color);
            border-radius: 4px;
            overflow: hidden;
            margin: 1rem 0;
        }}
        
        .metric-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease;
        }}
        
        .metric-description {{
            font-size: 0.875rem;
            color: #6b7280;
            margin: 0;
        }}
        
        /* 섹션 */
        .section {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #111827;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border-color);
        }}
        
        /* 해석 섹션 */
        .interpretation-section {{
            padding: 1rem 0;
        }}
        
        /* 통계 테이블 */
        .table {{
            font-size: 0.95rem;
        }}
        
        .table th {{
            background: var(--bg-light);
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid var(--border-color);
        }}
        
        /* 환경 설정 */
        .env-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem;
            background: var(--bg-light);
            border-radius: 8px;
        }}
        
        .env-key {{
            font-weight: 600;
            color: #4b5563;
        }}
        
        .env-value {{
            color: #6b7280;
            font-family: 'Courier New', monospace;
        }}
        
        /* 뱃지 */
        .badge {{
            padding: 0.25rem 0.75rem;
            font-weight: 500;
            font-size: 0.875rem;
        }}
        
        /* 차트 컨테이너 */
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 2rem 0;
        }}
        
        /* 반응형 */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .report-meta {{
                flex-direction: column;
                gap: 0.5rem;
            }}
            
            .summary-score {{
                font-size: 2rem;
            }}
            
            .metric-score {{
                font-size: 2rem;
            }}
        }}
        
        /* 인쇄 스타일 */
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                max-width: 100%;
            }}
            
            .metric-card:hover {{
                transform: none;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 헤더 -->
        <div class="report-header">
            <h1 class="report-title">
                <i class="bi bi-graph-up-arrow"></i>
                RAGTrace 평가 보고서
            </h1>
            <div class="report-meta">
                <div class="report-meta-item">
                    <i class="bi bi-calendar-check"></i>
                    <span>{date}</span>
                </div>
                <div class="report-meta-item">
                    <i class="bi bi-database"></i>
                    <span>{dataset_name}</span>
                </div>
                <div class="report-meta-item">
                    <i class="bi bi-file-earmark-text"></i>
                    <span>{total_samples}개 샘플</span>
                </div>
                <div class="report-meta-item">
                    <i class="bi bi-key"></i>
                    <span>{run_id}</span>
                </div>
            </div>
        </div>
        
        <!-- 종합 점수 -->
        <div class="summary-card">
            <div class="row align-items-center">
                <div class="col-md-4 text-center">
                    <div class="summary-score">{overall_score:.3f}</div>
                    <p class="text-muted">종합 점수</p>
                </div>
                <div class="col-md-8">
                    <div class="chart-container">
                        <canvas id="radarChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 메트릭 카드 -->
        <div class="section">
            <h2 class="section-title">📊 평가 메트릭</h2>
            <div class="row">
                {metrics_cards}
            </div>
        </div>
        
        <!-- 해석 -->
        <div class="section">
            <h2 class="section-title">🔍 상세 분석 및 해석</h2>
            {interpretation}
        </div>
        
        <!-- 통계 분석 -->
        <div class="section">
            <h2 class="section-title">📈 통계 분석</h2>
            {statistics_section}
        </div>
        
        <!-- 환경 설정 -->
        <div class="section">
            <h2 class="section-title">⚙️ 평가 환경</h2>
            {environment_section}
        </div>
        
        <!-- 푸터 -->
        <div class="text-center text-muted mt-4">
            <p>RAGTrace Lite v2.0 | 🤖 AI 기반 분석 보고서</p>
        </div>
    </div>
    
    <script>
        // Radar Chart
        const chartData = {chart_data};
        
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: {{
                labels: chartData.labels,
                datasets: [{{
                    label: '점수',
                    data: chartData.values,
                    backgroundColor: 'rgba(79, 70, 229, 0.2)',
                    borderColor: 'rgba(79, 70, 229, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(79, 70, 229, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(79, 70, 229, 1)',
                    pointRadius: 4,
                    pointHoverRadius: 6
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
                            stepSize: 0.2,
                            font: {{
                                size: 10
                            }}
                        }},
                        pointLabels: {{
                            font: {{
                                size: 12,
                                weight: '500'
                            }}
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
        
        // Distribution Chart (if exists)
        const distCtx = document.getElementById('distributionChart');
        if (distCtx) {{
            new Chart(distCtx, {{
                type: 'bar',
                data: {{
                    labels: chartData.labels,
                    datasets: [{{
                        label: '점수 분포',
                        data: chartData.values,
                        backgroundColor: chartData.values.map(v => 
                            v >= 0.8 ? 'rgba(16, 185, 129, 0.8)' :
                            v >= 0.6 ? 'rgba(245, 158, 11, 0.8)' :
                            'rgba(239, 68, 68, 0.8)'
                        ),
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
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
                        }}
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>'''