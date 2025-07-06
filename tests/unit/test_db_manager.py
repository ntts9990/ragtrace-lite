"""
Unit tests for db_manager module
"""

import pytest
import sqlite3
from pathlib import Path
import pandas as pd

from ragtrace_lite.db_manager import DatabaseManager
from ragtrace_lite.config_loader import Config, DatabaseConfig


class TestDatabaseManager:
    """Test database management functionality"""
    
    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create DatabaseManager instance with temporary database"""
        config = Config(
            database=DatabaseConfig(path=temp_db_path)
        )
        return DatabaseManager(config)
    
    @pytest.fixture
    def in_memory_db_manager(self):
        """Create DatabaseManager with in-memory database"""
        config = Config(
            database=DatabaseConfig(path=":memory:")
        )
        return DatabaseManager(config)
    
    def test_create_tables(self, db_manager):
        """Test database table creation"""
        # Tables should be created on initialization
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='evaluation_runs'
        """)
        assert cursor.fetchone() is not None
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='evaluation_results'
        """)
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_create_evaluation_run(self, in_memory_db_manager):
        """Test creating evaluation run"""
        run_id = "test_run_123"
        
        in_memory_db_manager.create_evaluation_run(
            run_id=run_id,
            llm_provider="hcx",
            llm_model="HCX-005",
            dataset_name="test_data.json",
            total_items=10,
            metrics=["faithfulness", "answer_relevancy"],
            config_data={"test": "config"}
        )
        
        # Verify the run was created
        conn = sqlite3.connect(in_memory_db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?",
            (run_id,)
        )
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == run_id  # run_id
        assert row[2] == "hcx"   # llm_provider
        assert row[3] == "HCX-005"  # llm_model
        assert row[4] == "test_data.json"  # dataset_name
        assert row[5] == 10  # total_items
        
        conn.close()
    
    def test_save_evaluation_results(self, in_memory_db_manager):
        """Test saving evaluation results"""
        run_id = "test_run_123"
        
        # Create run first
        in_memory_db_manager.create_evaluation_run(
            run_id=run_id,
            llm_provider="gemini",
            llm_model="gemini-2.5-flash",
            dataset_name="test.json",
            total_items=2,
            metrics=["faithfulness"],
            config_data={}
        )
        
        # Create sample results
        results_df = pd.DataFrame([
            {
                'faithfulness': 0.8,
                'answer_relevancy': 0.9,
                'context_precision': 0.85,
                'context_recall': 0.95,
                'answer_correctness': 0.87
            },
            {
                'faithfulness': 0.7,
                'answer_relevancy': 0.85,
                'context_precision': 0.9,
                'context_recall': 0.88,
                'answer_correctness': 0.82
            }
        ])
        
        dataset = [
            {
                'question': 'Test question 1',
                'answer': 'Test answer 1',
                'contexts': ['Context 1'],
                'ground_truth': 'Truth 1'
            },
            {
                'question': 'Test question 2',
                'answer': 'Test answer 2',
                'contexts': ['Context 2'],
                'ground_truth': 'Truth 2'
            }
        ]
        
        # Save results
        in_memory_db_manager.save_evaluation_results(
            run_id=run_id,
            results_df=results_df,
            dataset=dataset
        )
        
        # Verify results were saved
        conn = sqlite3.connect(in_memory_db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM evaluation_results WHERE run_id = ?",
            (run_id,)
        )
        count = cursor.fetchone()[0]
        
        assert count == 2
        
        conn.close()
    
    def test_complete_evaluation_run(self, in_memory_db_manager):
        """Test completing evaluation run"""
        run_id = "test_run_123"
        
        # Create run
        in_memory_db_manager.create_evaluation_run(
            run_id=run_id,
            llm_provider="hcx",
            llm_model="HCX-005",
            dataset_name="test.json",
            total_items=1,
            metrics=["faithfulness"],
            config_data={}
        )
        
        # Complete the run
        in_memory_db_manager.complete_evaluation_run(run_id)
        
        # Verify status
        conn = sqlite3.connect(in_memory_db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM evaluation_runs WHERE run_id = ?",
            (run_id,)
        )
        status = cursor.fetchone()[0]
        
        assert status == "completed"
        
        conn.close()
    
    def test_list_evaluations(self, in_memory_db_manager):
        """Test listing evaluations"""
        # Create multiple runs
        for i in range(3):
            run_id = f"test_run_{i}"
            in_memory_db_manager.create_evaluation_run(
                run_id=run_id,
                llm_provider="hcx",
                llm_model="HCX-005",
                dataset_name=f"test_{i}.json",
                total_items=10,
                metrics=["faithfulness"],
                config_data={}
            )
            if i < 2:  # Complete first two
                in_memory_db_manager.complete_evaluation_run(run_id)
        
        # List evaluations
        evaluations = in_memory_db_manager.list_evaluations(limit=5)
        
        assert len(evaluations) == 3
        assert evaluations[0]['status'] == 'running'  # Most recent
        assert evaluations[1]['status'] == 'completed'
        assert evaluations[2]['status'] == 'completed'
    
    def test_get_evaluation_summary(self, in_memory_db_manager):
        """Test getting evaluation summary"""
        run_id = "test_run_summary"
        
        # Create and populate run
        in_memory_db_manager.create_evaluation_run(
            run_id=run_id,
            llm_provider="gemini",
            llm_model="gemini-2.5-flash",
            dataset_name="test.json",
            total_items=2,
            metrics=["faithfulness", "answer_relevancy"],
            config_data={}
        )
        
        # Add results
        results_df = pd.DataFrame([
            {'faithfulness': 0.8, 'answer_relevancy': 0.9},
            {'faithfulness': 0.7, 'answer_relevancy': 0.85}
        ])
        
        dataset = [
            {'question': 'Q1', 'answer': 'A1', 'contexts': ['C1'], 'ground_truth': 'GT1'},
            {'question': 'Q2', 'answer': 'A2', 'contexts': ['C2'], 'ground_truth': 'GT2'}
        ]
        
        in_memory_db_manager.save_evaluation_results(run_id, results_df, dataset)
        in_memory_db_manager.complete_evaluation_run(run_id)
        
        # Get summary
        summary = in_memory_db_manager.get_evaluation_summary(run_id)
        
        assert 'run_info' in summary
        assert 'metric_statistics' in summary
        assert 'ragas_score' in summary
        
        assert summary['run_info']['run_id'] == run_id
        assert summary['run_info']['llm_provider'] == 'gemini'
        assert summary['metric_statistics']['faithfulness']['average'] == 0.75
        assert summary['metric_statistics']['answer_relevancy']['average'] == 0.875
    
    def test_close_connection(self, db_manager):
        """Test closing database connection"""
        # Should not raise any exceptions
        db_manager.close()
        
        # Verify connection is closed by trying to use it
        with pytest.raises(Exception):
            db_manager.create_evaluation_run(
                run_id="test",
                llm_provider="hcx",
                llm_model="HCX-005",
                dataset_name="test.json",
                total_items=1,
                metrics=[],
                config_data={}
            )