#!/usr/bin/env python
"""
Run RAGTrace Dashboard
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Set Flask environment
os.environ['FLASK_ENV'] = 'development'

from ragtrace_lite.dashboard.app import run_dashboard

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════╗
    ║     RAGTrace Dashboard Starting...     ║
    ╚════════════════════════════════════════╝
    
    📊 대시보드 기능:
    • 평가 보고서 목록 및 필터링
    • 상세 메트릭 시각화
    • 다중 보고서 비교 분석
    • 통계 검정 및 트렌드 분석
    • HTML 보고서 내보내기
    
    🌐 브라우저에서 접속:
    http://localhost:8080
    
    종료: Ctrl+C
    """)
    
    try:
        run_dashboard(host='127.0.0.1', port=8080, debug=True)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)