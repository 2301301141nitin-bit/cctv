@echo off
title Antigravity CCTV Intelligence Platform
color 0B

echo.
echo  ============================================================
echo    Antigravity CCTV Intelligence Platform v2.0
echo    One-Click Launcher for Windows
echo  ============================================================
echo.

:: ---- Configuration ----
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "VENV_DIR=%PROJECT_ROOT%\unified_server\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "WEB_DIR=%PROJECT_ROOT%\unified_server\web"
set "SERVER_DIR=%PROJECT_ROOT%\unified_server"
set "REQUIREMENTS=%SERVER_DIR%\requirements.txt"
set "SERVER_PORT=8000"

:: ---- Step 1: Verify Python ----
echo  [1/5] Verifying Python installation...

if exist "%VENV_PYTHON%" (
    echo        Virtual environment found.
) else (
    echo        Virtual environment not found, creating...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo.
        echo  ERROR: Python not found or venv creation failed.
        echo  Install Python 3.10+ from https://python.org
        echo  Make sure "Add Python to PATH" is checked.
        echo.
        pause
        exit /b 1
    )
    echo        Virtual environment created.
)

:: ---- Step 2: Install Python Dependencies (if missing) ----
echo.
echo  [2/5] Checking Python dependencies...

"%VENV_PYTHON%" -c "import fastapi; import torch; import transformers; import ultralytics; import faiss; import shapely" 2>nul
if errorlevel 1 (
    echo        Installing Python dependencies [this may take several minutes]...
    
    :: Install CUDA-enabled PyTorch first (for GPU acceleration)
    echo        Installing PyTorch with CUDA support ^(this is a 2.5GB download, please wait^)...
    "%VENV_PIP%" install torch torchvision --index-url https://download.pytorch.org/whl/cu124 --default-timeout=1000 --disable-pip-version-check
    if errorlevel 1 (
        echo.
        echo        [WARNING] CUDA PyTorch download failed. Falling back to CPU PyTorch...
        "%VENV_PIP%" install torch torchvision --default-timeout=1000 --disable-pip-version-check
    )
    
    :: Install remaining dependencies
    "%VENV_PIP%" install -r "%REQUIREMENTS%" --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo.
        echo  ERROR: Failed to install Python dependencies.
        echo         Check your internet connection and try again.
        pause
        exit /b 1
    )
    echo        Dependencies installed.
) else (
    :: Check if CUDA PyTorch is installed
    "%VENV_PYTHON%" -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>nul
    if errorlevel 1 (
        echo        WARNING: PyTorch is CPU-only. For GPU acceleration, run:
        echo                 pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
    ) else (
        echo        All dependencies installed ^(GPU enabled^).
    )
)

:: ---- Step 3: Install Node.js Dependencies (if missing) ----
echo.
echo  [3/5] Checking frontend dependencies...

if not exist "%WEB_DIR%\node_modules\react" (
    echo        Installing npm packages...

    where node >nul 2>&1
    if errorlevel 1 (
        echo  WARNING: Node.js not found. Frontend will not be available.
        echo           Install Node.js from https://nodejs.org
        echo           The API will still work at http://localhost:%SERVER_PORT%/docs
        goto :skip_frontend
    )

    cd /d "%WEB_DIR%"
    call npm install --silent 2>nul
    if errorlevel 1 (
        echo  WARNING: npm install failed. Frontend may not work.
    ) else (
        echo        npm packages installed.
    )
    cd /d "%PROJECT_ROOT%"
) else (
    echo        npm packages already installed.
)

:: ---- Step 4: Build Frontend (if needed) ----
echo.
echo  [4/5] Checking frontend build...

if not exist "%WEB_DIR%\dist\index.html" (
    echo        Building frontend [first time only]...

    where node >nul 2>&1
    if errorlevel 1 (
        echo  WARNING: Node.js not found. Skipping frontend build.
        goto :skip_frontend
    )

    cd /d "%WEB_DIR%"
    call npm run build 2>nul
    if errorlevel 1 (
        echo  WARNING: Frontend build failed. API will still work.
    ) else (
        echo        Frontend built successfully.
    )
    cd /d "%PROJECT_ROOT%"
) else (
    echo        Frontend already built.
)

:skip_frontend

:: ---- Step 5: Kill Any Existing Server on Port ----
echo.
echo  [5/5] Starting unified server...

:: Kill any process already using port 8000 using a temp script
set "KILL_SCRIPT=%PROJECT_ROOT%\unified_server\_kill_port.py"
"%VENV_PYTHON%" -c "import subprocess, sys; result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True); lines = [l for l in result.stdout.splitlines() if ':%s ' % sys.argv[1] in l and 'LISTENING' in l]; pids = set(l.split()[-1] for l in lines); [subprocess.run(['taskkill', '/PID', p, '/F'], capture_output=True) for p in pids if p != '0']" %SERVER_PORT% 2>nul

:: Wait briefly for port to free up
timeout /t 1 /nobreak >nul

:: ---- Launch ----
echo.
echo  ============================================================
echo.
echo    Web UI:     http://localhost:%SERVER_PORT%/app/
echo    API Docs:   http://localhost:%SERVER_PORT%/docs
echo    Settings:   http://localhost:%SERVER_PORT%/app/settings
echo.
echo  ============================================================
echo    Press Ctrl+C to stop the server
echo  ============================================================
echo.

:: Open browser after a short delay (in background)
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:%SERVER_PORT%/app/"

:: Run the unified server
cd /d "%PROJECT_ROOT%"
"%VENV_PYTHON%" -m unified_server.main

:: If the server exits
echo.
echo  ============================================================
echo   Server stopped.
echo  ============================================================
echo.
pause
