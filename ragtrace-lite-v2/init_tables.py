#!/usr/bin/env python
"""Initialize database tables"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ragtrace.db"

def init_tables():
    """Create all necessary database tables"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create evaluations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            dataset_name TEXT,
            dataset_items INTEGER,
            faithfulness REAL,
            answer_relevancy REAL,
            context_precision REAL,
            context_recall REAL,
            answer_correctness REAL,
            ragas_score REAL,
            status TEXT DEFAULT 'running'
        )
    """)
    
    # Create evaluation_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_items (
            run_id TEXT,
            item_index INTEGER,
            question TEXT,
            answer TEXT,
            contexts TEXT,
            ground_truth TEXT,
            faithfulness REAL,
            answer_relevancy REAL,
            context_precision REAL,
            context_recall REAL,
            answer_correctness REAL,
            PRIMARY KEY (run_id, item_index),
            FOREIGN KEY (run_id) REFERENCES evaluations (run_id)
        )
    """)
    
    # Create evaluation_env table  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_env (
            run_id TEXT,
            key TEXT,
            value TEXT,
            PRIMARY KEY (run_id, key),
            FOREIGN KEY (run_id) REFERENCES evaluations (run_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database tables initialized")

if __name__ == "__main__":
    init_tables()