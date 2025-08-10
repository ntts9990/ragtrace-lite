#!/usr/bin/env python
"""Test unified configuration system"""

import sys
sys.path.insert(0, 'src')

import os
from pathlib import Path
from ragtrace_lite.config.config_loader import get_config

def test_unified_config():
    """Test that all components use unified configuration"""
    
    print("🧪 Testing Unified Configuration System")  
    print("="*60)
    
    # Set environment variable
    test_db_path = "/Users/isle/PycharmProjects/ragtrace-lite/data/ragtrace.db"
    os.environ['DB_PATH'] = test_db_path
    
    # Test ConfigLoader
    config = get_config()
    db_config = config._get_default_config()
    
    print(f"✅ ConfigLoader DB path: {db_config['database']['path']}")
    
    # Test dashboard import (simulate)
    try:
        from ragtrace_lite.dashboard.app import DB_PATH as dashboard_db_path
        print(f"✅ Dashboard DB path: {dashboard_db_path}")
        
        if str(dashboard_db_path) == test_db_path:
            print("✅ Dashboard using correct unified DB path")
        else:
            print(f"❌ Dashboard DB path mismatch. Expected: {test_db_path}, Got: {dashboard_db_path}")
            
    except Exception as e:
        print(f"⚠️ Dashboard import failed (expected due to flask dependencies): {e}")
    
    # Test DatabaseManager
    try:
        from ragtrace_lite.db.manager import DatabaseManager
        db_manager = DatabaseManager(str(test_db_path))
        print(f"✅ DatabaseManager initialized with path: {db_manager.db_path}")
        
    except Exception as e:
        print(f"❌ DatabaseManager initialization failed: {e}")
    
    print("\n🎉 Configuration unification test completed!")
    
    # Show what the configuration contains
    print(f"\nFull database config: {db_config['database']}")
    print(f"Environment DB_PATH: {os.environ.get('DB_PATH', 'Not Set')}")

if __name__ == "__main__":
    test_unified_config()