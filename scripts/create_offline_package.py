#!/usr/bin/env python3
"""
폐쇄망 배포 패키지 생성 스크립트
모든 의존성과 필요한 파일들을 하나의 배포 패키지로 만듭니다.
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

class OfflinePackageCreator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.package_name = f"ragtrace-lite-offline-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.package_dir = self.project_root / "dist" / self.package_name
        
    def create_package(self):
        """폐쇄망 배포 패키지를 생성합니다."""
        print("🚀 RAGTrace Lite 폐쇄망 배포 패키지 생성 시작...")
        print(f"📦 패키지명: {self.package_name}")
        print(f"📁 생성 위치: {self.package_dir}")
        
        # 패키지 디렉토리 생성
        self.package_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. 의존성 다운로드
            self._download_dependencies()
            
            # 2. 소스 코드 복사
            self._copy_source_code()
            
            # 3. 모델 파일 복사
            self._copy_models()
            
            # 4. 설정 파일 복사
            self._copy_config_files()
            
            # 5. 스크립트 생성
            self._create_scripts()
            
            # 6. 문서 복사
            self._copy_documentation()
            
            # 7. 샘플 데이터 복사
            self._copy_sample_data()
            
            # 8. 패키지 압축
            zip_file = self._create_zip_package()
            
            print(f"\n🎉 폐쇄망 배포 패키지 생성 완료!")
            print(f"📦 패키지 파일: {zip_file}")
            print(f"📊 패키지 크기: {self._get_file_size(zip_file):.1f} MB")
            
            # 패키지 내용 요약
            self._print_package_summary()
            
            return zip_file
            
        except Exception as e:
            print(f"❌ 패키지 생성 실패: {e}")
            return None
    
    def _download_dependencies(self):
        """의존성 패키지를 다운로드합니다."""
        print("\n📦 [1/8] 의존성 패키지 다운로드 중...")
        
        wheels_dir = self.package_dir / "wheels"
        wheels_dir.mkdir(exist_ok=True)
        
        # requirements.txt에서 패키지 목록 읽기
        requirements_file = self.project_root / "requirements-full.txt"
        if not requirements_file.exists():
            print("⚠️  requirements-full.txt가 없어 현재 환경에서 생성합니다...")
            self._create_requirements_file()
        
        # Windows용 wheel 패키지 다운로드
        cmd = [
            sys.executable, "-m", "pip", "download",
            "-r", str(requirements_file),
            "-d", str(wheels_dir),
            "--platform", "win_amd64",
            "--python-version", "3.11",
            "--abi", "cp311",
            "--only-binary=:all:",
            "--no-deps"  # 의존성은 별도로 처리
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ 의존성 다운로드 완료: {len(list(wheels_dir.glob('*.whl')))}개 패키지")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  일부 패키지 다운로드 실패, 계속 진행합니다: {e}")
        
        # 간단한 requirements.txt 생성
        simple_requirements = wheels_dir / "requirements.txt"
        with open(simple_requirements, 'w') as f:
            f.write("# RAGTrace Lite 의존성\\n")
            f.write("# pip install -r requirements.txt\\n\\n")
            for wheel in wheels_dir.glob("*.whl"):
                f.write(f"{wheel.name}\\n")
    
    def _create_requirements_file(self):
        """현재 환경에서 requirements.txt를 생성합니다."""
        requirements_file = self.project_root / "requirements-full.txt"
        cmd = [sys.executable, "-m", "pip", "freeze"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            with open(requirements_file, 'w') as f:
                f.write(result.stdout)
            print(f"✅ requirements-full.txt 생성 완료")
        except subprocess.CalledProcessError as e:
            print(f"❌ requirements.txt 생성 실패: {e}")
    
    def _copy_source_code(self):
        """소스 코드를 복사합니다."""
        print("\n📂 [2/8] 소스 코드 복사 중...")
        
        # 소스 코드 복사
        src_dirs = ["src", "pyproject.toml"]
        for item in src_dirs:
            src_path = self.project_root / item
            if src_path.exists():
                if src_path.is_dir():
                    dst_path = self.package_dir / item
                    shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                else:
                    shutil.copy2(src_path, self.package_dir / item)
                print(f"✅ 복사 완료: {item}")
    
    def _copy_models(self):
        """BGE-M3 모델 파일을 복사합니다."""
        print("\n🤖 [3/8] BGE-M3 모델 복사 중...")
        
        models_src = self.project_root / "models"
        if models_src.exists():
            models_dst = self.package_dir / "models"
            shutil.copytree(models_src, models_dst)
            
            model_size = self._get_folder_size(models_dst)
            print(f"✅ BGE-M3 모델 복사 완료: {model_size:.1f} MB")
        else:
            print("⚠️  BGE-M3 모델이 없습니다. download_bge_m3.py를 먼저 실행하세요.")
            
            # 빈 모델 디렉토리와 README 생성
            models_dst = self.package_dir / "models"
            models_dst.mkdir(exist_ok=True)
            
            readme_content = """# BGE-M3 Model Directory

이 디렉토리는 BGE-M3 모델 파일을 위한 것입니다.

## 모델 다운로드 방법

폐쇄망 배포 전에 인터넷이 연결된 환경에서 다음 명령을 실행하세요:

```bash
python scripts/download_bge_m3.py
```

