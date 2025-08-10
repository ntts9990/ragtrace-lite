#!/usr/bin/env python
"""Test dashboard functionality and display results"""

import sys
import os
sys.path.insert(0, 'src')

from ragtrace_lite.dashboard.app import app
from ragtrace_lite.dashboard.services import DashboardService
import json
from datetime import datetime

def test_dashboard_functionality():
    """Test dashboard service and data retrieval"""
    print("🧪 Testing Dashboard Functionality\n")
    
    # Test service initialization
    service = DashboardService()
    print("✅ DashboardService initialized")
    
    # Test data retrieval methods
    print("\n📊 Testing data retrieval...")
    
    try:
        # Get recent runs
        recent_runs = service.get_recent_runs(limit=5)
        print(f"✅ Recent runs: {len(recent_runs)} found")
        
        for i, run in enumerate(recent_runs[:3]):
            print(f"  {i+1}. Run ID: {run.get('run_id', 'unknown')}")
            print(f"     Dataset: {run.get('dataset_name', 'unknown')}")
            print(f"     Items: {run.get('dataset_items', 'unknown')}")
            if 'metrics' in run:
                metrics = json.loads(run['metrics']) if isinstance(run['metrics'], str) else run['metrics']
                print(f"     Metrics: {list(metrics.keys())}")
            print("")
            
    except Exception as e:
        print(f"❌ Error getting recent runs: {e}")
    
    try:
        # Get performance trends
        trends = service.get_performance_trends()
        print(f"✅ Performance trends: {len(trends)} data points")
        
    except Exception as e:
        print(f"❌ Error getting trends: {e}")
    
    try:
        # Get environment analysis
        env_analysis = service.get_environment_analysis()
        print(f"✅ Environment analysis: {len(env_analysis)} conditions")
        
        for condition in env_analysis[:3]:
            print(f"  - {condition.get('env_key', 'unknown')}: {condition.get('env_value', 'unknown')} (avg: {condition.get('avg_score', 0):.3f})")
            
    except Exception as e:
        print(f"❌ Error getting environment analysis: {e}")

if __name__ == "__main__":
    test_dashboard_functionality()
    
    print(f"\n🌐 Dashboard is ready!")
    print(f"🔗 URL: http://127.0.0.1:5000")
    print(f"📊 Database: {os.path.abspath('ragtrace.db')}")
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")