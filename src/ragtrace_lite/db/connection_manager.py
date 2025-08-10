"""Database connection management and initialization"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
import logging

from .schema import SCHEMAS, INDEXES, SCHEMA_VERSION
from .migrations import migrate_database

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Database connection management and schema initialization"""
    
    def __init__(self, db_path: str = "data/ragtrace.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            isolation_level='DEFERRED'
        )
        conn.row_factory = sqlite3.Row
        
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database with schema"""
        with self.get_connection() as conn:
            # Ensure metadata table exists first
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # Check and run migrations
            current_version = self._get_schema_version(conn)
            if current_version < SCHEMA_VERSION:
                logger.info(f"Migrating database from v{current_version} to v{SCHEMA_VERSION}")
                # Call migrate_database with just connection
                try:
                    migrate_database(conn)
                except Exception as e:
                    logger.warning(f"Migration skipped: {e}")
            
            # Create tables
            for table_name, schema in SCHEMAS.items():
                conn.execute(schema)
                logger.debug(f"Ensured table exists: {table_name}")
            
            # Create indexes
            for index_sql in INDEXES:
                try:
                    conn.execute(index_sql)
                except sqlite3.OperationalError:
                    pass  # Index already exists
            
            # Update schema version
            conn.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('schema_version', ?)
            """, (SCHEMA_VERSION,))
            
            logger.info(f"Database initialized at {self.db_path}")
    
    def _get_schema_version(self, conn) -> int:
        """Get current schema version"""
        try:
            cursor = conn.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            )
            row = cursor.fetchone()
            return int(row['value']) if row else 0
        except sqlite3.OperationalError:
            return 0