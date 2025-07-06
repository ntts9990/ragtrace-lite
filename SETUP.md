# RAGTrace Lite 설치 가이드

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite
```

### 2. 환경 설정

#### Python 환경 (권장: Python 3.9+)
```bash
# uv 사용 (권장)
uv venv
uv sync

# 또는 pip 사용
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -e .[all]
```

### 3. API 키 설정
`.env` 파일을 생성하고 다음 내용을 추가:

```env
# HCX (Naver Clova Studio) - 필수
CLOVA_STUDIO_API_KEY=nv-your-api-key-here

# Gemini (Google) - 필수  
GOOGLE_API_KEY=your-gemini-api-key-here

# OpenAI - 선택사항 (기본 임베딩용)
OPENAI_API_KEY=sk-your-openai-api-key-here

# BGE-M3 모델 경로 - 선택사항 (기본값: ./models/bge-m3)
BGE_M3_MODEL_PATH=./models/bge-m3
```

### 4. 실행 테스트
```bash
# 기본 평가 실행 (BGE-M3 + HCX)
uv run python -m ragtrace_lite.cli evaluate data/evaluation_data.json --llm hcx

# 웹 대시보드 생성
uv run python -m ragtrace_lite.cli dashboard --open
```

## 🖥️ 플랫폼별 주의사항

### Windows
- PowerShell 또는 Command Prompt 사용
- 가상환경 활성화: `venv\Scripts\activate`
- 경로 구분자: `\` 대신 `/` 사용 권장

### Linux
- 기본 설정으로 동작
- CUDA 지원 시 자동으로 GPU 사용

### macOS
- M1/M2 Mac의 경우 MPS 자동 감지
- Intel Mac의 경우 CPU 사용

## 📦 의존성 옵션

```bash
# 최소 설치 (LLM만)
pip install -e .[llm]

# 임베딩 포함
pip install -e .[llm,embeddings]

# 전체 기능
pip install -e .[all]
```

## 🔧 트러블슈팅

### BGE-M3 모델 다운로드 실패
```bash
# 수동 다운로드
mkdir -p models
cd models
git clone https://huggingface.co/BAAI/bge-m3
```

### API 키 인식 안됨
- `.env` 파일이 프로젝트 루트에 있는지 확인
- API 키에 따옴표 없이 입력했는지 확인
- 환경변수 직접 설정: `export CLOVA_STUDIO_API_KEY=your-key`

### 권한 오류 (Linux/Mac)
```bash
chmod +x scripts/*
sudo chown -R $USER:$USER ./models
```

## 📊 사용 예제

```bash
# 다양한 LLM으로 평가
ragtrace-lite evaluate data/sample.json --llm gemini
ragtrace-lite evaluate data/sample.json --llm hcx

# 결과 확인
ragtrace-lite dashboard
ragtrace-lite list-datasets
```

## 🌐 지원 환경

- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.9, 3.10, 3.11, 3.12
- **GPU**: CUDA (Linux), MPS (macOS M1/M2), CPU (모든 플랫폼)