이 명령은 BAAI/bge-m3 모델을 이 디렉토리에 다운로드합니다.

## 모델 정보
- **모델명**: BAAI/bge-m3
- **크기**: 약 2.3GB
- **라이선스**: MIT
- **용도**: 다국어 임베딩 모델
"""
            
            with open(models_dst / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
    
    def _copy_config_files(self):
        """설정 파일들을 복사합니다."""
        print("\n⚙️  [4/8] 설정 파일 복사 중...")
        
        config_dir = self.package_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # config.yaml 복사
        config_files = ["config.yaml"]
        for config_file in config_files:
            src_path = self.project_root / config_file
            if src_path.exists():
                shutil.copy2(src_path, config_dir / config_file)
                print(f"✅ 복사: {config_file}")
        
        # .env 템플릿 생성
        env_template = config_dir / ".env.template"
        env_content = """# RAGTrace Lite 환경 변수 설정

# HCX API 설정 (폐쇄망 내부 엔드포인트)
CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key-here
HCX_API_ENDPOINT=https://your-internal-hcx-endpoint.com

# BGE-M3 모델 설정
BGE_M3_MODEL_PATH=./models/bge-m3
BGE_M3_DEVICE=auto

# 데이터베이스 설정
DATABASE_PATH=./db/ragtrace_lite.db

# 로그 설정
LOG_LEVEL=INFO
LOG_FILE=./logs/ragtrace.log

# 평가 설정
EVALUATION_BATCH_SIZE=1
EVALUATION_TIMEOUT=300
"""
        
        with open(env_template, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env.template 생성 완료")
    
    def _create_scripts(self):
        """Windows 설치 및 실행 스크립트를 생성합니다."""
        print("\n📜 [5/8] Windows 스크립트 생성 중...")
        
        scripts_dir = self.package_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # install.bat
        install_script = """@echo off
chcp 65001 > nul 2>&1
setlocal enabledelayedexpansion

echo =========================================
echo RAGTrace Lite 폐쇄망 설치 스크립트
echo =========================================
echo.

REM 로그 파일 초기화
if not exist "logs" mkdir logs
echo [%date% %time%] 설치 시작 > logs\\install.log

REM Python 설치 확인
echo [1/7] Python 설치 확인 중...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았거나 PATH에 없습니다!
    echo.
    echo 해결 방법:
    echo 1. python-installer\\python-3.11.x-amd64.exe를 실행하여 Python 설치
    echo 2. 설치 시 "Add Python to PATH" 옵션 체크
    echo 3. 새 명령 프롬프트에서 다시 실행
    echo.
    echo [%date% %time%] Python 없음 - 설치 중단 >> logs\\install.log
    pause
    exit /b 1
)

python --version
echo [%date% %time%] Python 확인 완료 >> logs\\install.log

REM 기존 가상환경 확인 및 삭제
echo [2/7] 기존 가상환경 확인 중...
if exist "venv" (
    echo 기존 가상환경 발견. 삭제 중...
    rmdir /s /q venv
    echo [%date% %time%] 기존 venv 삭제 >> logs\\install.log
)

REM 가상환경 생성
echo [3/7] Python 가상환경 생성 중...
python -m venv venv >> logs\\install.log 2>&1
if errorlevel 1 (
    echo ❌ Python 가상환경 생성 실패!
    echo 로그 파일을 확인하세요: logs\\install.log
    echo.
    echo 수동 해결 방법:
    echo 1. python -m ensurepip --upgrade
    echo 2. python -m pip install --upgrade pip
    echo 3. MANUAL_INSTALLATION_GUIDE.md 참조
    echo.
    pause
    exit /b 1
)
echo [%date% %time%] 가상환경 생성 완료 >> logs\\install.log

REM 가상환경 활성화 확인
echo [4/7] 가상환경 활성화 중...
if not exist "venv\\Scripts\\activate.bat" (
    echo ❌ 가상환경 활성화 스크립트를 찾을 수 없습니다!
    echo venv\\Scripts\\activate.bat가 없습니다.
    echo MANUAL_INSTALLATION_GUIDE.md를 참조하여 수동 설치하세요.
    pause
    exit /b 1
)

call venv\\Scripts\\activate.bat
echo [%date% %time%] 가상환경 활성화 완료 >> logs\\install.log

REM pip 업그레이드
echo [5/7] pip 업그레이드 중...
python -m pip install --upgrade pip >> logs\\install.log 2>&1
if errorlevel 1 (
    echo ⚠️  pip 업그레이드 실패. 기존 버전으로 계속 진행합니다.
    echo [%date% %time%] pip 업그레이드 실패 >> logs\\install.log
) else (
    echo [%date% %time%] pip 업그레이드 완료 >> logs\\install.log
)

REM wheels 디렉토리 확인
echo [6/7] 의존성 패키지 확인 중...
if not exist "wheels" (
    echo ❌ wheels 디렉토리가 없습니다!
    echo 패키지가 올바르게 압축 해제되었는지 확인하세요.
    pause
    exit /b 1
)

REM .whl 파일 개수 확인
set wheel_count=0
for %%f in (wheels\\*.whl) do set /a wheel_count+=1
if %wheel_count% LSS 10 (
    echo ❌ wheels 디렉토리에 충분한 패키지가 없습니다! (발견: %wheel_count%개)
    echo 패키지가 올바르게 준비되었는지 확인하세요.
    pause
    exit /b 1
)

