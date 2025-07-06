[![PyPI version](https://badge.fury.io/py/ragtrace-lite.svg)](https://badge.fury.io/py/ragtrace-lite)
[![Python Support](https://img.shields.io/pypi/pyversions/ragtrace-lite.svg)](https://pypi.org/project/ragtrace-lite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Documentation Status](https://readthedocs.org/projects/ragtrace-lite/badge/?version=latest)](https://ragtrace-lite.readthedocs.io/en/latest/?badge=latest)

# RAGTrace Lite

경량화된 RAG (Retrieval-Augmented Generation) 평가 프레임워크

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE-MIT)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE-APACHE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 개요

RAGTrace Lite는 RAG 시스템의 성능을 평가하기 위한 경량화된 프레임워크입니다. 
[RAGAS](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 하며, 
한국어 환경에 최적화되어 있습니다.

## 주요 특징

- 🚀 **빠른 설치 및 실행**: 최소 의존성으로 빠르게 시작
- 🤖 **다중 LLM 지원**: HCX-005 (Naver) & Gemini (Google)
- 🌐 **로컬 임베딩**: BGE-M3를 통한 오프라인 임베딩 지원
- 📊 **5가지 RAGAS 메트릭**: Faithfulness, Answer Relevancy, Context Precision/Recall, Answer Correctness
- 💾 **데이터 저장**: SQLite 기반 평가 결과 저장 및 이력 관리
- 📈 **향상된 보고서**: JSON, CSV, Markdown, Elasticsearch NDJSON 형식 지원
- 🔐 **보안**: 환경 변수 기반 API 키 관리

## 라이선스

이 프로젝트는 **듀얼 라이선스**로 제공됩니다:

- **MIT 라이선스**: [LICENSE-MIT](LICENSE-MIT)
- **Apache License 2.0**: [LICENSE-APACHE](LICENSE-APACHE)

사용자는 두 라이선스 중 하나를 선택하여 사용할 수 있습니다.
자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 빠른 시작

### 설치

#### 🚀 UV 사용 (권장)

```bash
# UV 설치
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell  
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 또는 pip으로
pip install uv

# RAGTrace Lite 설치
uv pip install ragtrace-lite

# 전체 기능 설치
uv pip install "ragtrace-lite[all]"
```

#### 📦 pip 사용

```bash
# 기본 설치 (최소 기능)
pip install ragtrace-lite

# LLM 지원 포함
pip install "ragtrace-lite[llm]"

# 로컬 임베딩 포함
pip install "ragtrace-lite[embeddings]"

# 전체 기능
pip install "ragtrace-lite[all]"
```

> 💡 **UV 사용을 권장하는 이유**: 더 빠른 의존성 해결, 더 나은 가상환경 관리, 크로스 플랫폼 일관성

### 기본 사용법

```bash
# 간단한 평가 실행 (HCX-005 + BGE-M3)
ragtrace-lite evaluate data.json

# LLM 선택
ragtrace-lite evaluate data.json --llm gemini

# 향상된 기능 사용
ragtrace-lite-enhanced evaluate data.json
```

### 환경 설정

`.env` 파일을 생성하여 API 키를 설정하세요:

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
- [RAGTrace](https://github.com/yourusername/RAGTrace) - 원본 프로젝트
- [RAGAS](https://github.com/explodinggradients/ragas) - RAG 평가 프레임워크

## 저작권

Original work Copyright 2024 RAGTrace Contributors  
Modified work Copyright 2025 RAGTrace Lite Contributors