# 🔒 RAGTrace Lite 폐쇄망 윈도우 배포 가이드

## 📋 개요
이 가이드는 RAGTrace Lite를 폐쇄망 윈도우 PC에서 실행하기 위한 완전한 준비 과정을 설명합니다.

## 🎯 배포 환경
- **타겟 OS**: Windows 10/11
- **Python**: 3.11.x
- **네트워크**: 폐쇄망 (인터넷 연결 없음)
- **LLM**: HCX-005 (API 호출)
- **임베딩**: BGE-M3 (로컬 모델)

## 📦 사전 준비 (인터넷 연결된 환경에서)

### 1. Python 3.11 설치 파일 다운로드
- [Python 3.11 Windows 설치 파일](https://www.python.org/downloads/windows/) 다운로드
- 파일명: `python-3.11.x-amd64.exe`

### 2. 의존성 패키지 다운로드
```bash
# 모든 의존성을 wheel 형태로 다운로드
python -m pip download -r requirements-offline.txt -d wheels --platform win_amd64 --python-version 3.11 --abi cp311 --only-binary=:all:

# BGE-M3 모델 사전 다운로드를 위한 스크립트 실행
python scripts/download_bge_m3.py
```

### 3. 프로젝트 패키징
```bash
# 전체 프로젝트를 압축
python scripts/create_offline_package.py
```

## 📁 배포 패키지 구조
```
ragtrace-lite-offline/
├── python-installer/
│   └── python-3.11.x-amd64.exe
├── wheels/
│   ├── *.whl (모든 의존성)
│   └── requirements.txt
├── models/
│   └── bge-m3/ (사전 다운로드된 모델)
├── src/
│   └── ragtrace_lite/ (소스 코드)
├── data/
│   ├── input/
│   └── output/
├── scripts/
│   ├── install.bat
│   ├── run_evaluation.bat
│   └── setup_environment.py
├── config/
│   ├── config.yaml
│   └── .env.template
└── README_OFFLINE.md
```

## 🚀 폐쇄망 설치 과정

### 1. Python 설치
```cmd
# 관리자 권한으로 실행
python-installer\python-3.11.x-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
```

### 2. 환경 설정
```cmd
# 설치 스크립트 실행
scripts\install.bat
```

### 3. API 키 설정
```cmd
# .env 파일 생성 및 설정
copy config\.env.template .env
# .env 파일을 열어 HCX API 키 입력
notepad .env
```

### 4. 테스트 실행
```cmd
# 평가 실행
scripts\run_evaluation.bat
```

## ⚙️ 환경 변수 설정

### .env 파일 예시
```bash
# HCX API 설정 (폐쇄망 내부 API 엔드포인트)
CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key-here
HCX_API_ENDPOINT=https://your-internal-hcx-endpoint.com

# BGE-M3 모델 경로 (로컬)
BGE_M3_MODEL_PATH=./models/bge-m3
BGE_M3_DEVICE=auto

# 데이터베이스 설정
DATABASE_PATH=./db/ragtrace_lite.db

# 로그 설정
LOG_LEVEL=INFO
LOG_FILE=./logs/ragtrace.log
```

## 🔧 주요 스크립트

### install.bat
```batch
@echo off
echo RAGTrace Lite 폐쇄망 설치 시작...

echo [1/4] Python 가상환경 생성
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] 의존성 패키지 설치
python -m pip install --no-index --find-links wheels -r wheels\requirements.txt

echo [3/4] RAGTrace Lite 설치
python -m pip install -e .

echo [4/4] 디렉토리 구조 생성
mkdir db logs reports\web reports\markdown

echo 설치 완료!
echo 다음 단계: .env 파일에 API 키를 설정하세요.
pause
```

### run_evaluation.bat
```batch
@echo off
call venv\Scripts\activate.bat

echo RAGTrace Lite 평가 실행...
python -m src.ragtrace_lite.main --llm-provider hcx --llm-model HCX-005 --embedding-provider bge_m3 --data-file data\input\evaluation_data.json

echo 평가 완료!
echo 결과: reports\web\dashboard.html 확인
pause
```

## 🔍 트러블슈팅

### 일반적인 문제들

1. **Python 설치 오류**
   - 관리자 권한으로 실행 확인
   - 기존 Python 버전과 충돌 확인

2. **의존성 설치 오류**
   - wheel 파일 무결성 확인
   - Windows용 바이너리 패키지 확인

3. **BGE-M3 모델 로딩 오류**
   - 모델 파일 경로 확인
   - 디스크 용량 확인 (약 3GB 필요)

4. **HCX API 연결 오류**
   - 폐쇄망 내부 API 엔드포인트 확인
   - API 키 유효성 확인
   - 네트워크 방화벽 설정 확인

## 📊 성능 고려사항

### 시스템 요구사항
- **RAM**: 최소 8GB, 권장 16GB
- **디스크**: 최소 5GB 여유 공간
- **CPU**: BGE-M3 모델 실행을 위한 멀티코어 권장

### 최적화 설정
```yaml
# config.yaml
performance:
  batch_size: 1  # 메모리 절약을 위해 작게 설정
  max_workers: 2  # CPU 코어 수에 따라 조정
  device: auto    # auto/cpu/cuda 선택

evaluation:
  timeout: 300    # HCX API 타임아웃 (초)
  retry_count: 3  # 실패 시 재시도 횟수
```

## 🔒 보안 고려사항

1. **API 키 보안**
   - .env 파일 권한 설정
   - 로그에 API 키 노출 방지

2. **모델 파일 보안**
   - 모델 파일 무결성 검증
   - 접근 권한 제한

3. **네트워크 보안**
   - 내부 API 엔드포인트 화이트리스트
   - HTTPS 강제 사용

## 📝 체크리스트

### 배포 전 확인사항
- [ ] Python 3.11 설치 파일 준비
- [ ] 모든 wheel 패키지 다운로드 완료
- [ ] BGE-M3 모델 사전 다운로드 완료
- [ ] 설치 스크립트 테스트 완료
- [ ] HCX API 엔드포인트 확인
- [ ] 샘플 데이터 준비

### 설치 후 확인사항
- [ ] Python 3.11 정상 설치
- [ ] 가상환경 생성 완료
- [ ] 모든 의존성 설치 완료
- [ ] BGE-M3 모델 로딩 성공
- [ ] HCX API 연결 성공
- [ ] 샘플 평가 실행 성공
- [ ] 웹 대시보드 생성 확인

## 📞 지원

문제 발생 시 다음 로그 파일을 확인하세요:
- `logs/ragtrace.log`: 애플리케이션 로그
- `logs/install.log`: 설치 과정 로그
- `db/ragtrace_lite.db`: 평가 결과 데이터베이스

추가 지원이 필요한 경우 내부 개발팀에 문의하세요.