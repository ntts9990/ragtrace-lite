"""Tests for Excel parser module"""

import pytest
from pathlib import Path
import pandas as pd
import tempfile

from ragtrace_lite.core.excel_parser import ExcelParser


def create_test_excel(file_path: str):
    """Create a test Excel file"""
    data = {
        'question': ['What is RAG?', 'How does LLM work?'],
        'answer': ['RAG is Retrieval-Augmented Generation', 'LLM processes text'],
        'contexts': ['Context about RAG', 'Context about LLM'],
        'ground_truth': ['Correct answer 1', 'Correct answer 2'],
        'env_sys_prompt_version': ['v2.0', ''],
        'env_es_nodes': [3, ''],
        'env_quantized': ['false', ''],
        'env_custom_param': ['test_value', '']
    }
    
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False, engine='openpyxl')
    return file_path


class TestExcelParser:
    """Test cases for ExcelParser"""
    
    def test_parse_basic(self):
        """Test basic Excel parsing"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = create_test_excel(f.name)
            
            parser = ExcelParser(excel_path)
            dataset, environment, hash_val, items = parser.parse()
            
            # Check dataset
            assert len(dataset) == 2
            assert dataset[0]['question'] == 'What is RAG?'
            
            # Check environment
            assert environment['sys_prompt_version'] == 'v2.0'
            assert environment['es_nodes'] == 3
            assert environment['quantized'] is False
            assert environment['custom_param'] == 'test_value'
            
            # Check metadata
            assert items == 2
            assert len(hash_val) == 16
            
            # Cleanup
            Path(excel_path).unlink()
    
    def test_value_normalization(self):
        """Test value type normalization"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            parser = ExcelParser(f.name)
            
            # Boolean normalization
            assert parser._normalize_value('true') is True
            assert parser._normalize_value('TRUE') is True
            assert parser._normalize_value('yes') is True
            assert parser._normalize_value('1') is True
            
            assert parser._normalize_value('false') is False
            assert parser._normalize_value('FALSE') is False
            assert parser._normalize_value('no') is False
            assert parser._normalize_value('0') is False
            
            # Number normalization
            assert parser._normalize_value('123') == 123
            assert parser._normalize_value('123.45') == 123.45
            
            # String normalization
            assert parser._normalize_value('text') == 'text'
            assert parser._normalize_value('  text  ') == 'text'
    
    def test_context_splitting(self):
        """Test context string splitting"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            parser = ExcelParser(f.name)
            
            # Newline splitting
            contexts = parser._split_contexts('context1\ncontext2\ncontext3')
            assert contexts == ['context1', 'context2', 'context3']
            
            # Semicolon splitting
            contexts = parser._split_contexts('context1; context2; context3')
            assert contexts == ['context1', 'context2', 'context3']
            
            # Pipe splitting
            contexts = parser._split_contexts('context1 | context2 | context3')
            assert contexts == ['context1', 'context2', 'context3']
            
            # Single context
            contexts = parser._split_contexts('single context')
            assert contexts == ['single context']
            
            # Empty context
            contexts = parser._split_contexts('')
            assert contexts == []
    
    def test_missing_required_columns(self):
        """Test error handling for missing required columns"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            # Create Excel without required columns
            df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            df.to_excel(f.name, index=False)
            
            parser = ExcelParser(f.name)
            
            with pytest.raises(ValueError) as exc:
                parser.parse()
            
            assert "Missing required columns" in str(exc.value)
            
            # Cleanup
            Path(f.name).unlink()
    
    def test_template_creation(self):
        """Test template Excel creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.xlsx"
            
            ExcelParser.create_template(str(template_path))
            
            assert template_path.exists()
            
            # Check template content
            df = pd.read_excel(template_path, sheet_name='Data')
            
            # Check required columns exist
            assert 'question' in df.columns
            assert 'answer' in df.columns
            assert 'contexts' in df.columns
            assert 'ground_truth' in df.columns
            
            # Check env columns exist
            env_cols = [col for col in df.columns if col.startswith('env_')]
            assert len(env_cols) > 0
            assert 'env_sys_prompt_version' in df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])