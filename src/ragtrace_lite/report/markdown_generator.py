"""Markdown report generation for both Korean and English"""

from datetime import datetime
from typing import Dict, Any
import logging

from .report_utils import ReportUtils

logger = logging.getLogger(__name__)


class MarkdownReportGenerator:
    """Generate Markdown format reports with language support"""
    
    def __init__(self):
        self.utils = ReportUtils()
    
    def generate(
        self,
        run_id: str,
        results: Dict[str, Any],
        environment: Dict[str, Any],
        language: str,
        dataset_name: str
    ) -> str:
        """Generate Markdown report"""
        is_korean = language == "ko"
        
        # Calculate summary statistics
        summary_stats = self.utils.calculate_summary_stats(results)
        
        # Build markdown sections
        sections = []
        
        # Title and metadata
        title = "# RAG 평가 보고서\n" if is_korean else "# RAG Evaluation Report\n"
        sections.append(title)
        sections.append(f"**Run ID:** {run_id}\n")
        sections.append(f"**{'생성 시간' if is_korean else 'Generated at'}:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sections.append(f"**{'데이터셋' if is_korean else 'Dataset'}:** {dataset_name}\n")
        sections.append("---\n")
        
        # Summary section
        if is_korean:
            sections.append("## 평가 요약\n")
            sections.append(f"- **평가 항목 수:** {summary_stats.get('total_items', 0)}\n")
            sections.append(f"- **평균 점수:** {summary_stats.get('average_score', 0):.3f}\n")
            sections.append(f"- **성능 수준:** {summary_stats.get('performance_level', '평가 중')}\n\n")
        else:
            sections.append("## Evaluation Summary\n")
            sections.append(f"- **Items Evaluated:** {summary_stats.get('total_items', 0)}\n")
            sections.append(f"- **Average Score:** {summary_stats.get('average_score', 0):.3f}\n")
            sections.append(f"- **Performance Level:** {summary_stats.get('performance_level_en', 'Evaluating')}\n\n")
        
        # Metrics section
        metrics_md = self._format_metrics(results, is_korean)
        if metrics_md:
            sections.append(metrics_md)
        
        # Details section
        details_md = self._format_details(results, is_korean)
        if details_md:
            sections.append(details_md)
        
        # Environment section
        env_md = self._format_environment(environment, is_korean)
        if env_md:
            sections.append(env_md)
        
        return ''.join(sections)
    
    def _format_metrics(self, results: Dict, is_korean: bool) -> str:
        """Format metrics section for markdown"""
        metrics = results.get("metrics", {})
        if not metrics:
            return ""
        
        if is_korean:
            return self._format_metrics_ko(metrics)
        else:
            return self._format_metrics_en(metrics)
    
    def _format_metrics_ko(self, metrics: Dict) -> str:
        """Format metrics in Korean"""
        metric_names = {
            "faithfulness": "충실성",
            "answer_relevancy": "답변 관련성",
            "context_precision": "컨텍스트 정밀도",
            "context_recall": "컨텍스트 재현율",
            "answer_correctness": "답변 정확성"
        }
        
        lines = ["## 메트릭별 점수\n\n"]
        lines.append("| 메트릭 | 점수 |\n")
        lines.append("|--------|------|\n")
        
        for metric, value in metrics.items():
            if value is not None:
                display_name = metric_names.get(metric, metric)
                lines.append(f"| {display_name} | {value:.3f} |\n")
        
        lines.append("\n")
        return ''.join(lines)
    
    def _format_metrics_en(self, metrics: Dict) -> str:
        """Format metrics in English"""
        lines = ["## Metrics Scores\n\n"]
        lines.append("| Metric | Score |\n")
        lines.append("|--------|-------|\n")
        
        for metric, value in metrics.items():
            if value is not None:
                display_name = metric.replace("_", " ").title()
                lines.append(f"| {display_name} | {value:.3f} |\n")
        
        lines.append("\n")
        return ''.join(lines)
    
    def _format_details(self, results: Dict, is_korean: bool) -> str:
        """Format details section for markdown"""
        items = results.get("items", [])
        if not items:
            return ""
        
        if is_korean:
            return self._format_details_ko(items)
        else:
            return self._format_details_en(items)
    
    def _format_details_ko(self, items: list) -> str:
        """Format details in Korean"""
        lines = ["## 상세 평가 결과\n\n"]
        
        for idx, item in enumerate(items[:5], 1):  # Show first 5 items
            lines.append(f"### 항목 {idx}\n\n")
            
            question = item.get("question", "")
            lines.append(f"**질문:** {question}\n\n")
            
            answer = item.get("answer", "")
            if len(answer) > 200:
                answer = answer[:200] + "..."
            lines.append(f"**답변:** {answer}\n\n")
            
            item_metrics = item.get("metrics", {})
            if item_metrics:
                lines.append("**점수:**\n")
                for metric, score in item_metrics.items():
                    if score is not None:
                        lines.append(f"- {metric}: {score:.3f}\n")
                lines.append("\n")
        
        return ''.join(lines)
    
    def _format_details_en(self, items: list) -> str:
        """Format details in English"""
        lines = ["## Detailed Results\n\n"]
        
        for idx, item in enumerate(items[:5], 1):  # Show first 5 items
            lines.append(f"### Item {idx}\n\n")
            
            question = item.get("question", "")
            lines.append(f"**Question:** {question}\n\n")
            
            answer = item.get("answer", "")
            if len(answer) > 200:
                answer = answer[:200] + "..."
            lines.append(f"**Answer:** {answer}\n\n")
            
            item_metrics = item.get("metrics", {})
            if item_metrics:
                lines.append("**Scores:**\n")
                for metric, score in item_metrics.items():
                    if score is not None:
                        display_name = metric.replace("_", " ").title()
                        lines.append(f"- {display_name}: {score:.3f}\n")
                lines.append("\n")
        
        return ''.join(lines)
    
    def _format_environment(self, environment: Dict, is_korean: bool) -> str:
        """Format environment section for markdown"""
        if not environment:
            return ""
        
        if is_korean:
            return self._format_environment_ko(environment)
        else:
            return self._format_environment_en(environment)
    
    def _format_environment_ko(self, environment: Dict) -> str:
        """Format environment in Korean"""
        lines = ["## 실행 환경\n\n"]
        
        if environment.get("model_name"):
            lines.append(f"- **모델:** {environment['model_name']}\n")
        if environment.get("temperature") is not None:
            lines.append(f"- **온도:** {environment['temperature']}\n")
        if environment.get("llm_provider"):
            lines.append(f"- **LLM 제공자:** {environment['llm_provider']}\n")
        if environment.get("embedding_model"):
            lines.append(f"- **임베딩 모델:** {environment['embedding_model']}\n")
        
        lines.append("\n")
        return ''.join(lines)
    
    def _format_environment_en(self, environment: Dict) -> str:
        """Format environment in English"""
        lines = ["## Environment\n\n"]
        
        if environment.get("model_name"):
            lines.append(f"- **Model:** {environment['model_name']}\n")
        if environment.get("temperature") is not None:
            lines.append(f"- **Temperature:** {environment['temperature']}\n")
        if environment.get("llm_provider"):
            lines.append(f"- **LLM Provider:** {environment['llm_provider']}\n")
        if environment.get("embedding_model"):
            lines.append(f"- **Embedding Model:** {environment['embedding_model']}\n")
        
        lines.append("\n")
        return ''.join(lines)