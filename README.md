[![PyPI version](https://badge.fury.io/py/ragtrace-lite.svg)](https://badge.fury.io/py/ragtrace-lite)
[![Python Support](https://img.shields.io/pypi/pyversions/ragtrace-lite.svg)](https://pypi.org/project/ragtrace-lite/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# RAGTrace Lite

A lightweight RAG (Retrieval-Augmented Generation) evaluation framework with Korean language support

> 한국어 버전: [README_KO.md](README_KO.md)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE-APACHE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

RAGTrace Lite is a lightweight framework for evaluating RAG system performance. 
Built on the [RAGAS](https://github.com/explodinggradients/ragas) framework and optimized for Korean language environments.

**Key Features:**
- **Intelligent Metric Selection**: Automatically selects 5 or 4 metrics based on ground truth data availability
- **Local BGE-M3 Embeddings**: Offline embedding support for air-gapped environments  
- **Multi-LLM Support**: HCX-005 (Naver CLOVA Studio) and Gemini (Google)
- **Offline Deployment**: Complete air-gapped deployment for closed networks
- **Korean Language Optimized**: Native Korean language support

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
GOOGLE_API_KEY=your-gemini-api-key
```

### Run Sample Evaluation
```bash
# Run evaluation with BGE-M3 + HCX
ragtrace-lite evaluate data/sample_data.json --llm hcx

# Generate web dashboard
ragtrace-lite dashboard --open
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

## Key Features

- **Fast Installation & Execution**: Quick start with minimal dependencies
- **Multi-LLM Support**: HCX-005 (Naver CLOVA Studio) & Gemini (Google)
- **Local Embeddings**: Offline embedding support via BGE-M3
- **Intelligent Metric Selection**: Automatically selects 5 or 4 metrics based on ground truth availability
- **Complete Offline Support**: Full air-gapped execution for closed networks
- **Data Storage**: SQLite-based evaluation result storage and history management
- **Enhanced Reports**: JSON, CSV, Markdown, Elasticsearch NDJSON format support
- **Security**: Environment variable-based API key management

## License

This project is provided under **Apache License 2.0**:

- **Apache License 2.0**: [LICENSE-APACHE](LICENSE-APACHE)

See the [LICENSE](LICENSE) file for details.

## Usage

### CLI Commands

```bash
# Run evaluation
ragtrace-lite evaluate data.json --llm hcx

# List available datasets
ragtrace-lite list-datasets

# Generate web dashboard
ragtrace-lite dashboard --open

# Check version
ragtrace-lite version
```

### Python API

```python
from ragtrace_lite import RAGTraceEvaluator
from ragtrace_lite.config_loader import ConfigLoader

# Load configuration
config = ConfigLoader.load_config()

# Initialize evaluator
evaluator = RAGTraceEvaluator(config)

# Run evaluation
results = evaluator.evaluate("your_data.json")
```

### Environment Configuration

Create a `.env` file and set your API keys:

```bash
# HCX-005 (Naver CLOVA Studio)
CLOVA_STUDIO_API_KEY=your_clova_api_key

# Gemini (Google)
GEMINI_API_KEY=your_gemini_api_key
```

## 프로젝트 구조

```
ragtrace-lite/
├── src/
│   ├── config_loader.py      # 설정 관리
│   ├── data_processor.py     # 데이터 처리
│   ├── db_manager.py         # 데이터베이스 관리
│   ├── evaluator.py          # RAGAS 평가 엔진
│   ├── llm_factory.py        # LLM 어댑터
│   └── report_generator.py   # 보고서 생성
├── data/                     # 평가 데이터
├── config.yaml              # 설정 파일
└── ragtrace_lite.py         # CLI 진입점
```

## 기여하기

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참조하세요.

## 감사의 글

이 프로젝트는 다음 프로젝트들에 기반하고 있습니다:
- [RAGTrace](https://github.com/ntts9990/RAGTrace) - 원본 프로젝트
- [RAGAS](https://github.com/explodinggradients/ragas) - RAG 평가 프레임워크

## 저작권

Original work Copyright 2025 RAGTrace Contributors  
Modified work Copyright 2025 RAGTrace Lite Contributors
