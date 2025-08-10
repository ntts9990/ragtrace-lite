#!/usr/bin/env python
"""Test schema migration and denormalized columns"""

import sys
sys.path.insert(0, 'src')

from ragtrace_lite.db.manager import DatabaseManager
from pathlib import Path

def test_schema_migration():
    """Test that the schema migration works correctly"""
    
    print("🧪 Testing Schema Migration and Denormalized Columns")
    print("="*60)
    
    # Use the same DB path as dashboard
    db_path = Path(__file__).parent.parent / "data" / "ragtrace.db"
    
    # Initialize DatabaseManager (this will trigger migration)
    db_manager = DatabaseManager(str(db_path))
    
    # Test saving evaluation with denormalized columns
    test_metrics = {
        'faithfulness': 0.85,
        'answer_relevancy': 0.92, 
        'context_precision': 0.78,
        'context_recall': 0.88,
        'answer_correctness': 0.81
    }
    
    test_details = [
        {
            'question': 'Test question?',
            'answer': 'Test answer',
            'contexts': ['Test context'],
            'ground_truth': 'Test ground truth',
            'faithfulness': 0.85,
            'answer_relevancy': 0.92,
            'context_precision': 0.78,
            'context_recall': 0.88,
            'answer_correctness': 0.81
        }
    ]
    
    run_id = "test_schema_migration_001"
    
    success = db_manager.save_evaluation(
        run_id=run_id,
        dataset_name="schema_test",
        dataset_hash="test_hash",
        dataset_items=1,
        environment={'test': 'migration'},
        metrics=test_metrics,
        details=test_details
    )
    
    if success:
        print(f"✅ Successfully saved evaluation with run_id: {run_id}")
        
        # Verify the denormalized columns were saved
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT run_id, faithfulness, answer_relevancy, context_precision,
                   context_recall, answer_correctness, ragas_score
            FROM evaluations WHERE run_id = ?
        """, (run_id,))
        
        row = cursor.fetchone()
        if row:
            print(f"✅ Denormalized columns verified:")
            print(f"   - run_id: {row[0]}")
            print(f"   - faithfulness: {row[1]}")
            print(f"   - answer_relevancy: {row[2]}")
            print(f"   - context_precision: {row[3]}")
            print(f"   - context_recall: {row[4]}")
            print(f"   - answer_correctness: {row[5]}")
            print(f"   - ragas_score: {row[6]}")
        else:
            print("❌ Failed to retrieve saved evaluation")
        
        conn.close()
    else:
        print("❌ Failed to save evaluation")
    
    print("\n🎉 Schema migration test completed!")

if __name__ == "__main__":
    test_schema_migration()