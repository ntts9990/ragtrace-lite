#!/usr/bin/env python
"""Start RAGTrace Dashboard for viewing results"""

import sys
import os
sys.path.insert(0, 'src')

from ragtrace_lite.dashboard.app import app
import webbrowser
import threading
import time

def open_browser():
    """Open browser after a delay"""
    time.sleep(2)
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("🔗 Opened browser automatically!")
    except:
        print("🔗 Please open http://127.0.0.1:5000 in your browser")

if __name__ == "__main__":
    print("🎯 RAGTrace Lite v2 Dashboard")
    print("="*50)
    print("🌐 Starting dashboard server...")
    print("📊 Database: ragtrace.db")
    print("🔗 URL: http://127.0.0.1:5000")
    print("="*50)
    
    # Open browser in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start Flask app
    app.run(host='127.0.0.1', port=5000, debug=True)