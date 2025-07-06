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