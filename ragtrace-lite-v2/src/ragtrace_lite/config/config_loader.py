"""Configuration loader with environment variable support"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import re

from .config_models import AppConfig, LLMConfig, EmbeddingsConfig, EvaluationConfig, DatabaseConfig, LoggingConfig, ReportsConfig, OfflineConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Flexible configuration loader with environment variable substitution"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to config file (default: config.yaml in project root)
        """
        if config_path is None:
            # Try multiple locations
            possible_paths = [
                Path.cwd() / "config.yaml",
                Path(__file__).parent.parent.parent / "config.yaml",
                Path.home() / ".ragtrace" / "config.yaml"
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
            else:
                # Use default config (from Pydantic model)
                config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config: AppConfig = self._load_config()
    
    def _load_config(self) -> AppConfig:
        """Load configuration from YAML file and validate with Pydantic"""
        raw_config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    raw_config = yaml.safe_load(f)
                
                # Substitute environment variables
                raw_config = self._substitute_env_vars(raw_config)
                
                logger.info(f"Config loaded from: {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load raw config from {self.config_path}: {e}")
        
        try:
            # Validate and load with Pydantic model
            return AppConfig(**raw_config)
        except Exception as e:
            logger.error(f"Failed to validate config with Pydantic: {e}")
            logger.warning("Using default configuration due to validation errors.")
            return AppConfig() # Return default valid config
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config"""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Match ${VAR_NAME} or $VAR_NAME
            pattern = r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)'
            
            def replacer(match):
                var_name = match.group(1) or match.group(2)
                return os.getenv(var_name, match.group(0))
            
            return re.sub(pattern, replacer, config)
        else:
            return config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path (e.g., "llm.hcx.api_url")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, BaseModel) and hasattr(value, key):
                value = getattr(value, key)
            elif isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_llm_config(self, provider: Optional[str] = None) -> LLMConfig:
        """Get LLM configuration for specified provider"""
        if provider is None:
            provider = self.config.llm.provider
        
        if provider == "hcx":
            return self.config.llm.hcx
        elif provider == "gemini":
            return self.config.llm.gemini
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def get_embeddings_config(self, provider: Optional[str] = None) -> EmbeddingsConfig:
        """Get embeddings configuration for specified provider"""
        if provider is None:
            provider = self.config.embeddings.provider
        
        if provider == "local":
            return self.config.embeddings.local
        elif provider == "api":
            return self.config.embeddings.api
        else:
            raise ValueError(f"Unknown embeddings provider: {provider}")
    
    def save_config(self, config: Optional[AppConfig] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config.dict(), f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Config saved to: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise


# Global config instance
_config = None


def get_config() -> ConfigLoader:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config


def reload_config(config_path: Optional[str] = None):
    """Reload configuration from file"""
    global _config
    _config = ConfigLoader(config_path)
    return _config