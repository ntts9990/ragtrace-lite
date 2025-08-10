"""HTML report generation with templates and section builders"""

from datetime import datetime
from typing import Dict, Any, List
import logging

from .report_utils import ReportUtils

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate HTML format reports with language support"""
    
    def __init__(self):
        self.utils = ReportUtils()
        self.templates = self._load_templates()
    
    def generate(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        language: str,
        dataset_name: str
    ) -> str:
        """Generate HTML report"""
        is_korean = language == "ko"
        template = self.templates["ko" if is_korean else "en"]
        
        # Calculate summary statistics
        summary_stats = self.utils.calculate_summary_stats(results)
        
        # Generate sections
        title = self._get_title(is_korean)
        summary_section = self._generate_summary_section(
            run_id, dataset_name, summary_stats, is_korean
        )
        metrics_section = self._generate_metrics_section(results, is_korean)
        details_section = self._generate_details_section(results, is_korean)
        environment_section = self._generate_environment_section(environment, is_korean)
        
        # Format HTML
        html_content = template.format(
            title=title,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary_section=summary_section,
            metrics_section=metrics_section,
            details_section=details_section,
            environment_section=environment_section
        )
        
        return html_content
    
    def _load_templates(self) -> Dict[str, str]:
        """Load HTML templates for different languages"""
        templates = {
            "ko": """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Noto Sans KR', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metric-value {{ font-weight: bold; color: #2c3e50; }}
        .good {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .poor {{ color: #e74c3c; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .environment {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="timestamp">생성 시간: {generation_time}</p>
        {summary_section}
        {metrics_section}
        {details_section}
        {environment_section}
    </div>
</body>
</html>""",
            "en": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metric-value {{ font-weight: bold; color: #2c3e50; }}
        .good {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .poor {{ color: #e74c3c; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .environment {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="timestamp">Generated at: {generation_time}</p>
        {summary_section}
        {metrics_section}
        {details_section}
        {environment_section}
    </div>
</body>
</html>"""
        }
        return templates
    
    def _get_title(self, is_korean: bool) -> str:
        """Get report title based on language"""
        return "RAG 평가 보고서" if is_korean else "RAG Evaluation Report"
    
    def _generate_summary_section(
        self, run_id: str, dataset_name: str, summary_stats: Dict, is_korean: bool
    ) -> str:
        """Generate summary section HTML"""
        if is_korean:
            return f"""
            <div class="summary">
                <h2>평가 요약</h2>
                <p><strong>실행 ID:</strong> {run_id}</p>
                <p><strong>데이터셋:</strong> {dataset_name}</p>
                <p><strong>평가 항목 수:</strong> {summary_stats.get('total_items', 0)}</p>
                <p><strong>평균 점수:</strong> <span class="metric-value {summary_stats.get('performance_class', '')}">{summary_stats.get('average_score', 0):.3f}</span></p>
                <p><strong>성능 수준:</strong> <span class="{summary_stats.get('performance_class', '')}">{summary_stats.get('performance_level', '평가 중')}</span></p>
            </div>
            """
        else:
            return f"""
            <div class="summary">
                <h2>Evaluation Summary</h2>
                <p><strong>Run ID:</strong> {run_id}</p>
                <p><strong>Dataset:</strong> {dataset_name}</p>
                <p><strong>Items Evaluated:</strong> {summary_stats.get('total_items', 0)}</p>
                <p><strong>Average Score:</strong> <span class="metric-value {summary_stats.get('performance_class', '')}">{summary_stats.get('average_score', 0):.3f}</span></p>
                <p><strong>Performance Level:</strong> <span class="{summary_stats.get('performance_class', '')}">{summary_stats.get('performance_level_en', 'Evaluating')}</span></p>
            </div>
            """
    
    def _generate_metrics_section(self, results: Dict, is_korean: bool) -> str:
        """Generate metrics section HTML"""
        metrics = results.get("metrics", {})
        if not metrics:
            return ""
        
        metric_names_ko = {
            "faithfulness": "충실성",
            "answer_relevancy": "답변 관련성",
            "context_precision": "컨텍스트 정밀도",
            "context_recall": "컨텍스트 재현율",
            "answer_correctness": "답변 정확성"
        }
        
        header = "메트릭별 점수" if is_korean else "Metrics Scores"
        rows = []
        
        for metric, value in metrics.items():
            if value is not None:
                display_name = metric_names_ko.get(metric, metric) if is_korean else metric.replace("_", " ").title()
                rows.append(f"<tr><td>{display_name}</td><td class='metric-value'>{value:.3f}</td></tr>")
        
        if not rows:
            return ""
        
        return f"""
        <h2>{header}</h2>
        <table>
            <tr><th>{'메트릭' if is_korean else 'Metric'}</th><th>{'점수' if is_korean else 'Score'}</th></tr>
            {''.join(rows)}
        </table>
        """
    
    def _generate_details_section(self, results: Dict, is_korean: bool) -> str:
        """Generate details section HTML"""
        items = results.get("items", [])
        if not items:
            return ""
        
        header = "상세 평가 결과" if is_korean else "Detailed Results"
        table_headers = ["질문", "답변", "점수"] if is_korean else ["Question", "Answer", "Score"]
        
        rows = []
        for idx, item in enumerate(items[:10], 1):  # Limit to first 10 items
            question = item.get("question", "")[:100] + "..."
            answer = item.get("answer", "")[:100] + "..."
            scores = item.get("metrics", {})
            avg_score = sum(v for v in scores.values() if v is not None) / len([v for v in scores.values() if v is not None]) if scores else 0
            
            rows.append(f"""
            <tr>
                <td>{question}</td>
                <td>{answer}</td>
                <td class='metric-value'>{avg_score:.3f}</td>
            </tr>
            """)
        
        return f"""
        <h2>{header}</h2>
        <table>
            <tr>{''.join(f'<th>{h}</th>' for h in table_headers)}</tr>
            {''.join(rows)}
        </table>
        """
    
    def _generate_environment_section(self, environment: Dict, is_korean: bool) -> str:
        """Generate environment section HTML"""
        header = "실행 환경" if is_korean else "Environment"
        
        env_items = []
        if environment.get("model_name"):
            label = "모델" if is_korean else "Model"
            env_items.append(f"<p><strong>{label}:</strong> {environment['model_name']}</p>")
        if environment.get("temperature") is not None:
            label = "온도" if is_korean else "Temperature"
            env_items.append(f"<p><strong>{label}:</strong> {environment['temperature']}</p>")
        if environment.get("llm_provider"):
            label = "LLM 제공자" if is_korean else "LLM Provider"
            env_items.append(f"<p><strong>{label}:</strong> {environment['llm_provider']}</p>")
        
        if not env_items:
            return ""
        
        return f"""
        <div class="environment">
            <h2>{header}</h2>
            {''.join(env_items)}
        </div>
        """