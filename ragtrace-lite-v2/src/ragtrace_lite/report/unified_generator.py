"""Unified report generator supporting multiple formats and languages"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Literal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Report format options"""
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class ReportLanguage(str, Enum):
    """Report language options"""
    ENGLISH = "en"
    KOREAN = "ko"


class UnifiedReportGenerator:
    """Unified report generator supporting multiple formats and languages"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def generate_report(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        format: ReportFormat = ReportFormat.HTML,
        language: ReportLanguage = ReportLanguage.KOREAN,
        output_path: Optional[Union[str, Path]] = None,
        dataset_name: str = "평가 데이터셋"
    ) -> str:
        """
        Generate evaluation report in specified format and language
        
        Args:
            run_id: Evaluation run identifier
            results: Evaluation results dictionary
            environment: Environment information
            format: Output format (html, markdown, json)
            language: Report language (en, ko)
            output_path: Optional path to save the report
            dataset_name: Dataset name for display
            
        Returns:
            Generated report content as string
        """
        
        try:
            # Generate content based on format
            if format == ReportFormat.HTML:
                content = self._generate_html_report(
                    run_id, results, environment, language, dataset_name
                )
            elif format == ReportFormat.MARKDOWN:
                content = self._generate_markdown_report(
                    run_id, results, environment, language, dataset_name
                )
            elif format == ReportFormat.JSON:
                content = self._generate_json_report(
                    run_id, results, environment, dataset_name
                )
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Save to file if path specified
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Report saved to: {output_path}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate {format} report: {e}")
            raise
    
    def _generate_html_report(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        language: ReportLanguage,
        dataset_name: str
    ) -> str:
        """Generate HTML report"""
        
        metrics = results.get('metrics', {})
        details = results.get('details', [])
        
        # Calculate summary statistics
        summary = self._calculate_summary_stats(metrics, details)
        
        # Generate content sections
        sections = {
            'title': self._get_title(language, dataset_name),
            'summary': self._generate_summary_section(summary, language),
            'metrics': self._generate_metrics_section(metrics, language),
            'details': self._generate_details_section(details, language),
            'environment': self._generate_environment_section(environment, language),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'run_id': run_id
        }
        
        # Use appropriate template
        template_key = f"html_{language.value}"
        template = self.templates.get(template_key, self.templates['html_ko'])
        
        return template.format(**sections)
    
    def _generate_markdown_report(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        language: ReportLanguage,
        dataset_name: str
    ) -> str:
        """Generate Markdown report"""
        
        metrics = results.get('metrics', {})
        details = results.get('details', [])
        
        if language == ReportLanguage.KOREAN:
            title = f"# {dataset_name} 평가 보고서"
            sections = [
                f"**평가 ID**: {run_id}",
                f"**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## 📊 종합 메트릭",
                self._format_metrics_markdown_ko(metrics),
                "",
                "## 🔍 상세 분석",
                self._format_details_markdown_ko(details),
                "",
                "## 🏗️ 환경 정보", 
                self._format_environment_markdown_ko(environment)
            ]
        else:
            title = f"# {dataset_name} Evaluation Report"
            sections = [
                f"**Evaluation ID**: {run_id}",
                f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## 📊 Overall Metrics",
                self._format_metrics_markdown_en(metrics),
                "",
                "## 🔍 Detailed Analysis",
                self._format_details_markdown_en(details),
                "",
                "## 🏗️ Environment Information",
                self._format_environment_markdown_en(environment)
            ]
        
        return "\n".join([title] + sections)
    
    def _generate_json_report(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        dataset_name: str
    ) -> str:
        """Generate JSON report"""
        
        report = {
            "meta": {
                "run_id": run_id,
                "dataset_name": dataset_name,
                "generated_at": datetime.now().isoformat(),
                "format_version": "1.0"
            },
            "metrics": results.get('metrics', {}),
            "details": results.get('details', []),
            "environment": environment,
            "summary": self._calculate_summary_stats(
                results.get('metrics', {}),
                results.get('details', [])
            )
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _calculate_summary_stats(self, metrics: Dict, details: List) -> Dict[str, Any]:
        """Calculate summary statistics"""
        
        if not metrics:
            return {}
        
        # Overall score
        metric_values = [v for v in metrics.values() if isinstance(v, (int, float))]
        overall_score = sum(metric_values) / len(metric_values) if metric_values else 0
        
        # Performance category
        if overall_score >= 0.8:
            category = "excellent"
            category_ko = "우수"
        elif overall_score >= 0.6:
            category = "good" 
            category_ko = "보통"
        else:
            category = "needs_improvement"
            category_ko = "개선필요"
        
        # Question-level statistics
        question_stats = {}
        if details:
            scores = []
            for detail in details:
                if isinstance(detail, dict) and 'metrics' in detail:
                    detail_metrics = detail['metrics']
                    if isinstance(detail_metrics, dict):
                        detail_values = [v for v in detail_metrics.values() 
                                       if isinstance(v, (int, float))]
                        if detail_values:
                            scores.append(sum(detail_values) / len(detail_values))
            
            if scores:
                import numpy as np
                question_stats = {
                    "avg_score": float(np.mean(scores)),
                    "std_score": float(np.std(scores)),
                    "min_score": float(np.min(scores)),
                    "max_score": float(np.max(scores)),
                    "total_questions": len(scores)
                }
        
        return {
            "overall_score": round(overall_score, 3),
            "category": category,
            "category_ko": category_ko,
            "question_stats": question_stats
        }
    
    def _load_templates(self) -> Dict[str, str]:
        """Load HTML templates for different languages"""
        
        # Korean HTML template
        html_ko_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header .meta {{ margin-top: 15px; opacity: 0.9; font-size: 1.1em; }}
        .section {{ padding: 30px; border-bottom: 1px solid #eee; }}
        .section:last-child {{ border-bottom: none; }}
        .section h2 {{ color: #333; font-size: 1.8em; margin-bottom: 20px; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; border-left: 4px solid #667eea; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .metric-name {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .details-table th {{ background-color: #f8f9fa; font-weight: 600; }}
        .score-bar {{ width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .score-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); border-radius: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                평가 ID: {run_id} | 생성 시간: {timestamp}
            </div>
        </div>
        
        <div class="section">
            <h2>📊 종합 메트릭</h2>
            {metrics}
        </div>
        
        <div class="section">
            <h2>📋 요약 통계</h2>
            {summary}
        </div>
        
        <div class="section">
            <h2>🔍 상세 분석</h2>
            {details}
        </div>
        
        <div class="section">
            <h2>🏗️ 환경 정보</h2>
            {environment}
        </div>
    </div>
</body>
</html>
        """
        
        # English HTML template (simplified for now)
        html_en_template = html_ko_template.replace("ko", "en").replace(
            "평가 ID:", "Evaluation ID:"
        ).replace(
            "생성 시간:", "Generated:"
        )
        
        return {
            "html_ko": html_ko_template,
            "html_en": html_en_template
        }
    
    def _get_title(self, language: ReportLanguage, dataset_name: str) -> str:
        """Get report title"""
        if language == ReportLanguage.KOREAN:
            return f"{dataset_name} 평가 보고서"
        else:
            return f"{dataset_name} Evaluation Report"
    
    def _generate_summary_section(self, summary: Dict, language: ReportLanguage) -> str:
        """Generate summary statistics section"""
        if not summary:
            return "통계 정보 없음" if language == ReportLanguage.KOREAN else "No statistics available"
        
        overall_score = summary.get('overall_score', 0)
        category = summary.get('category_ko' if language == ReportLanguage.KOREAN else 'category', 'unknown')
        
        if language == ReportLanguage.KOREAN:
            return f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>전체 성능: {category}</h3>
                <div class="score-bar">
                    <div class="score-fill" style="width: {overall_score * 100}%;"></div>
                </div>
                <p style="margin: 10px 0 0 0; text-align: center;">종합 점수: {overall_score:.3f}</p>
            </div>
            """
        else:
            return f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Overall Performance: {category}</h3>
                <div class="score-bar">
                    <div class="score-fill" style="width: {overall_score * 100}%;"></div>
                </div>
                <p style="margin: 10px 0 0 0; text-align: center;">Overall Score: {overall_score:.3f}</p>
            </div>
            """
    
    def _generate_metrics_section(self, metrics: Dict, language: ReportLanguage) -> str:
        """Generate metrics section"""
        if not metrics:
            return "메트릭 정보 없음" if language == ReportLanguage.KOREAN else "No metrics available"
        
        metric_names = {
            'faithfulness': {'ko': '신뢰성', 'en': 'Faithfulness'},
            'answer_relevancy': {'ko': '답변 관련성', 'en': 'Answer Relevancy'},
            'context_precision': {'ko': '컨텍스트 정확도', 'en': 'Context Precision'},
            'context_recall': {'ko': '컨텍스트 재현율', 'en': 'Context Recall'},
            'answer_correctness': {'ko': '답변 정확도', 'en': 'Answer Correctness'}
        }
        
        lang_key = 'ko' if language == ReportLanguage.KOREAN else 'en'
        cards = []
        
        for metric_key, value in metrics.items():
            if isinstance(value, (int, float)):
                display_name = metric_names.get(metric_key, {}).get(lang_key, metric_key.title())
                cards.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{value:.3f}</div>
                    <div class="metric-name">{display_name}</div>
                </div>
                """)
        
        return f'<div class="metrics-grid">{"".join(cards)}</div>'
    
    def _generate_details_section(self, details: List, language: ReportLanguage) -> str:
        """Generate details section"""
        if not details:
            return "상세 정보 없음" if language == ReportLanguage.KOREAN else "No details available"
        
        # For now, show basic question count
        question_count = len(details)
        if language == ReportLanguage.KOREAN:
            return f"<p>총 {question_count}개의 질문이 평가되었습니다.</p>"
        else:
            return f"<p>Total {question_count} questions were evaluated.</p>"
    
    def _generate_environment_section(self, environment: Dict, language: ReportLanguage) -> str:
        """Generate environment section"""
        if not environment:
            return "환경 정보 없음" if language == ReportLanguage.KOREAN else "No environment information"
        
        items = []
        for key, value in environment.items():
            items.append(f"<li><strong>{key}:</strong> {value}</li>")
        
        return f"<ul>{''.join(items)}</ul>"
    
    # Helper methods for markdown formatting
    def _format_metrics_markdown_ko(self, metrics: Dict) -> str:
        """Format metrics for Korean markdown"""
        if not metrics:
            return "메트릭 정보 없음"
        
        lines = []
        metric_names = {
            'faithfulness': '신뢰성',
            'answer_relevancy': '답변 관련성', 
            'context_precision': '컨텍스트 정확도',
            'context_recall': '컨텍스트 재현율',
            'answer_correctness': '답변 정확도'
        }
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                name = metric_names.get(key, key.title())
                lines.append(f"- **{name}**: {value:.3f}")
        
        return "\n".join(lines)
    
    def _format_metrics_markdown_en(self, metrics: Dict) -> str:
        """Format metrics for English markdown"""
        if not metrics:
            return "No metrics available"
        
        lines = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                lines.append(f"- **{key.title()}**: {value:.3f}")
        
        return "\n".join(lines)
    
    def _format_details_markdown_ko(self, details: List) -> str:
        """Format details for Korean markdown"""
        if not details:
            return "상세 정보 없음"
        
        lines = [f"총 {len(details)}개의 질문이 평가되었습니다."]
        
        # Show first few questions if available
        if len(details) > 0 and isinstance(details[0], dict):
            lines.append("")
            lines.append("### 주요 질문 예시")
            for i, detail in enumerate(details[:3]):  # Show first 3
                if 'question' in detail:
                    lines.append(f"{i+1}. {detail['question']}")
        
        return "\n".join(lines)
    
    def _format_details_markdown_en(self, details: List) -> str:
        """Format details for English markdown"""
        if not details:
            return "No details available"
            
        lines = [f"Total {len(details)} questions were evaluated."]
        
        # Show first few questions if available
        if len(details) > 0 and isinstance(details[0], dict):
            lines.append("")
            lines.append("### Sample Questions")
            for i, detail in enumerate(details[:3]):  # Show first 3
                if 'question' in detail:
                    lines.append(f"{i+1}. {detail['question']}")
        
        return "\n".join(lines)
    
    def _format_environment_markdown_ko(self, environment: Dict) -> str:
        """Format environment for Korean markdown"""
        if not environment:
            return "환경 정보 없음"
        
        lines = []
        for key, value in environment.items():
            lines.append(f"- **{key}**: {value}")
        
        return "\n".join(lines)
    
    def _format_environment_markdown_en(self, environment: Dict) -> str:
        """Format environment for English markdown"""
        if not environment:
            return "No environment information"
        
        lines = []
        for key, value in environment.items():
            lines.append(f"- **{key}**: {value}")
        
        return "\n".join(lines)


# Convenience functions for backward compatibility
def generate_html_report(
    run_id: str,
    results: Dict[str, Any],
    environment: Dict[str, Any],
    language: str = "ko",
    output_path: Optional[str] = None,
    dataset_name: str = "평가 데이터셋"
) -> str:
    """Generate HTML report - backward compatibility function"""
    generator = UnifiedReportGenerator()
    lang = ReportLanguage.KOREAN if language == "ko" else ReportLanguage.ENGLISH
    
    return generator.generate_report(
        run_id=run_id,
        results=results,
        environment=environment,
        format=ReportFormat.HTML,
        language=lang,
        output_path=output_path,
        dataset_name=dataset_name
    )


def generate_markdown_report(
    run_id: str,
    results: Dict[str, Any],
    environment: Dict[str, Any], 
    language: str = "ko",
    output_path: Optional[str] = None,
    dataset_name: str = "평가 데이터셋"
) -> str:
    """Generate Markdown report - convenience function"""
    generator = UnifiedReportGenerator()
    lang = ReportLanguage.KOREAN if language == "ko" else ReportLanguage.ENGLISH
    
    return generator.generate_report(
        run_id=run_id,
        results=results,
        environment=environment,
        format=ReportFormat.MARKDOWN,
        language=lang,
        output_path=output_path,
        dataset_name=dataset_name
    )