echo 발견된 wheel 패키지: %wheel_count%개
echo [%date% %time%] wheel 패키지 확인: %wheel_count%개 >> logs\\install.log

REM 의존성 설치
echo.
echo 의존성 패키지 설치 중... (시간이 걸릴 수 있습니다)
if exist "wheels\\requirements.txt" (
    python -m pip install --no-index --find-links wheels -r wheels\\requirements.txt >> logs\\install.log 2>&1
) else (
    echo requirements.txt가 없어 개별 설치를 시도합니다...
    REM 핵심 패키지 우선 설치
    python -m pip install --no-index --find-links wheels torch >> logs\\install.log 2>&1
    python -m pip install --no-index --find-links wheels transformers >> logs\\install.log 2>&1
    python -m pip install --no-index --find-links wheels sentence-transformers >> logs\\install.log 2>&1
    python -m pip install --no-index --find-links wheels ragas >> logs\\install.log 2>&1
)

if errorlevel 1 (
    echo ⚠️  일부 패키지 설치에 실패했습니다.
    echo 로그 파일을 확인하세요: logs\\install.log
    echo.
    echo 계속 진행하려면 아무 키나 누르세요...
    pause > nul
    echo [%date% %time%] 의존성 설치 일부 실패 >> logs\\install.log
) else (
    echo [%date% %time%] 의존성 설치 완료 >> logs\\install.log
)

REM RAGTrace Lite 설치
echo [7/7] RAGTrace Lite 설치 중...
if exist "pyproject.toml" (
    python -m pip install -e . >> logs\\install.log 2>&1
) else (
    echo ⚠️  pyproject.toml이 없습니다. src 디렉토리만 사용합니다.
)

if errorlevel 1 (
    echo ⚠️  RAGTrace Lite 설치에 실패했지만 계속 진행합니다.
    echo [%date% %time%] RAGTrace Lite 설치 실패 >> logs\\install.log
) else (
    echo [%date% %time%] RAGTrace Lite 설치 완료 >> logs\\install.log
)

REM 필수 디렉토리 생성
echo.
echo 📁 필요한 디렉토리 생성 중...
if not exist "db" mkdir db
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
if not exist "reports\\web" mkdir reports\\web
if not exist "reports\\markdown" mkdir reports\\markdown
echo [%date% %time%] 디렉토리 생성 완료 >> logs\\install.log

REM 설치 확인 테스트
echo.
echo 🧪 설치 확인 테스트 중...
python -c "import sys; print('Python:', sys.version.split()[0])" >> logs\\install.log 2>&1
python -c "import src.ragtrace_lite; print('RAGTrace Lite 설치 확인됨')" >> logs\\install.log 2>&1
if errorlevel 1 (
    echo ⚠️  RAGTrace Lite 로딩 테스트 실패
    echo MANUAL_INSTALLATION_GUIDE.md를 참조하여 문제를 해결하세요.
    echo [%date% %time%] 로딩 테스트 실패 >> logs\\install.log
) else (
    echo ✅ RAGTrace Lite 로딩 테스트 성공
    echo [%date% %time%] 로딩 테스트 성공 >> logs\\install.log
)

REM BGE-M3 모델 확인
if exist "models\\bge-m3" (
    echo ✅ BGE-M3 모델 발견
    echo [%date% %time%] BGE-M3 모델 확인됨 >> logs\\install.log
) else (
    echo ⚠️  BGE-M3 모델이 없습니다
    echo 사전에 download_bge_m3.py를 실행했는지 확인하세요.
    echo [%date% %time%] BGE-M3 모델 없음 >> logs\\install.log
)

echo.
echo ========================================
echo ✅ 설치 완료!
echo ========================================
echo.
echo 📋 다음 단계:
echo 1. config\\.env.template을 복사하여 .env 파일 생성:
echo    copy config\\.env.template .env
echo.
echo 2. .env 파일을 편집하여 HCX API 키 설정:
echo    notepad .env
echo.
echo 3. 평가 실행:
echo    scripts\\run_evaluation.bat
echo.
echo 4. 문제가 있는 경우:
echo    - logs\\install.log 확인
echo    - MANUAL_INSTALLATION_GUIDE.md 참조
echo    - scripts\\test_installation.bat 실행
echo.
echo [%date% %time%] 설치 스크립트 완료 >> logs\\install.log
pause
"""
        
        with open(scripts_dir / "install.bat", 'w', encoding='utf-8') as f:
            f.write(install_script)
        
        # run_evaluation.bat
        run_script = """@echo off
chcp 65001 > nul 2>&1
setlocal enabledelayedexpansion

echo =========================================
echo RAGTrace Lite 평가 실행
echo =========================================
echo.

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs
echo [%date% %time%] 평가 시작 > logs\\evaluation.log

REM 가상환경 확인
echo [1/6] 가상환경 확인 중...
if not exist "venv\\Scripts\\activate.bat" (
    echo ❌ 가상환경이 없습니다!
    echo.
    echo 해결 방법:
    echo 1. scripts\\install.bat을 먼저 실행하세요
    echo 2. 또는 MANUAL_INSTALLATION_GUIDE.md를 참조하여 수동 설치하세요
    echo.
    echo [%date% %time%] 가상환경 없음 >> logs\\evaluation.log
    pause
    exit /b 1
)

