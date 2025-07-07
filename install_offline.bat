@echo off
chcp 65001 >nul
echo ====================================
echo RAGTrace Lite 오프라인 설치 시작
echo ====================================

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Python이 설치되어 있지 않습니다.
    echo Python 3.11 설치를 시작합니다...
    
    if exist "python-3.11.9-amd64.exe" (
        start /wait python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
        echo Python 설치 완료. 새 명령 프롬프트에서 다시 실행해주세요.
    ) else (
        echo ERROR: python-3.11.9-amd64.exe 파일을 찾을 수 없습니다.
        echo https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
        echo 위 주소에서 다운로드하여 현재 폴더에 넣어주세요.
    )
    pause
    exit
)

REM Python 버전 확인
echo Python 버전 확인 중...
python --version

REM 가상환경 생성
echo.
echo 가상환경 생성 중...
python -m venv ragtrace_env

REM 가상환경 활성화
call ragtrace_env\Scripts\activate.bat

REM pip 업그레이드
echo.
echo pip 업그레이드 중...
python -m pip install --upgrade pip --no-index --find-links packages\

REM 패키지 설치
echo.
echo RAGTrace Lite 설치 중...
echo 이 작업은 몇 분 정도 걸릴 수 있습니다...
pip install --no-index --find-links packages\ ragtrace-lite[all]

REM 설치 확인
ragtrace-lite version >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: RAGTrace Lite 설치가 완료되지 않았을 수 있습니다.
    echo packages 폴더에 모든 필요한 파일이 있는지 확인해주세요.
) else (
    echo.
    echo RAGTrace Lite 설치 확인 완료!
)

REM BGE-M3 모델 복사
echo.
echo BGE-M3 모델 설정 중...
if exist "models\bge-m3" (
    if not exist "ragtrace_env\models" mkdir ragtrace_env\models
    echo BGE-M3 모델 복사 중... (약 2.3GB)
    xcopy /E /I /Y /Q models\bge-m3 ragtrace_env\models\bge-m3
    echo BGE-M3 모델 복사 완료!
) else (
    echo WARNING: models\bge-m3 폴더를 찾을 수 없습니다.
    echo BGE-M3 임베딩을 사용하려면 모델 파일이 필요합니다.
)

REM 환경 변수 설정 파일 생성
echo.
echo 환경 설정 파일 생성 중...
if not exist ".env" (
    (
    echo # RAGTrace Lite Configuration
    echo # HCX API 키를 실제 값으로 변경해주세요
    echo CLOVA_STUDIO_API_KEY=your-hcx-api-key-here
    echo.
    echo # BGE-M3 모델 경로
    echo BGE_M3_MODEL_PATH=./models/bge-m3
    echo.
    echo # 기본 설정
    echo DEFAULT_LLM=hcx
    echo DEFAULT_EMBEDDING=bge_m3
    echo.
    echo # 로그 레벨
    echo LOG_LEVEL=INFO
    ) > .env
    echo .env 파일이 생성되었습니다.
) else (
    echo .env 파일이 이미 존재합니다.
)

REM 실행 배치 파일 생성
echo.
echo 실행 스크립트 생성 중...
(
echo @echo off
echo chcp 65001 ^>nul
echo call ragtrace_env\Scripts\activate.bat
echo ragtrace-lite %%*
) > run_ragtrace.bat

REM 샘플 데이터 생성
echo.
echo 샘플 데이터 생성 중...
if not exist "data" mkdir data
(
echo [
echo   {
echo     "question": "한국의 수도는 어디인가요?",
echo     "answer": "한국의 수도는 서울입니다.",
echo     "contexts": [
echo       "서울특별시는 대한민국의 수도이자 최대 도시입니다.",
echo       "서울은 정치, 경제, 문화의 중심지입니다."
echo     ],
echo     "ground_truths": ["한국의 수도는 서울이다."]
echo   }
echo ]
) > data\sample.json

echo.
echo ====================================
echo 설치 완료!
echo ====================================
echo.
echo 다음 단계:
echo.
echo 1. .env 파일을 메모장으로 열어 HCX API 키 입력
echo    notepad .env
echo.
echo 2. 테스트 실행:
echo    run_ragtrace.bat evaluate data\sample.json
echo.
echo 3. 도움말 보기:
echo    run_ragtrace.bat --help
echo.
echo ====================================
echo.
pause