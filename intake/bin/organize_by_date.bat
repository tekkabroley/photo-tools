@echo off
setlocal

rem Organize every photo under intake\, including files in subdirectories.
rem intake\bin\ is skipped so this script and its helper are left in place.
set "SCRIPT_DIR=%~dp0"
set "PYTHON="

where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if defined PYTHON (
    "%PYTHON%" "%SCRIPT_DIR%organize_by_date.py" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>&1 && (
    py -3 "%SCRIPT_DIR%organize_by_date.py" %*
    exit /b %ERRORLEVEL%
)

echo Python not found. Install Python or add it to PATH.
exit /b 1