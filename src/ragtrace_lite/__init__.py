"""
RAGTrace Lite v2.0 - Lightweight RAG evaluation framework
"""

import sys
from pathlib import Path

# Windows 호환성을 위한 패키지 경로 보장
_package_root = Path(__file__).parent.parent
if str(_package_root) not in sys.path:
    sys.path.insert(0, str(_package_root))

# 버전 정보
__version__ = "2.0.0"

# 핵심 모듈 import (절대 경로)
from ragtrace_lite.core.excel_parser import ExcelParser
from ragtrace_lite.core.evaluator import Evaluator
from ragtrace_lite.db.manager import DatabaseManager
from ragtrace_lite.stats.window_compare import WindowComparator
from ragtrace_lite.report.generator import ReportGenerator

# Public API
__all__ = [
    "__version__",
    "ExcelParser",
    "Evaluator", 
    "DatabaseManager",
    "WindowComparator",
    "ReportGenerator",
]

# 패키지 정보
__author__ = "RAGTrace Team"
__email__ = "ragtrace@example.com"
__license__ = "Apache-2.0"