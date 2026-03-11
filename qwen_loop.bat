@echo off
REM Qwen Code Persistence Loop - Easy Launcher
REM 
REM Usage: qwen_loop.bat "Your task description"
REM
REM Example: qwen_loop.bat "Process all files in Needs_Action"

cd /d "%~dp0"

if "%~1"=="" (
    echo.
    echo ============================================================
    echo QWEN CODE PERSISTENCE LOOP
    echo ============================================================
    echo.
    echo Usage: qwen_loop.bat "Your task description"
    echo.
    echo Example:
    echo   qwen_loop.bat "Process all Facebook comments"
    echo   qwen_loop.bat "Create invoices for all customers"
    echo.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo QWEN CODE PERSISTENCE LOOP
echo ============================================================
echo.
echo Task: %*
echo Vault: %CD%
echo.
echo Starting persistence loop...
echo ============================================================
echo.

python scripts\qwen_loop.py %*

echo.
pause
