"""
RAGTrace Lite Logging System

Comprehensive logging system that:
- Stores all evaluation data with timestamps
- Tracks all API calls and responses
- Records system events and errors
- Prepares data for Elasticsearch migration
- Supports both SQLite and future Elasticsearch backends
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import traceback
import uuid
from enum import Enum

class LogLevel(Enum):
    """Log levels for the logging system"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log categories for better organization"""
    SYSTEM = "SYSTEM"
    EVALUATION = "EVALUATION"
    API_CALL = "API_CALL"
    DATABASE = "DATABASE"
    REPORT = "REPORT"
    ERROR = "ERROR"

class ComprehensiveLogger:
    """Enhanced logging system for RAGTrace Lite"""
    
    def __init__(self, db_path: str = "db/ragtrace_logs.db"):
        """Initialize the logging system"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup Python logging
        self._setup_python_logging()
        
        # Initialize database
        self._init_database()
        
        # Session ID for tracking related logs
        self.session_id = str(uuid.uuid4())
        
    def _setup_python_logging(self):
        """Configure Python's built-in logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('RAGTraceLite')
    
    def _init_database(self):
        """Initialize logging database with comprehensive schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Main logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Log metadata
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            component TEXT,
            function_name TEXT,
            
            -- Log content
            message TEXT NOT NULL,
            details TEXT,  -- JSON with additional data
            
            -- Context information
            run_id TEXT,
            item_index INTEGER,
            
            -- Error tracking
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            
            -- Performance metrics
            duration_ms REAL,
            memory_usage_mb REAL,
            
            -- Elasticsearch preparation
            es_indexed BOOLEAN DEFAULT FALSE,
            es_index_name TEXT
        )
        """)
        
        # API calls logging table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- API details
            provider TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            method TEXT,
            
            -- Request details
            request_id TEXT,
            request_headers TEXT,  -- JSON
            request_body TEXT,  -- JSON
            request_size_bytes INTEGER,
            
            -- Response details
            response_status_code INTEGER,
            response_headers TEXT,  -- JSON
            response_body TEXT,  -- JSON
            response_size_bytes INTEGER,
            response_time_ms REAL,
            
            -- Token usage
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            
            -- Error handling
            retry_count INTEGER DEFAULT 0,
            error_message TEXT,
            
            -- Context
            run_id TEXT,
            item_index INTEGER
        )
        """)
        
        # System events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Event details
            event_type TEXT NOT NULL,
            event_name TEXT NOT NULL,
            event_data TEXT,  -- JSON
            
            -- System metrics
            cpu_percent REAL,
            memory_percent REAL,
            disk_usage_percent REAL,
            
            -- Context
            run_id TEXT
        )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_session ON logs (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_run ON logs (run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_session ON api_logs (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_timestamp ON api_logs (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON system_events (session_id)")
        
        conn.commit()
        conn.close()
    
    def log(self, 
            level: LogLevel,
            category: LogCategory,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            component: Optional[str] = None,
            function_name: Optional[str] = None,
            run_id: Optional[str] = None,
            item_index: Optional[int] = None,
            duration_ms: Optional[float] = None):
        """Log a message with comprehensive metadata"""
        
        log_id = str(uuid.uuid4())
        
        # Log to Python logger
        self.logger.log(
            getattr(logging, level.value),
            f"[{category.value}] {message}"
        )
        
        # Store in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO logs (
                log_id, session_id, level, category, component, function_name,
                message, details, run_id, item_index, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                self.session_id,
                level.value,
                category.value,
                component,
                function_name,
                message,
                json.dumps(details) if details else None,
                run_id,
                item_index,
                duration_ms
            ))
            conn.commit()
        finally:
            conn.close()
        
        return log_id
    
    def log_api_call(self,
                     provider: str,
                     endpoint: str,
                     request_data: Dict[str, Any],
                     response_data: Dict[str, Any],
                     response_time_ms: float,
                     run_id: Optional[str] = None,
                     item_index: Optional[int] = None):
        """Log API call details"""
        
        log_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO api_logs (
                log_id, session_id, provider, endpoint, method,
                request_id, request_headers, request_body, request_size_bytes,
                response_status_code, response_headers, response_body, 
                response_size_bytes, response_time_ms,
                prompt_tokens, completion_tokens, total_tokens,
                run_id, item_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                self.session_id,
                provider,
                endpoint,
                request_data.get('method', 'POST'),
                request_data.get('request_id'),
                json.dumps(request_data.get('headers', {})),
                json.dumps(request_data.get('body', {})),
                len(json.dumps(request_data.get('body', {}))),
                response_data.get('status_code'),
                json.dumps(response_data.get('headers', {})),
                json.dumps(response_data.get('body', {})),
                len(json.dumps(response_data.get('body', {}))),
                response_time_ms,
                response_data.get('usage', {}).get('prompt_tokens'),
                response_data.get('usage', {}).get('completion_tokens'),
                response_data.get('usage', {}).get('total_tokens'),
                run_id,
                item_index
            ))
            conn.commit()
            
            # Also log as regular log
            self.log(
                LogLevel.INFO,
                LogCategory.API_CALL,
                f"API call to {provider} {endpoint}",
                details={
                    'response_time_ms': response_time_ms,
                    'status_code': response_data.get('status_code'),
                    'tokens': response_data.get('usage', {}).get('total_tokens')
                },
                run_id=run_id,
                item_index=item_index
            )
            
        finally:
            conn.close()
        
        return log_id
    
    def log_error(self,
                  error: Exception,
                  context: str,
                  run_id: Optional[str] = None,
                  item_index: Optional[int] = None,
                  additional_info: Optional[Dict[str, Any]] = None):
        """Log error with full stack trace"""
        
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'stack_trace': traceback.format_exc()
        }
        
        if additional_info:
            error_details.update(additional_info)
        
        log_id = self.log(
            LogLevel.ERROR,
            LogCategory.ERROR,
            f"Error in {context}: {type(error).__name__}",
            details=error_details,
            run_id=run_id,
            item_index=item_index
        )
        
        # Update error fields
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            UPDATE logs 
            SET error_type = ?, error_message = ?, stack_trace = ?
            WHERE log_id = ?
            """, (
                type(error).__name__,
                str(error),
                traceback.format_exc(),
                log_id
            ))
            conn.commit()
        finally:
            conn.close()
        
        return log_id
    
    def log_system_event(self,
                        event_type: str,
                        event_name: str,
                        event_data: Optional[Dict[str, Any]] = None,
                        run_id: Optional[str] = None):
        """Log system event"""
        
        event_id = str(uuid.uuid4())
        
        # Get system metrics
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            disk_usage_percent = psutil.disk_usage('/').percent
        except:
            cpu_percent = memory_percent = disk_usage_percent = None
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO system_events (
                event_id, session_id, event_type, event_name, event_data,
                cpu_percent, memory_percent, disk_usage_percent, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                self.session_id,
                event_type,
                event_name,
                json.dumps(event_data) if event_data else None,
                cpu_percent,
                memory_percent,
                disk_usage_percent,
                run_id
            ))
            conn.commit()
        finally:
            conn.close()
        
        return event_id
    
    @contextmanager
    def log_duration(self, 
                    category: LogCategory,
                    operation: str,
                    run_id: Optional[str] = None):
        """Context manager to log operation duration"""
        start_time = datetime.now()
        
        try:
            yield
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.log(
                LogLevel.INFO,
                category,
                f"{operation} completed",
                details={'duration_ms': duration_ms},
                run_id=run_id,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.log_error(e, operation, run_id=run_id)
            raise
    
    def export_for_elasticsearch(self, 
                               output_path: str,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> str:
        """Export logs in Elasticsearch bulk format"""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build date filter
        date_filter = ""
        params = []
        if start_date:
            date_filter += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND timestamp <= ?"
            params.append(end_date)
        
        documents = []
        
        # Export logs
        cursor.execute(f"""
        SELECT * FROM logs 
        WHERE 1=1 {date_filter}
        ORDER BY timestamp
        """, params)
        
        for row in cursor.fetchall():
            doc = {
                "_index": "ragtrace_logs",
                "_id": row['log_id'],
                "_source": dict(row)
            }
            # Parse JSON fields
            if row['details']:
                doc['_source']['details'] = json.loads(row['details'])
            
            documents.append(json.dumps({"index": doc}))
            documents.append(json.dumps(doc["_source"], default=str))
        
        # Export API logs
        cursor.execute(f"""
        SELECT * FROM api_logs 
        WHERE 1=1 {date_filter}
        ORDER BY timestamp
        """, params)
        
        for row in cursor.fetchall():
            doc = {
                "_index": "ragtrace_api_logs",
                "_id": row['log_id'],
                "_source": dict(row)
            }
            # Parse JSON fields
            for field in ['request_headers', 'request_body', 'response_headers', 'response_body']:
                if row[field]:
                    doc['_source'][field] = json.loads(row[field])
            
            documents.append(json.dumps({"index": doc}))
            documents.append(json.dumps(doc["_source"], default=str))
        
        # Export system events
        cursor.execute(f"""
        SELECT * FROM system_events 
        WHERE 1=1 {date_filter}
        ORDER BY timestamp
        """, params)
        
        for row in cursor.fetchall():
            doc = {
                "_index": "ragtrace_system_events",
                "_id": row['event_id'],
                "_source": dict(row)
            }
            if row['event_data']:
                doc['_source']['event_data'] = json.loads(row['event_data'])
            
            documents.append(json.dumps({"index": doc}))
            documents.append(json.dumps(doc["_source"], default=str))
        
        conn.close()
        
        # Write NDJSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(doc + '\n')
        
        print(f"📤 Exported {len(documents) // 2} log entries to: {output_file}")
        return str(output_file)
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of a logging session"""
        if not session_id:
            session_id = self.session_id
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get log statistics
        cursor.execute("""
        SELECT 
            COUNT(*) as total_logs,
            COUNT(DISTINCT run_id) as unique_runs,
            SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as error_count,
            SUM(CASE WHEN level = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
            MIN(timestamp) as start_time,
            MAX(timestamp) as end_time
        FROM logs
        WHERE session_id = ?
        """, (session_id,))
        
        result = cursor.fetchone()
        if result:
            log_stats = {
                'total_logs': result[0],
                'unique_runs': result[1],
                'error_count': result[2],
                'warning_count': result[3],
                'start_time': result[4],
                'end_time': result[5]
            }
        else:
            log_stats = {}
        
        # Get API statistics
        cursor.execute("""
        SELECT 
            COUNT(*) as total_api_calls,
            COUNT(DISTINCT provider) as unique_providers,
            AVG(response_time_ms) as avg_response_time,
            SUM(total_tokens) as total_tokens_used
        FROM api_logs
        WHERE session_id = ?
        """, (session_id,))
        
        result = cursor.fetchone()
        if result:
            api_stats = {
                'total_api_calls': result[0],
                'unique_providers': result[1],
                'avg_response_time': result[2],
                'total_tokens_used': result[3]
            }
        else:
            api_stats = {}
        
        conn.close()
        
        return {
            'session_id': session_id,
            'log_statistics': log_stats,
            'api_statistics': api_stats
        }


# Global logger instance
_logger_instance: Optional[ComprehensiveLogger] = None

def get_logger() -> ComprehensiveLogger:
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ComprehensiveLogger()
    return _logger_instance


def test_logging_system():
    """Test the logging system"""
    print("🧪 Testing Comprehensive Logging System\n")
    
    logger = ComprehensiveLogger("test_logs.db")
    
    try:
        # Test basic logging
        logger.log(
            LogLevel.INFO,
            LogCategory.SYSTEM,
            "System started",
            details={'version': '1.0.4'},
            component='main'
        )
        
        # Test API logging
        logger.log_api_call(
            provider='gemini',
            endpoint='/v1/models/gemini-2.0-flash:generateContent',
            request_data={
                'method': 'POST',
                'headers': {'Authorization': 'Bearer xxx'},
                'body': {'prompt': 'Test prompt'}
            },
            response_data={
                'status_code': 200,
                'body': {'content': 'Test response'},
                'usage': {
                    'prompt_tokens': 10,
                    'completion_tokens': 20,
                    'total_tokens': 30
                }
            },
            response_time_ms=150.5
        )
        
        # Test error logging
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.log_error(e, "test_function")
        
        # Test duration logging
        with logger.log_duration(LogCategory.EVALUATION, "test_operation"):
            import time
            time.sleep(0.1)
        
        # Test system event
        logger.log_system_event(
            event_type='evaluation',
            event_name='evaluation_started',
            event_data={'dataset': 'test.json'}
        )
        
        # Export for Elasticsearch
        export_file = logger.export_for_elasticsearch("test_export_logs.ndjson")
        print(f"✅ Exported logs to: {export_file}")
        
        # Get session summary
        summary = logger.get_session_summary()
        print(f"\n📊 Session Summary:")
        print(f"   Total logs: {summary['log_statistics']['total_logs']}")
        print(f"   API calls: {summary['api_statistics']['total_api_calls']}")
        
        print("\n✅ All logging tests passed!")
        
    finally:
        # Cleanup
        Path("test_logs.db").unlink(missing_ok=True)
        Path("test_export_logs.ndjson").unlink(missing_ok=True)


if __name__ == "__main__":
    test_logging_system()