"""
Report generator module - exports main functionality

This module maintains backward compatibility while using the new modular structure.
"""

from .report_core import ReportGenerator, ReportFormat, ReportLanguage
from .report_utils import ReportUtils

__all__ = [
    'ReportGenerator',
    'ReportFormat', 
    'ReportLanguage',
    'ReportUtils'
]

# For backward compatibility, create a default instance
_default_generator = ReportGenerator()

# Export convenience functions
generate_report = _default_generator.generate_report