REM 가상환경 활성화
echo [2/6] 가상환경 활성화 중...
call venv\\Scripts\\activate.bat
echo [%date% %time%] 가상환경 활성화 >> logs\\evaluation.log

REM .env 파일 확인
echo [3/6] 환경 설정 확인 중...
if not exist ".env" (
    echo ❌ .env 파일이 없습니다!
    echo.
    echo 해결 방법:
    echo 1. copy config\\.env.template .env
    echo 2. notepad .env
    echo 3. HCX API 키를 설정하세요
    echo.
    echo [%date% %time%] .env 파일 없음 >> logs\\evaluation.log
    pause
    exit /b 1
)

REM BGE-M3 모델 확인
echo [4/6] BGE-M3 모델 확인 중...
if not exist "models\\bge-m3" (
    echo ⚠️  BGE-M3 모델이 없습니다!
    echo 사전에 download_bge_m3.py를 실행했는지 확인하세요.
    echo 계속 진행하면 OpenAI 임베딩을 사용합니다.
    echo.
    echo 계속하시겠습니까? (Y/N):
    set /p continue=
    if /i "!continue!" NEQ "Y" (
        echo 중단됨.
        pause
        exit /b 1
    )
    echo [%date% %time%] BGE-M3 모델 없음, OpenAI 사용 >> logs\\evaluation.log
) else (
    echo ✅ BGE-M3 모델 발견
    echo [%date% %time%] BGE-M3 모델 확인됨 >> logs\\evaluation.log
)

REM 데이터 파일 확인
echo [5/6] 입력 데이터 확인 중...
set data_file=data\\input\\evaluation_data.json
if not exist "!data_file!" (
    echo ⚠️  기본 데이터 파일이 없습니다: !data_file!
    echo.
    echo 사용 가능한 데이터 파일:
    if exist "data\\input" (
        dir /b data\\input\\*.json 2>nul
        if errorlevel 1 (
            echo   (JSON 파일이 없습니다)
        )
    ) else (
        echo   (data\\input 디렉토리가 없습니다)
    )
    echo.
    echo 데이터 파일 경로를 입력하세요 (Enter: 기본값 사용):
    set /p user_data_file=
    if not "!user_data_file!"=="" (
        if exist "!user_data_file!" (
            set data_file=!user_data_file!
            echo 사용자 지정 파일: !data_file!
        ) else (
            echo ❌ 파일을 찾을 수 없습니다: !user_data_file!
            pause
            exit /b 1
        )
    )
)

echo 사용할 데이터 파일: !data_file!
echo [%date% %time%] 데이터 파일: !data_file! >> logs\\evaluation.log

REM HCX API 연결 테스트
echo [6/6] HCX API 연결 테스트 중...
python -c "
from src.ragtrace_lite.config_loader import load_config
from src.ragtrace_lite.llm_factory import create_llm, check_llm_connection
import os

try:
    config = load_config()
    config.llm.provider = 'hcx'
    
    api_key = os.getenv('CLOVA_STUDIO_API_KEY')
    if not api_key:
        print('❌ HCX API 키가 설정되지 않았습니다')
        exit(1)
    elif not api_key.startswith('nv-'):
        print('❌ HCX API 키 형식이 올바르지 않습니다 (nv-로 시작해야 함)')
        exit(1)
    else:
        print('✅ HCX API 키 형식 확인')
    
    # LLM 생성 테스트
    llm = create_llm(config)
    print('✅ HCX LLM 어댑터 생성 성공')
    
except Exception as e:
    print(f'❌ HCX 설정 오류: {e}')
    exit(1)
" >> logs\\evaluation.log 2>&1

if errorlevel 1 (
    echo ❌ HCX API 설정에 문제가 있습니다!
    echo.
    echo 해결 방법:
    echo 1. .env 파일에서 CLOVA_STUDIO_API_KEY 확인
    echo 2. API 키가 nv-로 시작하는지 확인
    echo 3. 폐쇄망 내부 API 엔드포인트 접근 가능한지 확인
    echo 4. logs\\evaluation.log 파일 확인
    echo.
    echo [%date% %time%] HCX API 설정 오류 >> logs\\evaluation.log
    pause
    exit /b 1
)

echo ✅ HCX API 연결 테스트 성공
echo [%date% %time%] HCX API 연결 성공 >> logs\\evaluation.log

REM 평가 실행
echo.
echo ========================================
echo 📊 평가 실행 시작
echo ========================================
echo.
echo 데이터 파일: !data_file!
echo LLM: HCX-005
echo 임베딩: BGE-M3 (또는 OpenAI)
echo.
echo 평가 중... (시간이 걸릴 수 있습니다)
echo.

python -m src.ragtrace_lite.main --llm-provider hcx --llm-model HCX-005 --embedding-provider bge_m3 --data-file "!data_file!" >> logs\\evaluation.log 2>&1

