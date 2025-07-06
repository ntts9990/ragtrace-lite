"""
End-to-end integration tests for RAGTrace Lite
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from ragtrace_lite import RAGTraceLite
from ragtrace_lite.config_loader import load_config


class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for testing"""
        def mock_invoke(*args, **kwargs):
            mock_response = Mock()
            mock_response.content = "Test LLM response"
            return mock_response
        return mock_invoke
    
    @pytest.fixture
    def mock_ragas_evaluate(self):
        """Mock RAGAS evaluation"""
        import pandas as pd
        
        def mock_evaluate(*args, **kwargs):
            # Return mock evaluation results
            return pd.DataFrame([
                {
                    'faithfulness': 0.85,
                    'answer_relevancy': 0.90,
                    'context_precision': 0.88,
                    'context_recall': 0.92,
                    'answer_correctness': 0.87
                },
                {
                    'faithfulness': 0.80,
                    'answer_relevancy': 0.85,
                    'context_precision': 0.83,
                    'context_recall': 0.88,
                    'answer_correctness': 0.82
                }
            ])
        return mock_evaluate
    
    @patch('ragtrace_lite.llm_factory.create_llm')
    @patch('ragtrace_lite.llm_factory.test_llm_connection')
    @patch('ragtrace_lite.evaluator.evaluate')
    def test_complete_evaluation_flow(
        self,
        mock_evaluate,
        mock_test_connection,
        mock_create_llm,
        temp_config_file,
        temp_data_file,
        tmp_path,
        mock_llm_response,
        mock_ragas_evaluate
    ):
        """Test complete evaluation flow from start to finish"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm.invoke = mock_llm_response
        mock_create_llm.return_value = mock_llm
        mock_test_connection.return_value = True
        mock_evaluate.return_value = mock_ragas_evaluate()
        
        # Create app instance
        app = RAGTraceLite(temp_config_file)
        
        # Run evaluation
        output_dir = str(tmp_path / "test_reports")
        success = app.evaluate_dataset(
            data_path=temp_data_file,
            output_dir=output_dir,
            llm_provider="hcx"
        )
        
        assert success is True
        
        # Verify outputs
        output_path = Path(output_dir)
        assert output_path.exists()
        
        # Check for report files
        report_files = list(output_path.glob("*.md"))
        assert len(report_files) > 0
        
        # Verify database has results
        summary = app.db_manager.get_evaluation_summary(app.run_id)
        assert summary is not None
        assert 'ragas_score' in summary
        assert summary['ragas_score'] > 0
    
    @patch('ragtrace_lite.llm_factory.create_llm')
    @patch('ragtrace_lite.llm_factory.test_llm_connection')
    def test_evaluation_with_llm_failure(
        self,
        mock_test_connection,
        mock_create_llm,
        temp_config_file,
        temp_data_file
    ):
        """Test evaluation behavior when LLM connection fails"""
        # Setup mock to fail connection test
        mock_test_connection.return_value = False
        
        # Create app instance
        app = RAGTraceLite(temp_config_file)
        
        # Run evaluation
        success = app.evaluate_dataset(
            data_path=temp_data_file,
            llm_provider="gemini"
        )
        
        assert success is False
    
    def test_list_evaluations_flow(self, temp_config_file):
        """Test listing evaluations"""
        app = RAGTraceLite(temp_config_file)
        
        # Should not raise any exceptions even with empty database
        app.list_evaluations(limit=5)
    
    def test_show_evaluation_details_flow(self, temp_config_file):
        """Test showing evaluation details"""
        app = RAGTraceLite(temp_config_file)
        
        # Should handle non-existent run ID gracefully
        app.show_evaluation_details("non_existent_run_id")
    
    @pytest.mark.parametrize("file_format", ["json", "xlsx", "csv"])
    @patch('ragtrace_lite.llm_factory.create_llm')
    @patch('ragtrace_lite.llm_factory.test_llm_connection')
    @patch('ragtrace_lite.evaluator.evaluate')
    def test_multiple_file_formats(
        self,
        mock_evaluate,
        mock_test_connection,
        mock_create_llm,
        file_format,
        tmp_path,
        sample_dataset,
        temp_config_file,
        mock_llm_response,
        mock_ragas_evaluate
    ):
        """Test evaluation with different file formats"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm.invoke = mock_llm_response
        mock_create_llm.return_value = mock_llm
        mock_test_connection.return_value = True
        mock_evaluate.return_value = mock_ragas_evaluate()
        
        # Create test file based on format
        if file_format == "json":
            test_file = tmp_path / "test_data.json"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(sample_dataset, f)
        elif file_format == "xlsx":
            import pandas as pd
            test_file = tmp_path / "test_data.xlsx"
            df = pd.DataFrame(sample_dataset)
            df['contexts'] = df['contexts'].apply(json.dumps)
            df.to_excel(test_file, index=False)
        elif file_format == "csv":
            import pandas as pd
            test_file = tmp_path / "test_data.csv"
            df = pd.DataFrame(sample_dataset)
            df['contexts'] = df['contexts'].apply(lambda x: '|'.join(x))
            df.to_csv(test_file, index=False)
        
        # Create app and run evaluation
        app = RAGTraceLite(temp_config_file)
        success = app.evaluate_dataset(
            data_path=str(test_file),
            output_dir=str(tmp_path / "reports")
        )
        
        assert success is True
    
    def test_cleanup_resources(self, temp_config_file):
        """Test resource cleanup"""
        app = RAGTraceLite(temp_config_file)
        
        # Should not raise any exceptions
        app.cleanup()
        
        # Verify database connection is closed
        # Further operations should fail
        with pytest.raises(Exception):
            app.db_manager.list_evaluations()