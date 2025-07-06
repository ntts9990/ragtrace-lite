# 🔧 RAGTrace Lite 폐쇄망 수동 설치 가이드

## 📋 개요
이 문서는 자동 설치 스크립트가 실패한 경우 RAGTrace Lite를 폐쇄망 윈도우 PC에서 **수동으로 설치**하는 상세한 방법을 제공합니다.

## 🎯 대상 환경
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.11.x
- **네트워크**: 폐쇄망 (인터넷 연결 없음)
- **권한**: 관리자 권한 (Python 설치 시)

---

## 📦 1단계: Python 3.11 설치

### 1.1 Python 설치 파일 확인
```cmd
# 패키지 디렉토리에서 확인
dir python-installer\python-3.11.*.exe
```

### 1.2 Python 설치 (관리자 권한 필요)
```cmd
# 방법 1: GUI 설치 (권장)
python-installer\python-3.11.x-amd64.exe

# 설치 옵션:
# ✅ Add Python to PATH
# ✅ Install for all users
# ✅ Associate files with Python
```

```cmd
# 방법 2: 명령줄 자동 설치
python-installer\python-3.11.x-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
```

### 1.3 Python 설치 확인
```cmd
# 새 명령 프롬프트 열기 (중요!)
python --version
# 출력 예: Python 3.11.x

python -m pip --version
# 출력 예: pip 23.x.x
```

**❗ 중요**: Python 설치 후 반드시 **새로운 명령 프롬프트**를 열어야 PATH 환경변수가 적용됩니다.

---

## 🏗️ 2단계: 가상환경 생성

### 2.1 프로젝트 디렉토리로 이동
```cmd
# RAGTrace Lite 압축 해제 후
cd ragtrace-lite-offline-YYYYMMDD-HHMMSS
```

### 2.2 가상환경 생성
```cmd
python -m venv venv
```

### 2.3 가상환경 활성화
```cmd
venv\Scripts\activate.bat

# 성공 시 프롬프트가 다음과 같이 변경됨:
# (venv) C:\path\to\ragtrace-lite>
```

### 2.4 pip 업그레이드
```cmd
python -m pip install --upgrade pip
```

---

## 📦 3단계: 의존성 패키지 설치

### 3.1 wheels 디렉토리 확인
```cmd
dir wheels\*.whl
# 50개 이상의 .whl 파일이 있어야 함
```

### 3.2 의존성 설치 (방법 1: 자동)
```cmd
python -m pip install --no-index --find-links wheels -r wheels\requirements.txt
```

### 3.3 의존성 설치 (방법 2: 개별 설치)
```cmd
# 핵심 패키지부터 순서대로 설치
python -m pip install --no-index --find-links wheels torch
python -m pip install --no-index --find-links wheels transformers
python -m pip install --no-index --find-links wheels sentence-transformers
python -m pip install --no-index --find-links wheels datasets
python -m pip install --no-index --find-links wheels pandas
python -m pip install --no-index --find-links wheels pydantic
python -m pip install --no-index --find-links wheels aiohttp
python -m pip install --no-index --find-links wheels langchain
python -m pip install --no-index --find-links wheels ragas

# 나머지 패키지 일괄 설치
for /f %i in ('dir /b wheels\*.whl') do python -m pip install --no-index --find-links wheels %~ni
```

### 3.4 설치 확인
```cmd
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import transformers; print('Transformers:', transformers.__version__)"
python -c "import sentence_transformers; print('SentenceTransformers OK')"
python -c "import datasets; print('Datasets OK')"
python -c "import ragas; print('RAGAS OK')"
```

---

## 🚀 4단계: RAGTrace Lite 설치

### 4.1 프로젝트 설치
```cmd
python -m pip install -e .
```

### 4.2 설치 확인
```cmd
python -c "import src.ragtrace_lite; print('RAGTrace Lite 설치 완료')"
```

---

## 📁 5단계: 디렉토리 구조 생성