echo.
if errorlevel 1 (
    echo ========================================
    echo ❌ 평가 실행 실패!
    echo ========================================
    echo.
    echo 문제 해결:
    echo 1. 로그 파일 확인: logs\\evaluation.log
    echo 2. 로그 파일 확인: logs\\ragtrace.log
    echo 3. API 키 및 네트워크 연결 확인
    echo 4. BGE-M3 모델 파일 확인: models\\bge-m3\\
    echo 5. MANUAL_INSTALLATION_GUIDE.md 참조
    echo.
    echo [%date% %time%] 평가 실행 실패 >> logs\\evaluation.log
) else (
    echo ========================================
    echo ✅ 평가 완료!
    echo ========================================
    echo.
    echo 📊 결과 확인:
    echo 1. 웹 대시보드: reports\\web\\dashboard.html
    echo 2. 상세 보고서: reports\\markdown\\
    echo 3. 데이터베이스: db\\ragtrace_lite.db
    echo.
    echo 웹 대시보드 열기 (Y/N)?
    set /p open_dashboard=
    if /i "!open_dashboard!"=="Y" (
        if exist "reports\\web\\dashboard.html" (
            start reports\\web\\dashboard.html
        ) else (
            echo ⚠️  대시보드 파일을 찾을 수 없습니다.
        )
    )
    echo.
    echo [%date% %time%] 평가 완료 >> logs\\evaluation.log
)

echo.
pause
"""
        
        with open(scripts_dir / "run_evaluation.bat", 'w', encoding='utf-8') as f:
            f.write(run_script)
        
        # test_installation.bat
        test_script = """@echo off
chcp 65001 > nul 2>&1
setlocal enabledelayedexpansion

echo =========================================
echo RAGTrace Lite 설치 테스트
echo =========================================
echo.

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs
echo [%date% %time%] 설치 테스트 시작 > logs\\test.log

REM 테스트 결과 변수
set test_count=0
set pass_count=0

REM 테스트 1: 가상환경 확인
echo [테스트 1/10] 가상환경 확인...
set /a test_count+=1
if exist "venv\\Scripts\\activate.bat" (
    echo ✅ 가상환경 존재
    set /a pass_count+=1
    echo [%date% %time%] 가상환경 존재 >> logs\\test.log
) else (
    echo ❌ 가상환경 없음
    echo [%date% %time%] 가상환경 없음 >> logs\\test.log
)

REM 가상환경 활성화
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
)

REM 테스트 2: Python 버전 확인
echo [테스트 2/10] Python 버전 확인...
set /a test_count+=1
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python 실행 실패
    echo [%date% %time%] Python 실행 실패 >> logs\\test.log
) else (
    python --version
    echo ✅ Python 실행 성공
    set /a pass_count+=1
    echo [%date% %time%] Python 실행 성공 >> logs\\test.log
)

REM 테스트 3: pip 확인
echo [테스트 3/10] pip 확인...
set /a test_count+=1
python -m pip --version > nul 2>&1
if errorlevel 1 (
    echo ❌ pip 실행 실패
    echo [%date% %time%] pip 실행 실패 >> logs\\test.log
) else (
    python -m pip --version
    echo ✅ pip 실행 성공
    set /a pass_count+=1
    echo [%date% %time%] pip 실행 성공 >> logs\\test.log
)

REM 테스트 4: 핵심 패키지 확인
echo [테스트 4/10] 핵심 패키지 확인...
set /a test_count+=1
python -c "
packages = ['torch', 'transformers', 'sentence_transformers', 'datasets', 'pandas', 'ragas']
failed = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✅ {pkg}')
    except ImportError:
        print(f'  ❌ {pkg}')
        failed.append(pkg)

if failed:
    print(f'실패한 패키지: {failed}')
    exit(1)
else:
    print('모든 핵심 패키지 로딩 성공')
" >> logs\\test.log 2>&1

if errorlevel 1 (
    echo ❌ 일부 핵심 패키지 로딩 실패
    echo [%date% %time%] 핵심 패키지 로딩 실패 >> logs\\test.log
) else (
    echo ✅ 모든 핵심 패키지 로딩 성공
    set /a pass_count+=1
    echo [%date% %time%] 핵심 패키지 로딩 성공 >> logs\\test.log
)

REM 테스트 5: RAGTrace Lite 모듈 확인
echo [테스트 5/10] RAGTrace Lite 모듈 확인...
set /a test_count+=1
python -c "import src.ragtrace_lite; print('RAGTrace Lite 모듈 로딩 성공')" >> logs\\test.log 2>&1
if errorlevel 1 (
    echo ❌ RAGTrace Lite 모듈 로딩 실패
    echo [%date% %time%] RAGTrace Lite 모듈 로딩 실패 >> logs\\test.log
) else (
    echo ✅ RAGTrace Lite 모듈 로딩 성공
    set /a pass_count+=1
    echo [%date% %time%] RAGTrace Lite 모듈 로딩 성공 >> logs\\test.log
)

