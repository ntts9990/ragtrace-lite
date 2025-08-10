"""Core report generation orchestration and base functionality"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum
import logging

from .html_generator import HTMLReportGenerator
from .markdown_generator import MarkdownReportGenerator
from .report_utils import ReportUtils

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


class ReportGenerator:
    """Unified report generator supporting multiple formats and languages"""
    
    def __init__(self):
        self.html_generator = HTMLReportGenerator()
        self.markdown_generator = MarkdownReportGenerator()
        self.utils = ReportUtils()
    
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
            output_path: Optional output file path
            dataset_name: Name of the dataset
            
        Returns:
            Generated report content as string
        """
        logger.info(f"Generating {format.value} report in {language.value} for {run_id}")
        
        # Generate report based on format
        if format == ReportFormat.HTML:
            content = self.html_generator.generate(
                run_id=run_id,
                results=results,
                environment=environment,
                language=language,
                dataset_name=dataset_name
            )
        elif format == ReportFormat.MARKDOWN:
            content = self.markdown_generator.generate(
                run_id=run_id,
                results=results,
                environment=environment,
                language=language,
                dataset_name=dataset_name
            )
        elif format == ReportFormat.JSON:
            content = self.utils.generate_json_report(
                run_id=run_id,
                results=results,
                environment=environment,
                dataset_name=dataset_name
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save to file if output path is provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ReportFormat.JSON:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json.loads(content), f, ensure_ascii=False, indent=2)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(f"Report saved to {output_path}")
        
        return content