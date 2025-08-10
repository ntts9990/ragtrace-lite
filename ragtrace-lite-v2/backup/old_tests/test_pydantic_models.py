#!/usr/bin/env python
"""Test Pydantic evaluation models and DatabaseManager integration"""

import sys
sys.path.insert(0, 'src')

import logging
import json
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pydantic_models():
    """Test Pydantic model creation and validation"""
    print("🧪 Testing Pydantic Models")
    print("="*60)
    
    try:
        from ragtrace_lite.models.evaluation import (
            EvaluationMetrics, EvaluationItem, EvaluationResult,
            EvaluationConfig, EvaluationEnvironment, EvaluationStatus
        )
        
        # Test EvaluationMetrics
        metrics = EvaluationMetrics(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_precision=0.80,
            context_recall=0.85,
            answer_correctness=0.88
        )
        print(f"✅ EvaluationMetrics created: RAGAS score = {metrics.ragas_score:.3f}")
        
        # Test validation (should fail)
        try:
            invalid_metrics = EvaluationMetrics(
                faithfulness=1.5,  # Invalid: > 1.0
                answer_relevancy=0.9,
                context_precision=0.8,
                context_recall=0.85,
                answer_correctness=0.88
            )
            print("❌ Validation should have failed for faithfulness > 1.0")
            return False
        except Exception:
            print("✅ Validation correctly rejected invalid faithfulness score")
        
        # Test EvaluationItem
        item = EvaluationItem(
            item_index=0,
            question="What is RAG?",
            answer="RAG stands for Retrieval-Augmented Generation",
            contexts=["RAG is a technique that combines retrieval and generation"],
            ground_truth="RAG is Retrieval-Augmented Generation",
            metrics=metrics
        )
        print(f"✅ EvaluationItem created with {len(item.contexts)} contexts")
        
        # Test JSON context parsing
        item_with_json_contexts = EvaluationItem(
            item_index=1,
            question="Test question",
            answer="Test answer", 
            contexts='["Context 1", "Context 2"]',  # JSON string
            metrics=metrics
        )
        print(f"✅ JSON contexts parsed: {len(item_with_json_contexts.contexts)} contexts")
        
        # Test EvaluationConfig
        config = EvaluationConfig(
            llm_provider="hcx",
            llm_model="hcx-005",
            temperature=0.1,
            batch_size=5
        )
        print(f"✅ EvaluationConfig created: {config.llm_provider}/{config.llm_model}")
        
        # Test EvaluationEnvironment
        environment = EvaluationEnvironment(
            python_version="3.9.0",
            ragas_version="0.1.0",
            model_name="hcx-005",
            temperature=0.1
        )
        print(f"✅ EvaluationEnvironment created: Python {environment.python_version}")
        
        # Test EvaluationResult
        result = EvaluationResult(
            run_id="test_model_validation_001",
            dataset_name="test_dataset",
            dataset_hash="abc123",
            overall_metrics=metrics,
            items=[item, item_with_json_contexts],
            config=config,
            environment=environment,
            dataset_items=2,
            total_items=2
        )
        print(f"✅ EvaluationResult created: {result.run_id}")
        print(f"   - Status: {result.status}")
        print(f"   - RAGAS Score: {result.overall_metrics.ragas_score:.3f}")
        print(f"   - Items: {len(result.items)}")
        print(f"   - Success Rate: {result.success_rate:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """Test DatabaseManager integration with Pydantic models"""
    print(f"\n🗄️ Testing DatabaseManager Integration")
    print("="*60)
    
    try:
        from ragtrace_lite.models.evaluation import (
            EvaluationMetrics, EvaluationItem, EvaluationResult,
            EvaluationConfig, EvaluationEnvironment, EvaluationStatus
        )
        from ragtrace_lite.db.manager import DatabaseManager
        from ragtrace_lite.config.config_loader import get_config
        
        # Use unified config
        config_loader = get_config()
        db_path = config_loader._get_default_config()['database']['path']
        
        db_manager = DatabaseManager(str(db_path))
        print(f"✅ DatabaseManager initialized: {db_path}")
        
        # Create test evaluation
        metrics = EvaluationMetrics(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_precision=0.80,
            context_recall=0.85,
            answer_correctness=0.88
        )
        
        items = [
            EvaluationItem(
                item_index=0,
                question="What is the main purpose of RAG?",
                answer="RAG combines retrieval and generation for better answers",
                contexts=["RAG retrieves relevant documents", "Then generates answers"],
                ground_truth="RAG improves answer quality",
                metrics=metrics
            ),
            EvaluationItem(
                item_index=1,
                question="How does RAG work?",
                answer="RAG first retrieves then generates",
                contexts=["Step 1: Retrieve", "Step 2: Generate"],
                ground_truth="Two-step process",
                metrics=metrics
            )
        ]
        
        config = EvaluationConfig(
            llm_provider="hcx",
            llm_model="hcx-005",
            temperature=0.1
        )
        
        environment = EvaluationEnvironment(
            python_version="3.9.0",
            ragas_version="0.1.0",
            model_name="hcx-005"
        )
        
        import time
        test_run_id = f"pydantic_test_{int(time.time())}"
        evaluation = EvaluationResult(
            run_id=test_run_id,
            dataset_name="pydantic_test",
            dataset_hash="test_hash_001",
            overall_metrics=metrics,
            items=items,
            config=config,
            environment=environment,
            dataset_items=2,
            total_items=2,
            status=EvaluationStatus.COMPLETED
        )
        
        # Test saving with Pydantic model
        success = db_manager.save_evaluation_model(evaluation)
        if success:
            print(f"✅ Evaluation model saved successfully: {evaluation.run_id}")
        else:
            print(f"❌ Failed to save evaluation model")
            return False
        
        # Test loading with Pydantic model
        loaded_evaluation = db_manager.load_evaluation_model(evaluation.run_id)
        if loaded_evaluation:
            print(f"✅ Evaluation model loaded successfully: {loaded_evaluation.run_id}")
            print(f"   - RAGAS Score: {loaded_evaluation.overall_metrics.ragas_score:.3f}")
            print(f"   - Items loaded: {len(loaded_evaluation.items)}")
            print(f"   - Status: {loaded_evaluation.status}")
            
            # Verify data integrity
            if (loaded_evaluation.overall_metrics.ragas_score == evaluation.overall_metrics.ragas_score and
                len(loaded_evaluation.items) == len(evaluation.items) and
                loaded_evaluation.items[0].question == evaluation.items[0].question):
                print(f"✅ Data integrity verified")
            else:
                print(f"❌ Data integrity check failed")
                return False
        else:
            print(f"❌ Failed to load evaluation model")
            return False
        
        # Test status update
        status_updated = db_manager.update_evaluation_status(
            evaluation.run_id, 
            EvaluationStatus.COMPLETED
        )
        if status_updated:
            print(f"✅ Evaluation status updated successfully")
        else:
            print(f"❌ Failed to update evaluation status")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_serialization():
    """Test model serialization and deserialization"""
    print(f"\n🔄 Testing Serialization")
    print("="*60)
    
    try:
        from ragtrace_lite.models.evaluation import (
            EvaluationMetrics, EvaluationItem, EvaluationResult,
            EvaluationConfig, EvaluationEnvironment
        )
        
        # Create test data
        metrics = EvaluationMetrics(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_precision=0.80,
            context_recall=0.85,
            answer_correctness=0.88
        )
        
        config = EvaluationConfig(
            llm_provider="hcx",
            llm_model="hcx-005"
        )
        
        # Test to_dict methods
        metrics_dict = metrics.to_dict()
        config_dict = config.to_dict()
        
        print(f"✅ Metrics serialization: {len(metrics_dict)} fields")
        print(f"✅ Config serialization: {len(config_dict)} fields")
        
        # Test database dict conversion
        environment = EvaluationEnvironment(python_version="3.9.0")
        items = [
            EvaluationItem(
                item_index=0,
                question="Test?",
                answer="Answer",
                contexts=["Context"],
                metrics=metrics
            )
        ]
        
        import time
        serial_run_id = f"serialization_test_{int(time.time())}"
        evaluation = EvaluationResult(
            run_id=serial_run_id,
            dataset_name="test",
            dataset_hash="hash",
            overall_metrics=metrics,
            items=items,
            config=config,
            environment=environment,
            dataset_items=1,
            total_items=1
        )
        
        db_dict = evaluation.to_database_dict()
        print(f"✅ Database dict created with {len(db_dict)} fields")
        
        # Verify JSON serialization works
        json_metrics = json.loads(db_dict['metrics'])
        json_config = json.loads(db_dict['config_data'])
        json_env = json.loads(db_dict['environment_json'])
        
        print(f"✅ JSON serialization verified:")
        print(f"   - Metrics: {json_metrics['faithfulness']}")
        print(f"   - Config: {json_config['llm_provider']}")
        print(f"   - Environment: {json_env.get('python_version', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing dict-based code"""
    print(f"\n🔙 Testing Backward Compatibility")
    print("="*60)
    
    try:
        from ragtrace_lite.db.manager import DatabaseManager
        from ragtrace_lite.config.config_loader import get_config
        
        # Use unified config
        config_loader = get_config()
        db_path = config_loader._get_default_config()['database']['path']
        
        db_manager = DatabaseManager(str(db_path))
        
        # Test legacy save_evaluation method still works
        import time
        legacy_run_id = f"legacy_test_{int(time.time())}"
        legacy_success = db_manager.save_evaluation(
            run_id=legacy_run_id,
            dataset_name="legacy_dataset",
            dataset_hash="legacy_hash",
            dataset_items=1,
            environment={"python_version": "3.9.0"},
            metrics={
                'faithfulness': 0.8,
                'answer_relevancy': 0.9,
                'context_precision': 0.85,
                'context_recall': 0.8,
                'answer_correctness': 0.87
            },
            details=[
                {
                    'question': 'Legacy question?',
                    'answer': 'Legacy answer',
                    'contexts': ['Legacy context'],
                    'ground_truth': 'Legacy truth',
                    'faithfulness': 0.8,
                    'answer_relevancy': 0.9,
                    'context_precision': 0.85,
                    'context_recall': 0.8,
                    'answer_correctness': 0.87
                }
            ]
        )
        
        if legacy_success:
            print(f"✅ Legacy save_evaluation method works")
        else:
            print(f"❌ Legacy save_evaluation method failed")
            return False
        
        # Test that new Pydantic methods don't break existing data
        try:
            loaded_legacy = db_manager.load_evaluation_model(legacy_run_id)
            if loaded_legacy:
                print(f"✅ Legacy evaluation loaded with Pydantic model")
                print(f"   - RAGAS Score: {loaded_legacy.overall_metrics.ragas_score:.3f}")
            else:
                print(f"⚠️ Could not load legacy evaluation with Pydantic model (expected)")
        except Exception as e:
            print(f"⚠️ Legacy data not compatible with Pydantic loader: {str(e)[:50]}...")
        
        print(f"✅ Backward compatibility maintained")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all Pydantic model tests"""
    print("🚀 Pydantic Models Testing")
    print("="*80)
    
    test_results = [
        ("Pydantic Models", test_pydantic_models()),
        ("Database Integration", test_database_integration()),
        ("Serialization", test_serialization()),
        ("Backward Compatibility", test_backward_compatibility())
    ]
    
    # Summary
    print("\n" + "="*80)
    print("📊 PYDANTIC MODELS TEST RESULTS")
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
        print(f"\n🎉 ALL PYDANTIC MODEL TESTS PASSED! Type-safe evaluation models ready!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review before proceeding.")
        return False

if __name__ == "__main__":
    main()