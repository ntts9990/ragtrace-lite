"""
Integration tests for CLI interface
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
from io import StringIO

from ragtrace_lite.cli import main, main_enhanced


class TestCLI:
    """Test CLI functionality"""
    
    @pytest.fixture
    def mock_argv(self, monkeypatch):
        """Mock sys.argv for testing CLI commands"""
        def _mock_argv(args):
            monkeypatch.setattr(sys, 'argv', ['ragtrace-lite'] + args)
        return _mock_argv
    
    @patch('ragtrace_lite.cli.RAGTraceLite')
    def test_cli_evaluate_command(self, mock_app_class, mock_argv, temp_data_file):
        """Test CLI evaluate command"""
        # Setup mock
        mock_app = Mock()
        mock_app.evaluate_dataset.return_value = True
        mock_app_class.return_value = mock_app
        
        # Run CLI command
        mock_argv(['evaluate', temp_data_file])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify success exit
        assert exc_info.value.code == 0
        
        # Verify method was called
        mock_app.evaluate_dataset.assert_called_once()
        call_args = mock_app.evaluate_dataset.call_args
        assert call_args.kwargs['data_path'] == temp_data_file
    
    @patch('ragtrace_lite.cli.RAGTraceLite')
    def test_cli_evaluate_with_options(self, mock_app_class, mock_argv, temp_data_file):
        """Test CLI evaluate command with options"""
        # Setup mock
        mock_app = Mock()
        mock_app.evaluate_dataset.return_value = True
        mock_app_class.return_value = mock_app
        
        # Run CLI command with options
        mock_argv([
            'evaluate', 
            temp_data_file,
            '--llm', 'gemini',
            '--output', '/tmp/results'
        ])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify success exit
        assert exc_info.value.code == 0
        
        # Verify method was called with correct arguments
        call_args = mock_app.evaluate_dataset.call_args
        assert call_args[1]['llm_provider'] == 'gemini'
        assert call_args[1]['output_dir'] == '/tmp/results'
    
    def test_cli_list_datasets(self, mock_argv, tmp_path, capsys):
        """Test CLI list-datasets command"""
        # Create test data directory with files
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()
        (data_dir / "dataset1.json").touch()
        (data_dir / "dataset2.json").touch()
        (data_dir / "dataset3.xlsx").touch()
        
        # Run CLI command
        mock_argv(['list-datasets', '--data-dir', str(data_dir)])
        
        with pytest.raises(SystemExit):
            main()
        
        # Check output
        captured = capsys.readouterr()
        assert "dataset1.json" in captured.out
        assert "dataset2.json" in captured.out
        assert "dataset3.xlsx" in captured.out
    
    def test_cli_version(self, mock_argv, capsys):
        """Test CLI version command"""
        mock_argv(['version'])
        
        main()
        
        # Check output
        captured = capsys.readouterr()
        assert "RAGTrace Lite" in captured.out
        assert "v" in captured.out
        assert "MIT OR Apache-2.0" in captured.out
    
    def test_cli_no_command(self, mock_argv, capsys):
        """Test CLI with no command"""
        mock_argv([])
        
        with pytest.raises(SystemExit):
            main()
        
        # Should print help
        captured = capsys.readouterr()
        assert "usage:" in captured.out or "Usage:" in captured.out
        assert "evaluate" in captured.out
    
    @patch('ragtrace_lite.cli.RAGTraceLite')
    def test_cli_evaluate_failure(self, mock_app_class, mock_argv, temp_data_file):
        """Test CLI evaluate command failure"""
        # Setup mock to fail
        mock_app = Mock()
        mock_app.evaluate_dataset.return_value = False
        mock_app_class.return_value = mock_app
        
        # Run CLI command
        mock_argv(['evaluate', temp_data_file])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify failure exit
        assert exc_info.value.code == 1
    
    @patch('ragtrace_lite.cli.RAGTraceLiteEnhanced')
    def test_enhanced_cli_evaluate(self, mock_app_class, mock_argv, temp_data_file):
        """Test enhanced CLI evaluate command"""
        # Setup mock
        mock_app = Mock()
        mock_app.evaluate_dataset.return_value = True
        mock_app_class.return_value = mock_app
        
        # Run enhanced CLI command
        mock_argv(['evaluate', temp_data_file])
        
        with pytest.raises(SystemExit) as exc_info:
            main_enhanced()
        
        # Verify success exit
        assert exc_info.value.code == 0
        
        # Verify enhanced app was used
        mock_app_class.assert_called_once()
        mock_app.evaluate_dataset.assert_called_once()
    
    @patch('ragtrace_lite.cli.RAGTraceLiteEnhanced')
    def test_enhanced_cli_list(self, mock_app_class, mock_argv):
        """Test enhanced CLI list command"""
        # Setup mock
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        # Run enhanced CLI command
        mock_argv(['list', '--limit', '20'])
        
        main_enhanced()
        
        # Verify method was called
        mock_app.list_evaluations.assert_called_once_with(20)
    
    @patch('ragtrace_lite.cli.RAGTraceLiteEnhanced')
    def test_enhanced_cli_show(self, mock_app_class, mock_argv):
        """Test enhanced CLI show command"""
        # Setup mock
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        # Run enhanced CLI command
        mock_argv(['show', 'test_run_id_123'])
        
        main_enhanced()
        
        # Verify method was called
        mock_app.show_evaluation_details.assert_called_once_with('test_run_id_123')
    
    @patch('ragtrace_lite.cli.RAGTraceLiteEnhanced')
    def test_enhanced_cli_export_logs(self, mock_app_class, mock_argv):
        """Test enhanced CLI export-logs command"""
        # Setup mock
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        # Run enhanced CLI command
        mock_argv(['export-logs', '/tmp/logs.ndjson'])
        
        main_enhanced()
        
        # Verify method was called
        mock_app.export_logs.assert_called_once_with('/tmp/logs.ndjson')