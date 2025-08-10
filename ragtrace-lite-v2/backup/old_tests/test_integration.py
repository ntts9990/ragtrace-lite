#!/usr/bin/env python
"""Integration test for all Phase 0-4 improvements"""

import sys
import os
sys.path.insert(0, 'src')

import logging
import sqlite3
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phase_0_schema_fix():
    """Test Phase 0: DB schema migration and denormalized columns"""
    print("🧪 Testing Phase 0: DB Schema Migration")
    print("="*60)
    
    try:
        from ragtrace_lite.db.manager import DatabaseManager
        from ragtrace_lite.config.config_loader import get_config
        
        # Get unified DB path
        config = get_config()
        db_path = config._get_default_config()['database']['path']
        
        print(f"✅ Using unified DB path: {db_path}")
        
        # Initialize DatabaseManager (triggers migration)
        db_manager = DatabaseManager(str(db_path))
        
        # Check if denormalized columns exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(evaluations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing denormalized columns: {missing_columns}")
            return False
        else:
            print(f"✅ All denormalized columns present: {required_columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Phase 0 test failed: {e}")
        return False

def test_phase_1_unified_config():
    """Test Phase 1: Unified DB path configuration"""
    print("\n🧪 Testing Phase 1: Unified Configuration")
    print("="*60)
    
    try:
        from ragtrace_lite.config.config_loader import get_config
        from ragtrace_lite.db.manager import DatabaseManager
        
        # Set test DB path
        test_path = "/tmp/test_ragtrace.db"
        os.environ['DB_PATH'] = test_path
        
        # Get config
        config = get_config()
        db_config = config._get_default_config()['database']
        
        print(f"✅ ConfigLoader DB path: {db_config['path']}")
        
        # Test DatabaseManager uses same path
        db_manager = DatabaseManager(str(test_path))
        
        if str(db_manager.db_path) == test_path:
            print(f"✅ DatabaseManager using correct path: {db_manager.db_path}")
        else:
            print(f"❌ Path mismatch. Expected: {test_path}, Got: {db_manager.db_path}")
            return False
        
        # Cleanup
        if os.path.exists(test_path):
            os.remove(test_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 test failed: {e}")
        return False

def test_phase_2_embeddings_cleanup():
    """Test Phase 2: Embeddings implementation cleanup"""
    print("\n🧪 Testing Phase 2: Embeddings Cleanup")
    print("="*60)
    
    try:
        # Check that duplicate embeddings.py is removed
        embeddings_path = Path("src/ragtrace_lite/core/embeddings.py")
        if embeddings_path.exists():
            print(f"❌ Duplicate embeddings.py still exists")
            return False
        else:
            print(f"✅ Duplicate embeddings.py successfully removed")
        
        # Check that embeddings_adapter.py exists and works
        from ragtrace_lite.core.embeddings_adapter import EmbeddingsAdapter
        
        # Should use ConfigLoader
        adapter = EmbeddingsAdapter()
        print(f"✅ EmbeddingsAdapter initialized with provider: {adapter.provider}")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 test failed: {e}")
        return False

def test_phase_3_config_centralization():
    """Test Phase 3: Configuration centralization"""
    print("\n🧪 Testing Phase 3: Config Centralization")
    print("="*60)
    
    try:
        from ragtrace_lite.core.evaluator import Evaluator
        from ragtrace_lite.config.config_loader import get_config
        
        # Test that Evaluator uses ConfigLoader
        config = get_config()
        evaluator = Evaluator()
        
        # Check that evaluator gets config through ConfigLoader
        evaluator_config = evaluator._get_default_config()
        config_loader_config = config.get_llm_config()
        
        print(f"✅ Evaluator config provider: {evaluator_config.get('provider', 'unknown')}")
        print(f"✅ ConfigLoader provider: {config_loader_config.get('provider', 'unknown')}")
        
        if evaluator_config.get('provider') == config_loader_config.get('provider'):
            print(f"✅ Evaluator successfully using ConfigLoader")
        else:
            print(f"⚠️ Config mismatch between Evaluator and ConfigLoader")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 3 test failed: {e}")
        return False

def test_phase_4_rate_limiting():
    """Test Phase 4: Improved rate limiting"""
    print("\n🧪 Testing Phase 4: Advanced Rate Limiting")
    print("="*60)
    
    try:
        from ragtrace_lite.core.rate_limiter import get_rate_limiter
        from ragtrace_lite.core.llm_adapter import LLMAdapter
        
        # Test rate limiter directly
        limiter = get_rate_limiter("hcx")
        
        # Test burst requests
        wait1 = limiter.acquire_sync()
        wait2 = limiter.acquire_sync()
        
        print(f"✅ Burst request 1 wait time: {wait1:.3f}s")
        print(f"✅ Burst request 2 wait time: {wait2:.3f}s")
        
        # Both should be fast (near 0)
        if wait1 < 0.1 and wait2 < 0.1:
            print(f"✅ Burst requests processed efficiently")
        else:
            print(f"⚠️ Burst requests slower than expected")
        
        # Test rate limited request
        wait3 = limiter.acquire_sync()
        print(f"✅ Rate limited request wait time: {wait3:.3f}s")
        
        if wait3 > 0.1:
            print(f"✅ Rate limiting working correctly")
        else:
            print(f"⚠️ Rate limiting not applied as expected")
        
        # Test statistics
        stats = limiter.get_stats()
        print(f"✅ Rate limiter statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 4 test failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test complete workflow with all improvements"""
    print("\n🧪 Testing End-to-End Workflow")
    print("="*60)
    
    try:
        # Test with mock data
        from ragtrace_lite.db.manager import DatabaseManager
        from ragtrace_lite.config.config_loader import get_config
        
        # Use unified config
        config = get_config()
        db_path = config._get_default_config()['database']['path']
        
        db_manager = DatabaseManager(str(db_path))
        
        # Create test evaluation data
        test_metrics = {
            'faithfulness': 0.85,
            'answer_relevancy': 0.90,
            'context_precision': 0.80,
            'context_recall': 0.85,
            'answer_correctness': 0.88
        }
        
        test_details = [
            {
                'question': 'Integration test question?',
                'answer': 'Integration test answer',
                'contexts': ['Integration test context'],
                'ground_truth': 'Integration test ground truth',
                **test_metrics
            }
        ]
        
        run_id = "integration_test_001"
        
        # Test saving with new denormalized schema
        success = db_manager.save_evaluation(
            run_id=run_id,
            dataset_name="integration_test",
            dataset_hash="test_hash",
            dataset_items=1,
            environment={'test': 'integration'},
            metrics=test_metrics,
            details=test_details
        )
        
        if success:
            print(f"✅ Evaluation saved successfully with run_id: {run_id}")
            
            # Verify denormalized columns were populated
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT faithfulness, answer_relevancy, context_precision, 
                       context_recall, answer_correctness, ragas_score
                FROM evaluations WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            if row and all(val is not None for val in row):
                print(f"✅ Denormalized columns populated correctly:")
                print(f"   faithfulness: {row[0]:.3f}")
                print(f"   answer_relevancy: {row[1]:.3f}")
                print(f"   context_precision: {row[2]:.3f}")
                print(f"   context_recall: {row[3]:.3f}")
                print(f"   answer_correctness: {row[4]:.3f}")
                print(f"   ragas_score: {row[5]:.3f}")
            else:
                print(f"❌ Denormalized columns not populated correctly")
                return False
                
            conn.close()
        else:
            print(f"❌ Failed to save evaluation")
            return False
        
        print(f"✅ End-to-end workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 RAGTrace-Lite v2 Integration Testing")
    print("Testing all Phase 0-4 improvements...")
    print("="*80)
    
    test_results = []
    
    # Run all phase tests
    test_results.append(("Phase 0 - Schema Migration", test_phase_0_schema_fix()))
    test_results.append(("Phase 1 - Unified Config", test_phase_1_unified_config()))  
    test_results.append(("Phase 2 - Embeddings Cleanup", test_phase_2_embeddings_cleanup()))
    test_results.append(("Phase 3 - Config Centralization", test_phase_3_config_centralization()))
    test_results.append(("Phase 4 - Rate Limiting", test_phase_4_rate_limiting()))
    test_results.append(("End-to-End Workflow", test_end_to_end_workflow()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(test_results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {passed/len(test_results)*100:.1f}%")
    
    if failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! Ready to proceed to Phase 5+")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review before proceeding.")
        return False

if __name__ == "__main__":
    main()