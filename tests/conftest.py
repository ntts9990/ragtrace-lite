"""
Pytest configuration and fixtures for RAGTrace Lite tests
"""

import os
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_evaluation_data() -> Dict[str, Any]:
    """Sample evaluation data for testing"""
    return {
        "question": "What is RAGTrace Lite?",
        "contexts": [
            "RAGTrace Lite is a lightweight RAG evaluation framework.",
            "It supports multiple LLMs including HCX-005 and Gemini."
        ],
        "answer": "RAGTrace Lite is a lightweight framework for evaluating RAG systems.",
        "ground_truth": "RAGTrace Lite is a lightweight RAG evaluation framework that supports multiple LLMs."
    }


@pytest.fixture
def sample_dataset():
    """Sample dataset for testing"""
    return [
        {
            "question": "What is RAGTrace Lite?",
            "contexts": ["RAGTrace Lite is a lightweight RAG evaluation framework."],
            "answer": "RAGTrace Lite is a lightweight framework for evaluating RAG systems.",
            "ground_truth": "RAGTrace Lite is a lightweight RAG evaluation framework."
        },
        {
            "question": "Which LLMs are supported?",
            "contexts": ["It supports HCX-005 and Gemini 2.5 Flash."],
            "answer": "HCX-005 and Gemini are supported.",
            "ground_truth": "HCX-005 and Gemini 2.5 Flash are supported."
        }
    ]


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file"""
    config_content = """
llm:
  provider: hcx
  api_key: test_api_key
  model_name: HCX-005

embedding:
  provider: default
  device: cpu

evaluation:
  metrics:
    - faithfulness
    - answer_relevancy
    - context_precision
    - context_recall
    - answer_correctness
  batch_size: 1

database:
  path: ":memory:"

paths:
  reports: ./test_reports
  logs: ./test_logs
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def temp_data_file(tmp_path, sample_dataset):
    """Create a temporary data file"""
    import json
    data_file = tmp_path / "test_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(sample_dataset, f, ensure_ascii=False, indent=2)
    return str(data_file)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("CLOVA_STUDIO_API_KEY", "test_clova_key")
    monkeypatch.setenv("DEFAULT_LLM", "hcx")
    monkeypatch.setenv("DEFAULT_EMBEDDING", "bge_m3")


@pytest.fixture
def temp_db_path(tmp_path):
    """Temporary database path"""
    return str(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code here if needed
    pass