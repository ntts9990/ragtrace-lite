"""Configuration loader with environment variable support"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import re

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
                # Use default config
                config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            
            logger.info(f"Config loaded from: {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
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
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "llm": {
                "provider": os.getenv("LLM_PROVIDER", "hcx"),
                "hcx": {
                    "api_url": "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
                    "model_name": "HCX-005",
                    "temperature": 0.1,
                    "max_tokens": 1024,
                    "rate_limit_delay": 5.0,
                    "rate_limit_increment": 5.0,
                    "api_key": os.getenv("CLOVA_STUDIO_API_KEY")
                },
                "gemini": {
                    "api_url": "https://generativelanguage.googleapis.com/v1beta/models",
                    "model_name": "gemini-2.5-flash-lite",
                    "temperature": 0.1,
                    "max_tokens": 1024,
                    "rate_limit_delay": 5.0,
                    "rate_limit_increment": 5.0,
                    "api_key": os.getenv("GEMINI_API_KEY")
                }
            },
            "embeddings": {
                "provider": os.getenv("EMBEDDINGS_PROVIDER", "local"),
                "local": {
                    "model_path": "./models/bge-m3",
                    "use_gpu": False,
                    "batch_size": 32
                },
                "api": {
                    "api_url": os.getenv("EMBEDDINGS_API_URL", "http://localhost:8080/embeddings"),
                    "model_name": "bge-m3",
                    "api_key": os.getenv("EMBEDDINGS_API_KEY"),
                    "timeout": 30,
                    "max_batch_size": 100
                }
            },
            "evaluation": {
                "batch_size": {
                    "initial": 5,
                    "fallback_sizes": [3, 1]
                },
                "retry": {
                    "max_attempts": 3,
                    "backoff_factor": 2.0
                },
                "metrics": {
                    "base": ["faithfulness", "answer_relevancy", "context_precision"],
                    "conditional": ["context_recall", "answer_correctness"]
                }
            },
            "database": {
                "path": os.getenv("DB_PATH", "ragtrace.db"),
                "wal_mode": True
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "file": "ragtrace.log",
                "console": True,
                "timestamps": True
            },
            "reports": {
                "output_dir": "results",
                "formats": ["html", "json", "markdown"],
                "include_details": True,
                "include_plots": True
            },
            "offline": {
                "enabled": os.getenv("OFFLINE_MODE", "false").lower() == "true",
                "models_dir": "./models",
                "wheels_dir": "./offline_wheels",
                "python_version": "3.9",
                "platforms": ["win_amd64", "win32"]
            }
        }
    
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
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for specified provider"""
        if provider is None:
            provider = self.get("llm.provider", "hcx")
        
        config = self.get(f"llm.{provider}", {})
        config["provider"] = provider
        
        return config
    
    def get_embeddings_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get embeddings configuration for specified provider"""
        if provider is None:
            provider = self.get("embeddings.provider", "local")
        
        config = self.get(f"embeddings.{provider}", {})
        config["provider"] = provider
        
        return config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
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