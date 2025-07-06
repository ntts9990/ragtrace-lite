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

## 🚀 빠른 시작

### 📦 PyPI에서 설치 (권장)

```bash
# 기본 설치
pip install ragtrace-lite

# 전체 기능 설치 (LLM + 임베딩 + 향상된 기능)
pip install "ragtrace-lite[all]"

# 선택적 설치
pip install "ragtrace-lite[llm]"        # LLM 지원만
pip install "ragtrace-lite[embeddings]" # 로컬 임베딩만
```

### 🔧 개발자용 설치

```bash
# 저장소 클론 및 개발 모드 설치
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite

# uv 사용 (권장)
uv sync

# 또는 pip 사용
pip install -e .[all]
```

### 2. API 키 설정
`.env` 파일을 생성하고 API 키를 입력:
```env
CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key
GOOGLE_API_KEY=your-gemini-api-key
```

### 3. 샘플 평가 실행
```bash
# BGE-M3 + HCX로 평가 실행
ragtrace-lite evaluate data/sample_data.json --llm hcx

# 웹 대시보드 생성
ragtrace-lite dashboard --open
```

## 💻 플랫폼 지원

- ✅ **Windows** 10+ (PowerShell/CMD)
- ✅ **macOS** 10.15+ (Intel/Apple Silicon)  
- ✅ **Linux** Ubuntu 18.04+
- ✅ **Python** 3.9, 3.10, 3.11, 3.12

**GPU 지원**: CUDA (Linux), MPS (Apple Silicon), CPU (모든 플랫폼)

> 📖 **상세 설치 가이드**: [SETUP.md](SETUP.md) 참조

## 🔒 폐쇄망 배포

RAGTrace Lite는 **인터넷이 차단된 폐쇄망 환경**에서도 완전한 오프라인 실행을 지원합니다.

### 빠른 폐쇄망 배포

```bash
# 1. 배포 패키지 생성 (인터넷 연결 환경)
python scripts/prepare_offline_deployment.py

# 2. 생성된 ZIP 파일을 폐쇄망 PC로 복사
# dist/ragtrace-lite-offline-YYYYMMDD-HHMMSS.zip

# 3. 폐쇄망에서 압축 해제 후 설치
scripts/install.bat

# 4. 평가 실행
scripts/run_evaluation.bat
```

### 폐쇄망 지원 기능

- 🐍 **Python 3.11 자동 설치**: Windows 설치 파일 포함
- 🤖 **BGE-M3 로컬 모델**: 2.3GB 임베딩 모델 사전 다운로드
- 📦 **모든 의존성 포함**: wheel 파일로 완전 오프라인 설치
- 🔧 **자동 설치 스크립트**: Windows 배치 파일로 원클릭 설치
- 📚 **완전한 수동 가이드**: 스크립트 실패 시 수동 설치 지원

### 폐쇄망 요구사항

- **OS**: Windows 10+ (64bit)
- **CPU**: x86_64 아키텍처
- **메모리**: 최소 4GB RAM (BGE-M3 로딩용)
- **저장공간**: 최소 5GB (Python + 모델 + 의존성)
- **LLM**: HCX-005 API (폐쇄망 내부 호스트)

> 📖 **폐쇄망 배포 가이드**: [OFFLINE_DEPLOYMENT.md](OFFLINE_DEPLOYMENT.md)  
> 🛠️ **수동 설치 가이드**: [MANUAL_INSTALLATION_GUIDE.md](MANUAL_INSTALLATION_GUIDE.md)

## 주요 특징

- 🚀 **빠른 설치 및 실행**: 최소 의존성으로 빠르게 시작
- 🤖 **다중 LLM 지원**: HCX-005 (Naver) & Gemini (Google)
- 🌐 **로컬 임베딩**: BGE-M3를 통한 오프라인 임베딩 지원
- 📊 **지능형 메트릭 선택**: Ground Truth 데이터 유무에 따라 자동으로 5개 또는 4개 메트릭 적용
- 🔒 **완전한 폐쇄망 지원**: 인터넷 차단 환경에서도 완전 오프라인 실행
- 💾 **데이터 저장**: SQLite 기반 평가 결과 저장 및 이력 관리
- 📈 **향상된 보고서**: JSON, CSV, Markdown, Elasticsearch NDJSON 형식 지원
- 🔐 **보안**: 환경 변수 기반 API 키 관리

## 라이선스

이 프로젝트는 **듀얼 라이선스**로 제공됩니다:

- **MIT 라이선스**: [LICENSE-MIT](LICENSE-MIT)
- **Apache License 2.0**: [LICENSE-APACHE](LICENSE-APACHE)

사용자는 두 라이선스 중 하나를 선택하여 사용할 수 있습니다.
자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📚 설치 및 사용법

### CLI 명령어

```bash
# 평가 실행
ragtrace-lite evaluate data.json --llm hcx

# 데이터셋 목록 확인
ragtrace-lite list-datasets

# 웹 대시보드 생성
ragtrace-lite dashboard --open

# 버전 확인
ragtrace-lite version
```

### Python API 사용

```python
from ragtrace_lite import RAGTraceEvaluator
from ragtrace_lite.config_loader import ConfigLoader

# 설정 로드
config = ConfigLoader.load_config()

# 평가기 초기화
evaluator = RAGTraceEvaluator(config)

# 평가 실행
results = evaluator.evaluate("your_data.json")
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