REM 테스트 6: BGE-M3 모델 확인
echo [테스트 6/10] BGE-M3 모델 확인...
set /a test_count+=1
if exist "models\\bge-m3" (
    REM 모델 파일 상세 확인
    python -c "
from pathlib import Path
model_dir = Path('models/bge-m3')
required_files = ['config.json', 'tokenizer.json']
missing_files = []

for file in required_files:
    if not (model_dir / file).exists():
        missing_files.append(file)

if missing_files:
    print(f'누락된 파일: {missing_files}')
    exit(1)
else:
    print('BGE-M3 모델 파일 확인 완료')
" >> logs\\test.log 2>&1
    
    if errorlevel 1 (
        echo ❌ BGE-M3 모델 파일 불완전
        echo [%date% %time%] BGE-M3 모델 파일 불완전 >> logs\\test.log
    ) else (
        echo ✅ BGE-M3 모델 파일 확인 완료
        set /a pass_count+=1
        echo [%date% %time%] BGE-M3 모델 파일 확인 완료 >> logs\\test.log
    )
) else (
    echo ⚠️  BGE-M3 모델 디렉토리 없음
    echo [%date% %time%] BGE-M3 모델 디렉토리 없음 >> logs\\test.log
)

REM 테스트 7: BGE-M3 모델 로딩 테스트
echo [테스트 7/10] BGE-M3 모델 로딩 테스트...
set /a test_count+=1
if exist "models\\bge-m3" (
    python -c "
from sentence_transformers import SentenceTransformer
import torch

try:
    # CPU에서 테스트 (메모리 절약)
    model = SentenceTransformer('./models/bge-m3', device='cpu')
    test_embedding = model.encode('테스트 문장', convert_to_tensor=False)
    print(f'BGE-M3 모델 로딩 및 임베딩 성공 (차원: {len(test_embedding)})')
except Exception as e:
    print(f'BGE-M3 모델 로딩 실패: {e}')
    exit(1)
" >> logs\\test.log 2>&1
    
    if errorlevel 1 (
        echo ❌ BGE-M3 모델 로딩 실패
        echo [%date% %time%] BGE-M3 모델 로딩 실패 >> logs\\test.log
    ) else (
        echo ✅ BGE-M3 모델 로딩 성공
        set /a pass_count+=1
        echo [%date% %time%] BGE-M3 모델 로딩 성공 >> logs\\test.log
    )
) else (
    echo ⚠️  BGE-M3 모델이 없어 테스트 건너뜀
    echo [%date% %time%] BGE-M3 모델 없음, 테스트 건너뜀 >> logs\\test.log
)

REM 테스트 8: .env 파일 확인
echo [테스트 8/10] 환경 설정 파일 확인...
set /a test_count+=1
if exist ".env" (
    python -c "
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('CLOVA_STUDIO_API_KEY')

if not api_key:
    print('❌ HCX API 키가 설정되지 않음')
    exit(1)
elif api_key == 'nv-your-hcx-api-key-here':
    print('❌ HCX API 키가 기본값으로 설정됨 (실제 키 필요)')
    exit(1)
elif not api_key.startswith('nv-'):
    print('❌ HCX API 키 형식 오류 (nv-로 시작해야 함)')
    exit(1)
else:
    print('✅ HCX API 키 설정 확인')
" >> logs\\test.log 2>&1
    
    if errorlevel 1 (
        echo ❌ .env 파일 설정 문제
        echo [%date% %time%] .env 파일 설정 문제 >> logs\\test.log
    ) else (
        echo ✅ .env 파일 설정 확인
        set /a pass_count+=1
        echo [%date% %time%] .env 파일 설정 확인 >> logs\\test.log
    )
) else (
    echo ⚠️  .env 파일 없음
    echo [%date% %time%] .env 파일 없음 >> logs\\test.log
)

REM 테스트 9: 데이터 디렉토리 확인
echo [테스트 9/10] 데이터 디렉토리 확인...
set /a test_count+=1
if exist "data\\input" (
    set json_count=0
    for %%f in (data\\input\\*.json) do set /a json_count+=1
    if !json_count! GTR 0 (
        echo ✅ 입력 데이터 파일 확인 (!json_count!개)
        set /a pass_count+=1
        echo [%date% %time%] 입력 데이터 파일 확인: !json_count!개 >> logs\\test.log
    ) else (
        echo ⚠️  JSON 데이터 파일 없음
        echo [%date% %time%] JSON 데이터 파일 없음 >> logs\\test.log
    )
) else (
    echo ⚠️  data\\input 디렉토리 없음
    echo [%date% %time%] data\\input 디렉토리 없음 >> logs\\test.log
)

REM 테스트 10: 필수 디렉토리 확인
echo [테스트 10/10] 필수 디렉토리 확인...
set /a test_count+=1
set missing_dirs=
if not exist "db" set missing_dirs=!missing_dirs! db
if not exist "logs" set missing_dirs=!missing_dirs! logs
if not exist "reports" set missing_dirs=!missing_dirs! reports

if "!missing_dirs!"=="" (
    echo ✅ 모든 필수 디렉토리 존재
    set /a pass_count+=1
    echo [%date% %time%] 모든 필수 디렉토리 존재 >> logs\\test.log
) else (
    echo ⚠️  누락된 디렉토리:!missing_dirs!
    echo [%date% %time%] 누락된 디렉토리:!missing_dirs! >> logs\\test.log
)

REM 테스트 결과 요약
echo.
echo ========================================
echo 📊 테스트 결과 요약
echo ========================================
echo 통과: !pass_count!/!test_count!

