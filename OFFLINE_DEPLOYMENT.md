# 🔒 RAGTrace Lite 폐쇄망 윈도우 배포 가이드

## 📋 개요
이 가이드는 RAGTrace Lite를 폐쇄망 윈도우 PC에서 실행하기 위한 완전한 준비 과정을 설명합니다.

## 🎯 배포 환경
- **타겟 OS**: Windows 10/11
- **Python**: 3.9 이상 (권장: 3.11.x)
- **네트워크**: 폐쇄망 (인터넷 연결 없음)
- **LLM**: HCX-005 (Naver CLOVA Studio API)
- **임베딩**: BGE-M3 (로컬 모델)

## 📦 사전 준비 (인터넷 연결된 Windows PC에서)

### 1. 준비 환경 설정

#### Python 설치
```powershell
# Python 3.11 설치 (아직 없는 경우)
# https://www.python.org/downloads/windows/ 에서 다운로드
# 설치 시 "Add Python to PATH" 체크 필수
```

#### uv 설치 (선택사항, 권장)
```powershell
# PowerShell 관리자 권한으로 실행
# uv 설치 (빠른 패키지 관리자)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 또는 pip로 설치
pip install uv
```

### 2. 작업 디렉토리 준비
```powershell
# 오프라인 패키지 준비용 디렉토리 생성
mkdir C:\ragtrace-offline-prep
cd C:\ragtrace-offline-prep

# Git 클론 또는 소스코드 다운로드
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite
```

### 3. Python 설치 파일 다운로드
```powershell
# Python 3.11 Windows 설치 파일 다운로드 스크립트 실행
python scripts/download_python_installer.py

# 또는 수동 다운로드
# https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
# python-installer 폴더에 저장
```

### 4. 의존성 패키지 다운로드

#### 방법 1: uv 사용 (권장)
```powershell
# uv로 모든 의존성 다운로드
uv pip download -r requirements-offline.txt --dest wheels --python 3.11 --platform windows

# ragtrace-lite 패키지와 extras 다운로드
uv pip download ragtrace-lite[all] --dest wheels --python 3.11 --platform windows --no-deps
```

#### 방법 2: pip 사용
```powershell
# pip로 모든 의존성 다운로드
pip download -r requirements-offline.txt -d wheels `
    --platform win_amd64 `
    --python-version 311 `
    --implementation cp `
    --abi cp311 `
    --only-binary=:all:

# ragtrace-lite 패키지 다운로드
pip download ragtrace-lite[all] -d wheels --no-deps
```

### 5. BGE-M3 모델 사전 다운로드
```powershell
# BGE-M3 모델 다운로드 (약 2.3GB)
python scripts/download_bge_m3.py

# 다운로드 확인
dir models\bge-m3
```

### 6. 추가 필수 파일 준비
```powershell
# requirements 파일 생성 (설치 순서 보장)
pip freeze > wheels\requirements-install.txt

# 설정 파일 템플릿 복사
copy .env.example offline-package\.env.example
copy config.yaml offline-package\config.yaml
```

### 7. 오프라인 패키지 생성
```powershell
# 자동 패키징 스크립트 실행
python scripts/prepare_offline_deployment.py

# 또는 수동으로 압축
# 다음 항목들을 포함:
# - python-installer/
# - wheels/
# - models/bge-m3/
# - src/
# - scripts/
# - config files
# - batch files
```

### 8. 패키지 검증
```powershell
# 다운로드된 wheel 파일 확인
dir wheels\*.whl | measure-object

# 필수 패키지 확인
dir wheels\ragtrace_lite*.whl
dir wheels\torch*.whl
dir wheels\transformers*.whl
dir wheels\sentence_transformers*.whl

# 전체 패키지 크기 확인
# 예상 크기: 약 3-4GB (BGE-M3 모델 포함)
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
├── config.yaml
├── .env.example
└── README_OFFLINE.md
```

## ⚠️ 준비 과정 중 주의사항

### 흔한 문제와 해결방법

1. **wheel 다운로드 실패**
   ```powershell
   # 특정 패키지가 실패하는 경우
   # 개별적으로 다시 시도
   pip download torch --dest wheels --platform win_amd64 --only-binary=:all:
   ```

2. **플랫폼 불일치 문제**
   ```powershell
   # Windows 32bit/64bit 확인
   python -c "import platform; print(platform.machine())"
   
   # 32bit 시스템인 경우
   pip download -r requirements-offline.txt -d wheels --platform win32
   ```

3. **BGE-M3 다운로드 속도 문제**
   ```powershell
   # Hugging Face 미러 사용 (중국 등)
   set HF_ENDPOINT=https://hf-mirror.com
   python scripts/download_bge_m3.py
   ```

4. **디스크 공간 부족**
   - 최소 10GB 여유 공간 필요
   - wheels: 약 2GB
   - BGE-M3 모델: 약 2.3GB
   - 작업 공간: 약 3GB

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
copy .env.example .env
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
# HCX API 설정
CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key-here

# BGE-M3 모델 경로 (로컬)
BGE_M3_MODEL_PATH=./models/bge-m3
# BGE_M3_DEVICE=auto  # 자동 감지 (주석 처리됨)

# 데이터베이스 설정
DATABASE_PATH=./data/ragtrace_lite.db

# 로그 설정
LOG_LEVEL=INFO

# 평가 설정
EVALUATION_BATCH_SIZE=1
REQUEST_TIMEOUT=60
MAX_RETRIES=3

# 보고서 출력 디렉토리
REPORT_DIR=./reports
```

