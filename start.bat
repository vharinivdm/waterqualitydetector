@echo off
REM ###############################################################################
REM AquaGuard AI - Startup Script for Windows
REM This script starts the Flask application server
REM ###############################################################################

echo ======================================================================
echo 🌊 AquaGuard AI - Smart Water Management System
echo ======================================================================
echo.

cd /d "%~dp0"
set PROJECT_ROOT=%cd%

echo 📂 Project Directory: %PROJECT_ROOT%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python 3 is not installed!
    echo    Please install Python 3.7 or higher and try again.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Found: %PYTHON_VERSION%
echo.

REM Check if required packages are installed
echo 📦 Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo ⚠️  Dependencies not found. Installing...
    echo.
    pip install -r requirements.txt
    echo.
)

REM Check if database exists, if not initialize it
if not exist "data\aquaguard.db" (
    echo 🗄️  Initializing database...
    cd backend
    python database.py
    cd ..
    echo.
)

REM Check if model exists, if not train it
if not exist "models\rf_model.pkl" (
    echo 🧠 Training ML model...
    cd backend
    python train_model.py
    cd ..
    echo.
)

REM Create uploads directory if it doesn't exist
if not exist "uploads" (
    mkdir uploads
    echo 📁 Created uploads directory
)

echo ======================================================================
echo 🚀 Starting AquaGuard AI Server...
echo ======================================================================
echo.
echo 🌐 Server URLs:
echo    - Local:   http://localhost:9000
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
echo    - Network: http://%IP:~1%:9000
echo.
echo 👤 Demo Login Credentials:
echo    - Username: demo
echo    - Password: demo123
echo.
echo ⚠️  Press CTRL+C to stop the server
echo ======================================================================
echo.

REM Start the Flask application
cd backend
python app_enhanced.py
