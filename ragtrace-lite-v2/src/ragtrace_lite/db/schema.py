"""Database schema definitions"""

SCHEMA_VERSION = 2

# SQL statements for table creation
SCHEMAS = {
    "evaluations": """
        CREATE TABLE IF NOT EXISTS evaluations (
            run_id TEXT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            llm TEXT,
            dataset_name TEXT,
            dataset_hash TEXT,
            dataset_items INTEGER,
            total_items INTEGER,
            metrics TEXT,
            config_data TEXT,
            environment_json TEXT,
            ragas_score REAL,
            status TEXT DEFAULT 'running',
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
    
    "evaluation_env": """
        CREATE TABLE IF NOT EXISTS evaluation_env (
            run_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (run_id, key),
            FOREIGN KEY (run_id) REFERENCES evaluations (run_id) ON DELETE CASCADE
        )
    """,
    
    "evaluation_metric_summary": """
        CREATE TABLE IF NOT EXISTS evaluation_metric_summary (
            run_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            avg_score REAL,
            min_score REAL,
            max_score REAL,
            std_score REAL,
            count INTEGER,
            PRIMARY KEY (run_id, metric_name),
            FOREIGN KEY (run_id) REFERENCES evaluations (run_id) ON DELETE CASCADE
        )
    """,
    
    "evaluation_items": """
        CREATE TABLE IF NOT EXISTS evaluation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
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
            FOREIGN KEY (run_id) REFERENCES evaluations (run_id) ON DELETE CASCADE
        )
    """,
    
    "schema_version": """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
}

# Index definitions
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_eval_timestamp ON evaluations (timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_eval_dataset ON evaluations (dataset_hash)",
    "CREATE INDEX IF NOT EXISTS idx_eval_status ON evaluations (status)",
    "CREATE INDEX IF NOT EXISTS idx_env_key ON evaluation_env (key)",
    "CREATE INDEX IF NOT EXISTS idx_env_key_value ON evaluation_env (key, value)",
    "CREATE INDEX IF NOT EXISTS idx_metric_name ON evaluation_metric_summary (metric_name)",
    "CREATE INDEX IF NOT EXISTS idx_items_run ON evaluation_items (run_id)",
]