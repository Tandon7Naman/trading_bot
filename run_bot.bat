@echo off
REM Gold Trading Bot - Task Scheduler Batch File
REM Save this as: C:\Path\To\Gold-Trading-Bot\run_bot.bat

setlocal enabledelayedexpansion

REM ===== CONFIGURATION =====
REM Update these paths to match your system
set PROJECT_DIR=N:\gold-trading-bot
set PYTHON_PATH=N:\gold-trading-bot\.venv\Scripts\python.exe

REM ===== SETUP =====
cd /d %PROJECT_DIR%

REM Create logs directory
if not exist logs mkdir logs

REM Generate log filename with timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set LOG_FILE=logs\bot_run_%mydate%_%mytime%.log

REM ===== EXECUTION =====
echo. >> %LOG_FILE%
echo ============================================== >> %LOG_FILE%
echo Gold Trading Bot Run >> %LOG_FILE%
echo Started: %date% %time% >> %LOG_FILE%
echo ============================================== >> %LOG_FILE%
echo. >> %LOG_FILE%

REM Run the bot
echo [*] Running bot... >> %LOG_FILE%
%PYTHON_PATH% main_bot.py >> %LOG_FILE% 2>&1

REM Capture result
set EXIT_CODE=%ERRORLEVEL%

echo. >> %LOG_FILE%
if %EXIT_CODE% equ 0 (
    echo [+] Bot completed successfully at %time% >> %LOG_FILE%
) else (
    echo [-] Bot failed with exit code %EXIT_CODE% at %time% >> %LOG_FILE%
)
echo ============================================== >> %LOG_FILE%
echo. >> %LOG_FILE%

exit /b %EXIT_CODE%
