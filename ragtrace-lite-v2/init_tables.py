#!/usr/bin/env python
"""Initialize database tables using DatabaseManager"""

import sys
from pathlib import Path

# Add src path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def init_tables():
    """Initialize database using DatabaseManager"""
    
    try:
        from ragtrace_lite.db.manager import DatabaseManager
        from ragtrace_lite.config.config_loader import get_config
        
        # Use unified configuration
        config = get_config()
        db_config = config._get_default_config()['database']
        db_path = db_config['path']
        
        print(f"Initializing database at: {db_path}")
        
        # Initialize DatabaseManager (this will create all tables and run migrations)
        db_manager = DatabaseManager(str(db_path))
        
        print("✅ Database tables initialized successfully")
        print(f"   - Database path: {db_manager.db_path}")
        print(f"   - Tables created with latest schema")
        print(f"   - Migrations applied if needed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("Make sure you're running from the ragtrace-lite-v2 directory")
        return False
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_tables()
    sys.exit(0 if success else 1)