### 5.1 필수 디렉토리 생성
```cmd
if not exist "db" mkdir db
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
if not exist "reports\web" mkdir reports\web
if not exist "reports\markdown" mkdir reports\markdown
```

### 5.2 디렉토리 확인
```cmd
tree /f
# 또는
dir
```

---

## ⚙️ 6단계: 환경 변수 설정

### 6.1 .env 파일 생성
```cmd
copy config\.env.template .env
```

### 6.2 .env 파일 편집
```cmd
notepad .env
```

### 6.3 .env 파일 내용 예시
```bash
# HCX API 설정 (폐쇄망 내부 엔드포인트)
CLOVA_STUDIO_API_KEY=nv-your-actual-api-key-here
HCX_API_ENDPOINT=https://your-internal-hcx-endpoint.com

# BGE-M3 모델 설정
BGE_M3_MODEL_PATH=./models/bge-m3
BGE_M3_DEVICE=auto

# 데이터베이스 설정
DATABASE_PATH=./db/ragtrace_lite.db

# 로그 설정
LOG_LEVEL=INFO
LOG_FILE=./logs/ragtrace.log
```

---

## 🤖 7단계: BGE-M3 모델 확인

### 7.1 모델 디렉토리 확인
```cmd
dir models\bge-m3
# 다음 파일들이 있어야 함:
# - config.json
# - pytorch_model.bin (또는 .safetensors)
# - tokenizer.json
# - vocab.txt
```

### 7.2 모델 로딩 테스트
```cmd
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('./models/bge-m3'); print('BGE-M3 모델 로딩 성공')"
```

**모델이 없는 경우**: 인터넷 연결된 환경에서 `python scripts/download_bge_m3.py`를 실행하고 `models/` 폴더를 복사해야 합니다.

---

## 🧪 8단계: 설치 테스트

### 8.1 기본 테스트
```cmd
python -c "
import sys
print('Python 버전:', sys.version)

import src.ragtrace_lite
print('✅ RAGTrace Lite 로딩 성공')

from pathlib import Path
if Path('models/bge-m3').exists():
    print('✅ BGE-M3 모델 확인됨')
else:
    print('⚠️  BGE-M3 모델 없음')

if Path('.env').exists():
    print('✅ .env 파일 확인됨')
else:
    print('⚠️  .env 파일 없음')
"
```

### 8.2 API 연결 테스트
```cmd
python -c "
from src.ragtrace_lite.llm_factory import create_llm
from src.ragtrace_lite.config_loader import load_config

config = load_config()
config.llm.provider = 'hcx'

try:
    llm = create_llm(config)
    print('✅ HCX LLM 생성 성공')
except Exception as e:
    print(f'❌ HCX LLM 생성 실패: {e}')
"
```

---

## 🚀 9단계: 평가 실행

### 9.1 샘플 데이터 확인
```cmd
dir data\input\*.json
# evaluation_data.json 또는 다른 JSON 파일이 있어야 함
```

### 9.2 평가 실행
```cmd
python -m src.ragtrace_lite.main --llm-provider hcx --llm-model HCX-005 --embedding-provider bge_m3 --data-file data\input\evaluation_data.json
```

### 9.3 결과 확인
```cmd
# 웹 대시보드 확인
start reports\web\dashboard.html

# 또는 탐색기에서 열기
explorer reports\web\dashboard.html

# 마크다운 보고서 확인
dir reports\markdown\*.md
```

---

## 🔧 문제 해결

### Python 관련 문제

#### Python이 인식되지 않는 경우
```cmd
# PATH 환경변수 확인
echo %PATH%

# Python 설치 경로 확인
where python

# 수동으로 PATH 추가 (시스템 속성 > 고급 > 환경 변수)
C:\Program Files\Python311\
C:\Program Files\Python311\Scripts\
```

#### 가상환경 활성화 실패
```cmd
# PowerShell 정책 확인 및 변경 (관리자 권한)
powershell
Get-ExecutionPolicy
Set-ExecutionPolicy RemoteSigned

# 다시 cmd에서 시도
venv\Scripts\activate.bat
```

