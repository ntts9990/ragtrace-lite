"""
Unit tests for config_loader module
"""

import os
import pytest
from pathlib import Path

from ragtrace_lite.config_loader import load_config, Config, LLMConfig, EvaluationConfig


class TestConfigLoader:
    """Test configuration loading functionality"""
    
    def test_load_config_from_file(self, temp_config_file):
        """Test loading configuration from YAML file"""
        config = load_config(temp_config_file)
        
        assert isinstance(config, Config)
        assert config.llm.provider == "hcx"
        assert config.llm.api_key == "test_api_key"
        assert config.llm.model_name == "HCX-005"
        assert config.evaluation.batch_size == 1
        assert len(config.evaluation.metrics) == 5
    
    def test_load_config_with_env_override(self, temp_config_file, monkeypatch):
        """Test environment variable override"""
        # Override API key via environment
        monkeypatch.setenv("CLOVA_STUDIO_API_KEY", "env_override_key")
        
        config = load_config(temp_config_file)
        assert config.llm.api_key == "env_override_key"
    
    def test_load_config_without_file(self, monkeypatch):
        """Test loading config when file doesn't exist"""
        monkeypatch.setenv("DEFAULT_LLM", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
        
        config = load_config("non_existent_file.yaml")
        
        assert config.llm.provider == "gemini"
        assert config.llm.api_key == "test_gemini_key"
        assert config.llm.model_name == "gemini-2.5-flash"
    
    def test_llm_config_validation(self):
        """Test LLM configuration validation"""
        # Valid provider
        llm_config = LLMConfig(provider="gemini", api_key="test")
        assert llm_config.provider == "gemini"
        
        # Invalid provider should raise error
        with pytest.raises(ValueError, match="지원하지 않는 LLM 제공자"):
            LLMConfig(provider="invalid_llm", api_key="test")
    
    def test_evaluation_config_defaults(self):
        """Test evaluation configuration defaults"""
        eval_config = EvaluationConfig()
        
        assert eval_config.batch_size == 1
        assert len(eval_config.metrics) == 5
        assert "faithfulness" in eval_config.metrics
        assert "answer_correctness" in eval_config.metrics
    
    def test_config_validation_error(self, tmp_path):
        """Test configuration validation error handling"""
        # Create invalid config
        invalid_config = """
llm:
  provider: invalid_provider
  api_key: test
"""
        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text(invalid_config)
        
        with pytest.raises(ValueError, match="설정 파일 검증 실패"):
            load_config(str(config_file))
    
    def test_gemini_env_override(self, temp_config_file, monkeypatch):
        """Test Gemini API key environment override"""
        # Create config with gemini
        gemini_config = """
llm:
  provider: gemini
  api_key: file_api_key
"""
        config_file = Path(temp_config_file).parent / "gemini_config.yaml"
        config_file.write_text(gemini_config)
        
        # Set environment variable
        monkeypatch.setenv("GEMINI_API_KEY", "env_gemini_key")
        
        config = load_config(str(config_file))
        assert config.llm.api_key == "env_gemini_key"