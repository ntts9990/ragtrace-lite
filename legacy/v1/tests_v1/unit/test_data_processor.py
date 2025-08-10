"""
Unit tests for data_processor module
"""

import json
import pytest
from pathlib import Path
import pandas as pd

from ragtrace_lite.data_processor import DataProcessor
from ragtrace_lite.config_loader import Config, load_config


class TestDataProcessor:
    """Test data processing functionality"""
    
    @pytest.fixture
    def data_processor(self, temp_config_file):
        """Create DataProcessor instance"""
        config = load_config(temp_config_file)
        return DataProcessor(config)
    
    def test_load_json_data(self, data_processor, temp_data_file):
        """Test loading JSON data"""
        dataset = data_processor.load_and_prepare_data(temp_data_file)
        
        assert len(dataset) == 2
        assert all(isinstance(item, dict) for item in dataset)
        assert all('question' in item for item in dataset)
        assert all('contexts' in item for item in dataset)
        assert all('answer' in item for item in dataset)
        assert all('ground_truth' in item for item in dataset)
    
    def test_load_excel_data(self, data_processor, tmp_path, sample_dataset):
        """Test loading Excel data"""
        # Create Excel file
        excel_file = tmp_path / "test_data.xlsx"
        df = pd.DataFrame([
            {
                'question': item['question'],
                'contexts': json.dumps(item['contexts']),
                'answer': item['answer'],
                'ground_truth': item['ground_truth']
            }
            for item in sample_dataset
        ])
        df.to_excel(excel_file, index=False)
        
        # Load data
        dataset = data_processor.load_and_prepare_data(str(excel_file))
        
        assert len(dataset) == 2
        assert dataset[0]['question'] == sample_dataset[0]['question']
        assert isinstance(dataset[0]['contexts'], list)
    
    def test_load_csv_data(self, data_processor, tmp_path, sample_dataset):
        """Test loading CSV data"""
        # Create CSV file
        csv_file = tmp_path / "test_data.csv"
        df = pd.DataFrame([
            {
                'question': item['question'],
                'contexts': '|'.join(item['contexts']),  # Pipe separated
                'answer': item['answer'],
                'ground_truth': item['ground_truth']
            }
            for item in sample_dataset
        ])
        df.to_csv(csv_file, index=False)
        
        # Load data
        dataset = data_processor.load_and_prepare_data(str(csv_file))
        
        assert len(dataset) == 2
        assert isinstance(dataset[0]['contexts'], list)
        assert len(dataset[0]['contexts']) == len(sample_dataset[0]['contexts'])
    
    def test_validate_data_complete(self, data_processor, sample_dataset):
        """Test data validation with complete data"""
        validated = data_processor.validate_data(sample_dataset)
        
        assert len(validated) == 2
        assert all(item['is_valid'] for item in validated)
    
    def test_validate_data_missing_fields(self, data_processor):
        """Test data validation with missing fields"""
        incomplete_data = [
            {
                'question': 'Test question',
                'answer': 'Test answer'
                # Missing contexts and ground_truth
            }
        ]
        
        validated = data_processor.validate_data(incomplete_data)
        
        assert len(validated) == 1
        assert not validated[0]['is_valid']
        assert 'validation_errors' in validated[0]
    
    def test_validate_data_empty_values(self, data_processor):
        """Test data validation with empty values"""
        empty_data = [
            {
                'question': '',
                'contexts': [],
                'answer': 'Test answer',
                'ground_truth': 'Test truth'
            }
        ]
        
        validated = data_processor.validate_data(empty_data)
        
        assert len(validated) == 1
        assert not validated[0]['is_valid']
        assert 'validation_errors' in validated[0]
    
    def test_prepare_for_ragas(self, data_processor, sample_dataset):
        """Test preparing data for RAGAS evaluation"""
        # This would test the internal preparation logic
        # Implementation depends on actual RAGAS requirements
        pass
    
    def test_load_invalid_file_format(self, data_processor, tmp_path):
        """Test loading unsupported file format"""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("Invalid content")
        
        with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
            data_processor.load_and_prepare_data(str(invalid_file))
    
    def test_load_non_existent_file(self, data_processor):
        """Test loading non-existent file"""
        with pytest.raises(FileNotFoundError):
            data_processor.load_and_prepare_data("non_existent.json")
    
    def test_contexts_format_conversion(self, data_processor):
        """Test various contexts format conversions"""
        # Test JSON array string
        data_with_json_contexts = [{
            'question': 'Test',
            'contexts': '["context1", "context2"]',
            'answer': 'Answer',
            'ground_truth': 'Truth'
        }]
        
        processed = data_processor._process_contexts(data_with_json_contexts[0])
        assert isinstance(processed['contexts'], list)
        assert len(processed['contexts']) == 2
        
        # Test semicolon separated
        data_with_semicolon = [{
            'question': 'Test',
            'contexts': 'context1;context2;context3',
            'answer': 'Answer',
            'ground_truth': 'Truth'
        }]
        
        processed = data_processor._process_contexts(data_with_semicolon[0])
        assert isinstance(processed['contexts'], list)
        assert len(processed['contexts']) == 3