### 패키지 설치 문제

#### 특정 패키지 설치 실패
```cmd
# 개별 패키지 강제 설치
python -m pip install --no-index --find-links wheels --force-reinstall torch

# 캐시 무시하고 재설치
python -m pip install --no-cache-dir --no-index --find-links wheels transformers
```

#### 의존성 충돌
```cmd
# 현재 설치된 패키지 확인
python -m pip list

# 특정 패키지 제거 후 재설치
python -m pip uninstall package-name
python -m pip install --no-index --find-links wheels package-name
```

### BGE-M3 모델 문제

#### 모델 로딩 실패
```cmd
# 모델 파일 무결성 확인
dir models\bge-m3\*.bin
dir models\bge-m3\*.json

# 메모리 부족 시 디바이스 변경
# .env 파일에서 BGE_M3_DEVICE=cpu로 설정
```

#### 모델 경로 문제
```cmd
# 절대 경로로 테스트
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('C:\\full\\path\\to\\models\\bge-m3')"
```

### HCX API 문제

#### API 연결 실패
```cmd
# 환경 변수 확인
python -c "import os; print('API Key:', os.getenv('CLOVA_STUDIO_API_KEY')[:10] + '...' if os.getenv('CLOVA_STUDIO_API_KEY') else 'None')"

# 엔드포인트 확인
ping your-internal-hcx-endpoint.com
telnet your-internal-hcx-endpoint.com 443
```

#### 방화벽 문제
- 회사 IT 부서에 내부 API 엔드포인트 접근 권한 확인 요청
- Windows 방화벽에서 Python.exe 허용 확인

### 일반적인 오류

#### 모듈을 찾을 수 없음
```cmd
# Python 경로 확인
python -c "import sys; print('\n'.join(sys.path))"

# 현재 디렉토리에서 실행하는지 확인
cd ragtrace-lite-offline-YYYYMMDD-HHMMSS
python -m src.ragtrace_lite.main --help
```

#### 권한 오류
```cmd
# 관리자 권한으로 명령 프롬프트 실행
# 또는 사용자 권한으로 가상환경에서만 실행
```

---

## 📞 추가 지원

### 로그 파일 확인
```cmd
# 설치 중 오류 발생 시
type logs\install.log

# 실행 중 오류 발생 시
type logs\ragtrace.log
```

### 시스템 정보 수집
```cmd
# 문제 보고 시 다음 정보 수집
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
python --version
python -m pip --version
echo %PATH%
dir wheels | find /c ".whl"
dir models\bge-m3 | find /c "File(s)"
```

### 긴급 복구 방법
```cmd
# 가상환경 완전 재생성
rmdir /s venv
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip

# 최소한의 패키지만 설치하여 문제 격리
python -m pip install --no-index --find-links wheels torch
python -m pip install --no-index --find-links wheels transformers
python -m pip install --no-index --find-links wheels sentence-transformers
```

---

## 📋 설치 완료 체크리스트

설치가 완료되면 다음 항목들을 모두 확인하세요:

- [ ] Python 3.11.x 설치 완료 (`python --version`)
- [ ] 가상환경 생성 및 활성화 완료 (`(venv)` 프롬프트 확인)
- [ ] 모든 의존성 패키지 설치 완료 (`python -m pip list`)
- [ ] RAGTrace Lite 설치 완료 (`import src.ragtrace_lite`)
- [ ] 필수 디렉토리 생성 완료 (`db/`, `logs/`, `reports/`)
- [ ] .env 파일 생성 및 API 키 설정 완료
- [ ] BGE-M3 모델 확인 완료 (`models/bge-m3/`)
- [ ] HCX API 연결 테스트 성공
- [ ] 샘플 평가 실행 성공
- [ ] 웹 대시보드 생성 확인 (`reports/web/dashboard.html`)

모든 항목이 체크되면 폐쇄망에서 RAGTrace Lite를 성공적으로 사용할 수 있습니다! 🎉