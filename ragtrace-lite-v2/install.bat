@echo off
echo Installing RAGTrace Lite v2.0 for Windows...
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

:: Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Installing dependencies...
pip install -r requirements-windows.txt
if errorlevel 1 (
    echo Warning: Some dependencies failed to install
    echo Trying alternative installation...
    pip install -r requirements.txt
)

:: Install package in development mode
echo Installing RAGTrace Lite...
pip install -e .

:: Test installation
echo.
echo Testing installation...
python -c "import ragtrace_lite; print(f'RAGTrace Lite {ragtrace_lite.__version__} installed successfully!')"
if errorlevel 1 (
    echo Error: Installation test failed
    pause
    exit /b 1
)

:: Create .env file if not exists
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file to add your API keys
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To use RAGTrace Lite:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Edit .env file with your API keys
echo   3. Run: ragtrace --help
echo.
echo Quick start:
echo   ragtrace create-template
echo   ragtrace evaluate --excel template.xlsx
echo.
pause