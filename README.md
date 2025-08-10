# RAGTrace Lite (v2)

경량 RAG(Retrieval-Augmented Generation) 평가 프레임워크. Excel 기반 데이터 관리, 환경 조건 추적, 통계 비교를 지원합니다.

> 한국어 버전: [README_KO.md](README_KO.md)

[![PyPI version](https://img.shields.io/pypi/v/ragtrace-lite.svg)](https://pypi.org/project/ragtrace-lite/)
[![Python Support](https://img.shields.io/pypi/pyversions/ragtrace-lite.svg)](https://pypi.org/project/ragtrace-lite/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Overview

RAGTrace Lite is a lightweight framework for evaluating RAG system performance. 
Built on the [RAGAS](https://github.com/explodinggradients/ragas) framework and optimized for Korean language environments.

**Key Features:**
- **Excel-first workflow**: 하나의 Excel에 데이터와 `env_` 조건을 함께 관리
- **Environment tracking**: `env_*` 컬럼으로 무제한 환경 조건 추적
- **Statistical compare**: 기간 윈도우 간 성능 비교 및 유의성 검정
- **Local embeddings**: 오프라인 환경을 위한 BGE-M3 임베딩 지원
- **Multi-LLM**: HCX-005/Gemini 등 다양한 LLM 연동

## Quick Start

### Installation from PyPI (Recommended)

```bash
# Basic installation
pip install ragtrace-lite

# Full installation (LLM + Embeddings + Enhanced features)
pip install "ragtrace-lite[all]"

# Optional installations
pip install "ragtrace-lite[llm]"        # LLM support only
pip install "ragtrace-lite[embeddings]" # Local embeddings only
```

### Development Installation

```bash
# Clone repository and install in development mode
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .[all]
```

### API Key Configuration
Create a `.env` file and add your API keys:
```env
CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### Run Sample Evaluation (Excel)
```bash
# 템플릿 생성
ragtrace-lite create-template

# Excel 기반 평가 실행
ragtrace-lite evaluate --excel data/sample_ragas_dataset.xlsx --name "demo"

# 기간 비교 리포트 생성
ragtrace-lite compare-windows \
  --a-start 2025-01-01 --a-end 2025-01-07 \
  --b-start 2025-01-08 --b-end 2025-01-14 \
  --metric ragas_score

# 환경 키 사용 현황
ragtrace-lite list-env

# 최근 이력 조회
ragtrace-lite history --limit 20
```

## Platform Support

- **Windows** 10+ (PowerShell/CMD)
- **macOS** 10.15+ (Intel/Apple Silicon)  
- **Linux** Ubuntu 18.04+
- **Python** 3.9, 3.10, 3.11, 3.12

**GPU Support**: CUDA (Linux), MPS (Apple Silicon), CPU (All platforms)

> **Detailed Setup Guide**: [SETUP.md](SETUP.md)

## Offline Deployment

RAGTrace Lite supports complete offline execution in air-gapped environments.

### Quick Offline Deployment

```bash
# 1. Create deployment package (internet-connected environment)
python scripts/prepare_offline_deployment.py

# 2. Copy generated ZIP file to air-gapped PC
# dist/ragtrace-lite-offline-YYYYMMDD-HHMMSS.zip

# 3. Extract and install in air-gapped environment
scripts/install.bat

# 4. Run evaluation
scripts/run_evaluation.bat
```

### Offline Support Features

- **Python 3.11 Auto-Install**: Windows installer included
- **BGE-M3 Local Model**: 2.3GB embedding model pre-downloaded
- **All Dependencies Included**: Complete offline installation with wheel files
- **Automated Install Scripts**: One-click installation with Windows batch files
- **Complete Manual Guide**: Manual installation support when scripts fail

### Air-gapped Requirements

- **OS**: Windows 10+ (64bit)
- **CPU**: x86_64 architecture
- **Memory**: Minimum 4GB RAM (for BGE-M3 loading)
- **Storage**: Minimum 5GB (Python + model + dependencies)
- **LLM**: HCX-005 API (internal network host)

> **Offline Deployment Guide**: [OFFLINE_DEPLOYMENT.md](OFFLINE_DEPLOYMENT.md)  
> **Manual Installation Guide**: [MANUAL_INSTALLATION_GUIDE.md](MANUAL_INSTALLATION_GUIDE.md)

## Features (detailed)

- 빠른 설치 및 실행, 로컬 임베딩/다중 LLM, Excel 기반 데이터/환경 관리, 통계 리포트 생성

## License

This project is provided under **Apache License 2.0**. See [LICENSE](LICENSE).

## Usage

### CLI Commands

```bash
# Create Excel template
ragtrace-lite create-template

# Evaluate with Excel
ragtrace-lite evaluate --excel data.xlsx --name "exp-1"

# Compare windows
ragtrace-lite compare-windows --a-start 2025-01-01 --a-end 2025-01-07 --b-start 2025-01-08 --b-end 2025-01-14 --metric ragas_score

# List env usage
ragtrace-lite list-env

# History
ragtrace-lite history --limit 20
```

### Python API

```python
from ragtrace_lite import ExcelParser
from ragtrace_lite.core.adaptive_evaluator import AdaptiveEvaluator
from ragtrace_lite.db.manager import DatabaseManager

parser = ExcelParser("data.xlsx")
dataset, environment, dataset_hash, dataset_items = parser.parse()

evaluator = AdaptiveEvaluator()
results = evaluator.evaluate_sync(dataset, environment)

db = DatabaseManager("data/ragtrace.db")
db.save_evaluation(
    run_id="demo",
    dataset_name="data",
    dataset_hash=dataset_hash,
    dataset_items=dataset_items,
    environment=environment,
    metrics=results["metrics"],
    details=results["details"],
)
```

### Environment Configuration

Create a `.env` file and set your API keys:

```bash
# HCX-005 (Naver CLOVA Studio)
CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key

# Gemini (Google)
GEMINI_API_KEY=your-gemini-api-key
```

## Supported Metrics

### With Ground Truth Data (5 Metrics)
- **Context Recall**: Recall of retrieved contexts
- **Context Precision**: Precision of retrieved contexts
- **Answer Correctness**: Correctness of the answer
- **Answer Relevancy**: Relevance of the answer to the question
- **Answer Similarity**: Similarity between generated and ground truth answers

### Without Ground Truth Data (4 Metrics)
- **Context Relevancy**: Relevance of context to the question
- **Answer Relevancy**: Relevance of answer to the question
- **Faithfulness**: How faithful the answer is to the context
- **Coherence**: Logical coherence of the answer

## Project Structure

```
ragtrace-lite/
├── src/ragtrace_lite/          # Source code
│   ├── __init__.py
│   ├── cli.py                  # CLI interface
│   ├── config_loader.py        # Configuration management
│   ├── evaluator.py            # Evaluation engine
│   ├── llm_factory.py          # LLM integration
│   ├── db_manager.py           # Database management
│   └── report_generator.py     # Report generation
├── tests/                      # Tests
├── scripts/                    # Utility scripts
├── data/                       # Sample data
├── config.yaml                 # Default configuration
└── pyproject.toml             # Project configuration
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

Having issues or questions?

- **Issue Tracker**: [GitHub Issues](https://github.com/ntts9990/ragtrace-lite/issues)
- **Documentation**: [Full Documentation](https://github.com/ntts9990/ragtrace-lite/wiki)
- **Email**: ntts9990@gmail.com

## Acknowledgments

This project is based on the following open-source projects:

- [RAGAS](https://github.com/explodinggradients/ragas) - RAG evaluation framework
- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - Multilingual embedding model
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full history of changes.

---

Made with ❤️ by [ntts9990](https://github.com/ntts9990)
