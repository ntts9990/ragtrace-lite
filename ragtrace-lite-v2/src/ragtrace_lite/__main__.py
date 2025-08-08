"""
-m 플래그 실행 지원
python -m ragtrace_lite
"""

import sys
from ragtrace_lite.cli import cli

if __name__ == "__main__":
    sys.exit(cli())