if !pass_count! EQU !test_count! (
    echo ✅ 모든 테스트 통과! 시스템이 정상적으로 설정되었습니다.
    echo [%date% %time%] 모든 테스트 통과 >> logs\\test.log
) else (
    set /a fail_count=!test_count!-!pass_count!
    echo ⚠️  !fail_count!개 테스트 실패. 문제를 해결하고 다시 시도하세요.
    echo.
    echo 문제 해결 방법:
    echo 1. logs\\test.log 파일 확인
    echo 2. MANUAL_INSTALLATION_GUIDE.md 참조
    echo 3. scripts\\install.bat 다시 실행
    echo [%date% %time%] !fail_count!개 테스트 실패 >> logs\\test.log
)

echo.
echo 상세 로그: logs\\test.log
echo.
pause
"""
        
        with open(scripts_dir / "test_installation.bat", 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        # setup_env.bat - 환경 설정 도우미
        setup_env_script = """@echo off
chcp 65001 > nul 2>&1
echo =========================================
echo RAGTrace Lite 환경 설정 도우미
echo =========================================
echo.

echo 이 스크립트는 .env 파일 설정을 도와드립니다.
echo.

REM .env 파일 존재 확인
if exist ".env" (
    echo 기존 .env 파일이 발견되었습니다.
    echo 내용을 확인하고 수정하시겠습니까? (Y/n):
    set /p modify_existing=
    if /i "!modify_existing!" NEQ "n" (
        notepad .env
        goto :test_config
    )
) else (
    echo .env 파일이 없습니다. 새로 생성합니다.
    
    if exist "config\\.env.template" (
        copy "config\\.env.template" ".env"
        echo ✅ 템플릿에서 .env 파일을 생성했습니다.
    ) else (
        echo 기본 .env 파일을 생성합니다...
        echo # RAGTrace Lite 환경 변수 설정 > .env
        echo. >> .env
        echo # HCX API 설정 >> .env
        echo CLOVA_STUDIO_API_KEY=nv-your-hcx-api-key-here >> .env
        echo HCX_API_ENDPOINT=https://your-internal-hcx-endpoint.com >> .env
        echo. >> .env
        echo # BGE-M3 모델 설정 >> .env
        echo BGE_M3_MODEL_PATH=./models/bge-m3 >> .env
        echo BGE_M3_DEVICE=auto >> .env
        echo. >> .env
        echo # 데이터베이스 설정 >> .env
        echo DATABASE_PATH=./db/ragtrace_lite.db >> .env
        echo. >> .env
        echo # 로그 설정 >> .env
        echo LOG_LEVEL=INFO >> .env
        echo LOG_FILE=./logs/ragtrace.log >> .env
        echo ✅ 기본 .env 파일을 생성했습니다.
    )
)

echo.
echo 📝 .env 파일을 편집합니다...
echo 다음 항목들을 설정해주세요:
echo.
echo 1. CLOVA_STUDIO_API_KEY: HCX API 키 (nv-로 시작)
echo 2. HCX_API_ENDPOINT: 폐쇄망 내부 HCX 엔드포인트
echo.
echo 메모장이 열립니다. 편집 후 저장하고 닫아주세요.
pause
notepad .env

:test_config
echo.
echo 🧪 설정 확인 중...

REM 가상환경 활성화
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
) else (
    echo ❌ 가상환경이 없습니다. 먼저 scripts\\install.bat을 실행하세요.
    pause
    exit /b 1
)

REM 설정 테스트
python -c "
import os
from dotenv import load_dotenv

print('환경 변수 확인 중...')
load_dotenv()

# HCX API 키 확인
api_key = os.getenv('CLOVA_STUDIO_API_KEY')
if not api_key:
    print('❌ CLOVA_STUDIO_API_KEY가 설정되지 않았습니다')
elif api_key == 'nv-your-hcx-api-key-here':
    print('❌ API 키가 기본값으로 설정되어 있습니다')
    print('   실제 HCX API 키로 변경해주세요')
elif not api_key.startswith('nv-'):
    print('❌ HCX API 키 형식이 올바르지 않습니다 (nv-로 시작해야 함)')
else:
    print(f'✅ HCX API 키 확인 (길이: {len(api_key)})')

# 엔드포인트 확인
endpoint = os.getenv('HCX_API_ENDPOINT')
if not endpoint:
    print('❌ HCX_API_ENDPOINT가 설정되지 않았습니다')
elif endpoint == 'https://your-internal-hcx-endpoint.com':
    print('❌ API 엔드포인트가 기본값으로 설정되어 있습니다')
    print('   실제 폐쇄망 엔드포인트로 변경해주세요')
else:
    print(f'✅ HCX API 엔드포인트: {endpoint}')

# BGE-M3 모델 경로 확인
model_path = os.getenv('BGE_M3_MODEL_PATH', './models/bge-m3')
from pathlib import Path
if Path(model_path).exists():
    print(f'✅ BGE-M3 모델 경로: {model_path}')
else:
    print(f'⚠️  BGE-M3 모델이 없습니다: {model_path}')

print()
print('설정 확인 완료!')
"

if errorlevel 1 (
    echo.
    echo ❌ 설정에 문제가 있습니다.
    echo .env 파일을 다시 편집하시겠습니까? (Y/n):
    set /p edit_again=
    if /i "!edit_again!" NEQ "n" (
        notepad .env
        goto :test_config
    )
) else (
    echo.
    echo ✅ 환경 설정이 완료되었습니다!
    echo.
    echo 다음 단계:
    echo 1. scripts\\test_installation.bat으로 전체 시스템 테스트
    echo 2. scripts\\run_evaluation.bat으로 평가 실행
)

