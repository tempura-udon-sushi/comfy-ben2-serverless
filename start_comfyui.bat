@echo off
REM Navigate to ComfyUI directory
cd /d "%~dp0ComfyUI"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
)

REM Start ComfyUI
echo Starting ComfyUI...
python main.py %*
