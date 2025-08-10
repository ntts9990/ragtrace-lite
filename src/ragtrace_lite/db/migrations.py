"""Database migrations for schema evolution"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles database schema migrations"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        
    def get_current_version(self) -> int:
        """Get current schema version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            if not cursor.fetchone():
                return 0
                
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else 0
            
        except Exception as e:
            logger.error(f"Failed to get schema version: {e}")
            return 0
    
    def apply_migration_v3(self) -> bool:
        """Migration v2 -> v3: Add denormalized metric columns to evaluations table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists and get current schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations'")
            if not cursor.fetchone():
                logger.info("evaluations table doesn't exist, will be created by schema")
                return True
            
            # Check current columns
            cursor.execute("PRAGMA table_info(evaluations)")
            columns = [col[1] for col in cursor.fetchall()]
            logger.info(f"Current evaluations columns: {columns}")
            
            # Add missing columns that are expected by the schema/dashboard
            all_expected_columns = [
                ('llm', 'TEXT'),
                ('dataset_hash', 'TEXT'),
                ('total_items', 'INTEGER'),
                ('metrics', 'TEXT'),
                ('config_data', 'TEXT'),
                ('environment_json', 'TEXT'),
                ('error_message', 'TEXT'),
                ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            # Add missing metric columns if they don't exist
            metric_columns = [
                ('faithfulness', 'REAL'),
                ('answer_relevancy', 'REAL'), 
                ('context_precision', 'REAL'),
                ('context_recall', 'REAL'),
                ('answer_correctness', 'REAL')
            ]
            
            all_expected_columns.extend(metric_columns)
            
            for col_name, col_type in all_expected_columns:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {col_name} {col_type}")
                        logger.info(f"Added column: {col_name} {col_type}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e):
                            logger.warning(f"Failed to add column {col_name}: {e}")
            
            # Create schema_version table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Update schema version
            cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (3)")
            
            conn.commit()
            conn.close()
            
            logger.info("Migration v2 -> v3 completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration v2 -> v3 failed: {e}")
            return False
    
    def migrate_to_latest(self) -> bool:
        """Apply all necessary migrations to reach latest schema"""
        current_version = self.get_current_version()
        
        if current_version < 3:
            logger.info("Applying migration v2 -> v3...")
            if not self.apply_migration_v3():
                return False
        
        logger.info(f"Database is up to date (version {self.get_current_version()})")
        return True


def migrate_database(db_path: Path) -> bool:
    """Convenience function to migrate database to latest version"""
    migrator = DatabaseMigrator(db_path)
    return migrator.migrate_to_latest()