## 🔧 주요 스크립트

### install.bat (업데이트된 버전)
```batch
@echo off
echo RAGTrace Lite 폐쇄망 설치 시작...

echo [1/5] Python 버전 확인
python --version
if errorlevel 1 (
    echo Python이 설치되지 않았습니다!
    echo python-installer 폴더의 설치 파일을 실행하세요.
    pause
    exit /b 1
)

echo [2/5] Python 가상환경 생성
python -m venv venv
call venv\Scripts\activate.bat

echo [3/5] pip 업그레이드 (오프라인)
python -m pip install --no-index --find-links wheels pip setuptools wheel

echo [4/5] 의존성 패키지 설치
python -m pip install --no-index --find-links wheels -r requirements-offline.txt

echo [5/5] RAGTrace Lite 설치
REM PyPI에서 다운로드한 wheel이 있는 경우
if exist wheels\ragtrace_lite*.whl (
    python -m pip install --no-index --find-links wheels ragtrace-lite[all]
) else (
    REM 소스코드에서 설치
    python -m pip install --no-index --find-links wheels -e ".[all]"
)

echo [6/6] 디렉토리 구조 생성
if not exist data mkdir data
if not exist db mkdir db  
if not exist logs mkdir logs
if not exist reports\web mkdir reports\web
if not exist reports\markdown mkdir reports\markdown
if not exist models\bge-m3 mkdir models\bge-m3

echo.
echo ========================================
echo 설치가 완료되었습니다!
echo.
echo 다음 단계:
echo 1. .env 파일에 API 키를 설정하세요
echo    copy .env.example .env
echo    notepad .env
echo.
echo 2. 테스트 실행
echo    call run_evaluation.bat
echo ========================================
pause
```

### run_evaluation.bat
```batch
@echo off
call venv\Scripts\activate.bat

echo RAGTrace Lite 평가 실행...
ragtrace-lite evaluate data\input\evaluation_data.json --llm hcx

echo 평가 완료!
echo 결과: reports\web\dashboard.html 확인

echo.
echo 웹 대시보드 생성...
ragtrace-lite dashboard --open

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
   - CLOVA Studio API 키 유효성 확인
   - 네트워크 방화벽 설정 확인
   - 폐쇄망 내부에서 CLOVA Studio API 접근 가능 여부 확인

## 📊 성능 고려사항

### 시스템 요구사항
- **RAM**: 최소 8GB, 권장 16GB
- **디스크**: 최소 5GB 여유 공간
- **CPU**: BGE-M3 모델 실행을 위한 멀티코어 권장

### 최적화 설정
```yaml
# config.yaml
llm:
  provider: hcx
  model_name: HCX-005
  
embedding:
  provider: bge_m3
  model_name: BAAI/bge-m3
  device: auto    # auto/cpu/cuda 선택
  
evaluation:
  batch_size: 1  # HCX API 속도 제한으로 인해 1로 설정
  show_progress: true
  raise_exceptions: false
  timeout: 300    # API 타임아웃 (초)
  
results:
  output_path: ./reports
  formats: ["json", "csv", "markdown", "web"]
```

## 🔒 보안 고려사항

1. **API 키 보안**
   - .env 파일 권한 설정
   - 로그에 API 키 노출 방지

2. **모델 파일 보안**
   - 모델 파일 무결성 검증
   - 접근 권한 제한

3. **네트워크 보안**
   - CLOVA Studio API 접근을 위한 네트워크 설정
   - HTTPS 통신 보안

## 📝 체크리스트

### 배포 전 확인사항
- [ ] Python 3.9 이상 설치 파일 준비 (권장: 3.11)
- [ ] 모든 wheel 패키지 다운로드 완료
- [ ] BGE-M3 모델 사전 다운로드 완료
- [ ] 설치 스크립트 테스트 완료
- [ ] CLOVA Studio API 키 준비
- [ ] 샘플 데이터 준비

### 설치 후 확인사항
- [ ] Python 정상 설치 (3.9 이상)
- [ ] 가상환경 생성 완료
- [ ] 모든 의존성 설치 완료
- [ ] BGE-M3 모델 로딩 성공
- [ ] CLOVA Studio API 연결 성공
- [ ] 샘플 평가 실행 성공
- [ ] 웹 대시보드 생성 확인

## 📞 지원

문제 발생 시 다음 로그 파일을 확인하세요:
- `logs/ragtrace.log`: 애플리케이션 로그
- `logs/install.log`: 설치 과정 로그
- `data/ragtrace_lite.db`: 평가 결과 데이터베이스

추가 지원이 필요한 경우:
- GitHub Issues: https://github.com/ntts9990/ragtrace-lite/issues
- Email: ntts9990@gmail.com

## 📌 빠른 참조

### 온라인 환경에서 준비 (Windows)
```powershell
# 1. 프로젝트 클론
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite

# 2. 오프라인 패키지 준비
python scripts/prepare_offline_deployment.py
```

### 오프라인 환경에서 설치
```cmd
# 1. 패키지 압축 해제
# 2. 설치 실행
scripts\install.bat

# 3. API 키 설정
copy .env.example .env
notepad .env

# 4. 실행
scripts\run_evaluation.bat
```

### PyPI에서 직접 설치 (인터넷 연결 시)
```bash
# 일반 설치
pip install ragtrace-lite[all]

# API 키 설정
echo CLOVA_STUDIO_API_KEY=your-key > .env

# 실행
ragtrace-lite evaluate sample.json --llm hcx
```