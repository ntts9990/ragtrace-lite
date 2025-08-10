#!/usr/bin/env python
"""
RAGTrace Lite Dashboard - Unified Entry Point
Supports both development and production modes
"""

import sys
import os
import webbrowser
import threading
import time
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ragtrace_lite.dashboard.app import app


def open_browser(url: str, delay: int = 2):
    """Open browser after a delay"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"🔗 Browser opened automatically: {url}")
    except:
        print(f"🔗 Please open {url} in your browser")


def run_dashboard(host='127.0.0.1', port=5000, debug=False, open_browser_flag=True):
    """
    Run the RAGTrace dashboard
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable Flask debug mode
        open_browser_flag: Automatically open browser
    """
    print(f"""
    ╔════════════════════════════════════════╗
    ║     RAGTrace Lite v2 Dashboard        ║
    ╚════════════════════════════════════════╝
    
    📊 Features:
    • Evaluation report listing and filtering
    • Detailed metrics visualization
    • Multi-report comparison analysis
    • Statistical testing and trend analysis
    • HTML report export
    
    🌐 Server starting on: http://{host}:{port}
    📂 Database: data/ragtrace.db
    
    Press Ctrl+C to stop
    {"="*50}
    """)
    
    # Open browser in background if requested
    if open_browser_flag:
        browser_thread = threading.Thread(
            target=open_browser, 
            args=(f'http://{host}:{port}',),
            daemon=True
        )
        browser_thread.start()
    
    # Start Flask app
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point with CLI arguments"""
    parser = argparse.ArgumentParser(description='RAGTrace Lite Dashboard')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    
    args = parser.parse_args()
    
    # Set Flask environment based on debug flag
    if args.debug:
        os.environ['FLASK_ENV'] = 'development'
    else:
        os.environ['FLASK_ENV'] = 'production'
    
    run_dashboard(
        host=args.host,
        port=args.port,
        debug=args.debug,
        open_browser_flag=not args.no_browser
    )


if __name__ == '__main__':
    main()