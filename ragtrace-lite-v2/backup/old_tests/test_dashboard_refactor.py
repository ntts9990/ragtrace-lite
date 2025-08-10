#!/usr/bin/env python
"""Test dashboard service layer refactoring"""

import sys
sys.path.insert(0, 'src')

import logging
import requests
import json
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dashboard_service():
    """Test the new dashboard service layer"""
    print("🧪 Testing Dashboard Service Layer Refactoring")
    print("="*60)
    
    try:
        from ragtrace_lite.dashboard.services import DashboardService
        
        # Test service initialization
        service = DashboardService()
        print(f"✅ DashboardService initialized successfully")
        
        # Test get_all_reports
        reports = service.get_all_reports()
        print(f"✅ Retrieved {len(reports)} reports")
        
        if reports:
            sample_report = reports[0]
            print(f"✅ Sample report structure: {list(sample_report.keys())}")
            
            # Test get_question_details for first report
            run_id = sample_report['run_id']
            questions = service.get_question_details(run_id)
            print(f"✅ Retrieved {len(questions)} questions for run_id: {run_id}")
            
            if questions:
                sample_question = questions[0]
                print(f"✅ Sample question structure: {list(sample_question.keys())}")
            
        # Test time series stats
        time_series = service.get_time_series_stats()
        print(f"✅ Time series stats retrieved")
        print(f"   - Data points: {len(time_series.get('dates', []))}")
        print(f"   - Total evaluations: {time_series.get('summary', {}).get('total_evaluations', 0)}")
        
        # Test A/B testing (with synthetic data)
        if len(reports) >= 2:
            run_ids = [r['run_id'] for r in reports[:2]]
            ab_results = service.perform_ab_test([run_ids[0]], [run_ids[1]])
            
            if 'error' not in ab_results:
                print(f"✅ A/B test completed successfully")
                print(f"   - Metrics tested: {list(ab_results.keys())}")
            else:
                print(f"⚠️ A/B test returned error: {ab_results['error']}")
        else:
            print(f"⚠️ Not enough reports for A/B testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """Test API integration with new service layer"""
    print(f"\n🔗 Testing API Integration")
    print("="*60)
    
    # Note: This would require the Flask app to be running
    # For now, we'll just verify the imports work
    
    try:
        from ragtrace_lite.dashboard.app import app, dashboard_service
        
        print(f"✅ Flask app imported successfully")
        print(f"✅ Dashboard service instance available")
        
        # Test that service methods are callable
        methods_to_test = [
            'get_all_reports',
            'get_time_series_stats', 
            'perform_ab_test',
            'get_question_details'
        ]
        
        for method_name in methods_to_test:
            if hasattr(dashboard_service, method_name):
                print(f"✅ Service method '{method_name}' available")
            else:
                print(f"❌ Service method '{method_name}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_database_manager_usage():
    """Test that service layer uses DatabaseManager correctly"""
    print(f"\n🗄️ Testing DatabaseManager Usage")
    print("="*60)
    
    try:
        from ragtrace_lite.dashboard.services import DashboardService
        from ragtrace_lite.db.manager import DatabaseManager
        
        # Create service
        service = DashboardService()
        
        # Verify service has DatabaseManager instance
        if hasattr(service, 'db_manager') and isinstance(service.db_manager, DatabaseManager):
            print(f"✅ Service uses DatabaseManager instance")
            print(f"   - DB path: {service.db_manager.db_path}")
        else:
            print(f"❌ Service does not use DatabaseManager properly")
            return False
        
        # Test that service can get database connection
        try:
            with service.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM evaluations")
                count = cursor.fetchone()[0]
                print(f"✅ Database connection works, {count} evaluations found")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseManager usage test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that dashboard still works with existing data"""
    print(f"\n⏮️ Testing Backward Compatibility")
    print("="*60)
    
    try:
        from ragtrace_lite.dashboard.services import DashboardService
        
        service = DashboardService()
        
        # Test with existing data
        reports = service.get_all_reports()
        
        # Verify report structure matches expected format
        if reports:
            report = reports[0]
            expected_fields = [
                'run_id', 'dataset_name', 'timestamp', 'ragas_score',
                'dataset_items', 'status', 'faithfulness', 'answer_relevancy',
                'context_precision', 'context_recall', 'answer_correctness'
            ]
            
            missing_fields = [field for field in expected_fields if field not in report]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            else:
                print(f"✅ All required fields present in report")
        
        # Test question details format
        if reports:
            questions = service.get_question_details(reports[0]['run_id'])
            
            if questions:
                question = questions[0]
                expected_question_fields = ['index', 'question', 'answer', 'scores', 'analysis']
                
                missing_q_fields = [field for field in expected_question_fields if field not in question]
                
                if missing_q_fields:
                    print(f"❌ Missing required question fields: {missing_q_fields}")
                    return False
                else:
                    print(f"✅ All required question fields present")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all dashboard refactoring tests"""
    print("🚀 Dashboard Service Layer Refactoring Tests")
    print("="*80)
    
    test_results = []
    
    test_results.append(("Dashboard Service Layer", test_dashboard_service()))
    test_results.append(("API Integration", test_api_integration()))
    test_results.append(("DatabaseManager Usage", test_database_manager_usage()))
    test_results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 DASHBOARD REFACTORING TEST RESULTS")
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
        print(f"\n🎉 ALL DASHBOARD TESTS PASSED! Service layer successfully refactored!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review before proceeding.")
        return False

if __name__ == "__main__":
    main()