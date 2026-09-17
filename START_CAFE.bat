@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo       CAFE AROMA.COFFEE - STARTING
echo ========================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    set "PY=python"
)

if not exist "venv\Scripts\python.exe" (
    echo Creating the virtual environment...
    %PY% -m venv venv
    if errorlevel 1 goto :error
)

echo Installing/checking required packages...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Preparing the database...
venv\Scripts\python.exe database.py
if errorlevel 1 goto :error

echo.
echo Website starting at http://127.0.0.1:5000
start "Cafe Aroma" http://127.0.0.1:5000
venv\Scripts\python.exe app.py

goto :end

:error
echo.
echo Something went wrong. Make sure Python is installed and try again.
pause

:end
endlocal
