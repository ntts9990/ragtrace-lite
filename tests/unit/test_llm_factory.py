"""
Unit tests for llm_factory module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from ragtrace_lite.llm_factory import create_llm, test_llm_connection
from ragtrace_lite.config_loader import Config, LLMConfig, EmbeddingConfig


class TestLLMFactory:
    """Test LLM factory functionality"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config(
            llm=LLMConfig(
                provider="hcx",
                api_key="test_api_key",
                model_name="HCX-005"
            ),
            embedding=EmbeddingConfig(
                provider="default",
                device="cpu"
            )
        )
    
    def test_create_hcx_llm(self, config):
        """Test creating HCX LLM instance"""
        config.llm.provider = "hcx"
        
        llm = create_llm(config)
        
        assert llm is not None
        assert hasattr(llm, 'invoke')
        assert hasattr(llm, 'api_key')
        assert llm.api_key == "test_api_key"
    
    def test_create_gemini_llm(self, config):
        """Test creating Gemini LLM instance"""
        config.llm.provider = "gemini"
        config.llm.api_key = "test_gemini_key"
        config.llm.model_name = "gemini-2.5-flash"
        
        llm = create_llm(config)
        
        assert llm is not None
        assert hasattr(llm, 'invoke')
    
    def test_create_invalid_llm(self, config):
        """Test creating LLM with invalid provider"""
        config.llm.provider = "invalid_provider"
        
        with pytest.raises(ValueError, match="지원하지 않는 LLM 제공자"):
            create_llm(config)
    
    def test_create_llm_without_api_key(self, config):
        """Test creating LLM without API key"""
        config.llm.api_key = None
        
        with pytest.raises(ValueError, match="API 키가 설정되지 않았습니다"):
            create_llm(config)
    
    @patch('ragtrace_lite.llm_factory.requests.post')
    def test_test_llm_connection_hcx_success(self, mock_post):
        """Test successful HCX connection test"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": {"code": "20000"},
            "result": {"outputText": "Test response"}
        }
        mock_post.return_value = mock_response
        
        # Create mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Test response")
        
        result = test_llm_connection(mock_llm, "hcx")
        assert result is True
    
    @patch('ragtrace_lite.llm_factory.requests.post')
    def test_test_llm_connection_hcx_failure(self, mock_post):
        """Test failed HCX connection test"""
        # Mock failed response
        mock_post.side_effect = Exception("Connection error")
        
        # Create mock LLM
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Connection error")
        
        result = test_llm_connection(mock_llm, "hcx")
        assert result is False
    
    def test_test_llm_connection_gemini_success(self):
        """Test successful Gemini connection test"""
        # Create mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Test response")
        
        result = test_llm_connection(mock_llm, "gemini")
        assert result is True
    
    def test_test_llm_connection_gemini_failure(self):
        """Test failed Gemini connection test"""
        # Create mock LLM
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("API key invalid")
        
        result = test_llm_connection(mock_llm, "gemini")
        assert result is False
    
    def test_hcx_rate_limiting(self, config):
        """Test HCX rate limiting implementation"""
        config.llm.provider = "hcx"
        
        llm = create_llm(config)
        
        # Check if rate limiting is configured
        assert hasattr(llm, '_rate_limit_delay')
        assert llm._rate_limit_delay >= 2  # HCX requires 2 second delay
    
    def test_create_embeddings_default(self, config):
        """Test creating default embeddings"""
        config.embedding.provider = "default"
        
        # This would test embedding creation
        # Implementation depends on actual embedding logic
        pass
    
    def test_create_embeddings_bge_m3(self, config):
        """Test creating BGE-M3 embeddings"""
        config.embedding.provider = "bge_m3"
        
        # This would test BGE-M3 embedding creation
        # Implementation depends on actual embedding logic
        pass