echo.
pause
"""
        
        with open(scripts_dir / "setup_env.bat", 'w', encoding='utf-8') as f:
            f.write(setup_env_script)
        
        print("✅ Windows 스크립트 생성 완료")
    
    def _copy_documentation(self):
        """문서를 복사합니다."""
        print("\n📚 [6/8] 문서 복사 중...")
        
        docs = ["README.md", "OFFLINE_DEPLOYMENT.md"]
        for doc in docs:
            src_path = self.project_root / doc
            if src_path.exists():
                shutil.copy2(src_path, self.package_dir / doc)
                print(f"✅ 복사: {doc}")
        
        # README_OFFLINE.md 생성
        offline_readme = self.package_dir / "README_OFFLINE.md"
        readme_content = f"""# RAGTrace Lite 폐쇄망 버전

## 🚀 빠른 시작

### 1. 설치
```cmd
scripts\\install.bat
```

### 2. 환경 설정
```cmd
copy config\\.env.template .env
notepad .env
```

### 3. 실행
```cmd
scripts\\run_evaluation.bat
```

## 📋 패키지 정보
- **생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **버전**: RAGTrace Lite v1.0.3
- **플랫폼**: Windows 10/11
- **Python**: 3.11.x

## 📁 디렉토리 구조
```
{self.package_name}/
├── scripts/           # 설치 및 실행 스크립트
├── wheels/           # Python 의존성 패키지
├── models/           # BGE-M3 모델 파일
├── src/              # 소스 코드
├── config/           # 설정 파일
└── data/             # 샘플 데이터
```

## ❓ 문제 해결
자세한 내용은 OFFLINE_DEPLOYMENT.md를 참조하세요.
"""
        
        with open(offline_readme, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("✅ README_OFFLINE.md 생성 완료")
    
    def _copy_sample_data(self):
        """샘플 데이터를 복사합니다."""
        print("\n📊 [7/8] 샘플 데이터 복사 중...")
        
        data_src = self.project_root / "data"
        if data_src.exists():
            data_dst = self.package_dir / "data"
            shutil.copytree(data_src, data_dst, ignore=shutil.ignore_patterns('*.db', 'output/*'))
            print("✅ 샘플 데이터 복사 완료")
        else:
            # 기본 데이터 디렉토리 생성
            data_dst = self.package_dir / "data"
            data_dst.mkdir(exist_ok=True)
            
            input_dir = data_dst / "input"
            input_dir.mkdir(exist_ok=True)
            
            output_dir = data_dst / "output"
            output_dir.mkdir(exist_ok=True)
            
            print("✅ 데이터 디렉토리 생성 완료")
    
    def _create_zip_package(self):
        """패키지를 ZIP 파일로 압축합니다."""
        print("\n🗜️  [8/8] 패키지 압축 중...")
        
        zip_path = self.package_dir.parent / f"{self.package_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.package_dir.parent)
                    zipf.write(file_path, arcname)
        
        print(f"✅ 압축 완료: {zip_path.name}")
        return zip_path
    
    def _get_folder_size(self, folder_path: Path) -> float:
        """폴더 크기를 MB 단위로 반환합니다."""
        total_size = 0
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    
    def _get_file_size(self, file_path: Path) -> float:
        """파일 크기를 MB 단위로 반환합니다."""
        return file_path.stat().st_size / (1024 * 1024)
    
    def _print_package_summary(self):
        """패키지 내용 요약을 출력합니다."""
        print("\\n📋 패키지 내용 요약:")
        print("=" * 50)
        
        components = [
            ("소스 코드", self.package_dir / "src"),
            ("의존성 패키지", self.package_dir / "wheels"),
            ("BGE-M3 모델", self.package_dir / "models"),
            ("설정 파일", self.package_dir / "config"),
            ("스크립트", self.package_dir / "scripts"),
            ("문서", self.package_dir / "README.md"),
            ("샘플 데이터", self.package_dir / "data")
        ]
        
        total_size = 0
        for name, path in components:
            if path.exists():
                if path.is_dir():
                    size = self._get_folder_size(path)
                    file_count = len(list(path.rglob("*")))
                    print(f"✅ {name}: {size:.1f} MB ({file_count}개 파일)")
                else:
                    size = self._get_file_size(path)
                    print(f"✅ {name}: {size:.1f} MB")
                total_size += size
            else:
                print(f"⚠️  {name}: 없음")
        
        print("-" * 50)
        print(f"📊 총 크기: {total_size:.1f} MB")

def main():
    """메인 함수"""
    print("🔒 RAGTrace Lite 폐쇄망 배포 패키지 생성")
    print("=" * 60)
    
    creator = OfflinePackageCreator()
    zip_file = creator.create_package()
    
    if zip_file:
        print("\\n🎯 다음 단계:")
        print(f"1. {zip_file.name}을 폐쇄망 윈도우 PC로 복사")
        print("2. ZIP 파일 압축 해제")
        print("3. scripts\\install.bat 실행")
        print("4. config\\.env.template을 .env로 복사 후 API 키 설정")
        print("5. scripts\\run_evaluation.bat으로 평가 실행")
    else:
        print("\\n❌ 패키지 생성 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()