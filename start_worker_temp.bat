@echo off
echo ========================================
echo    Archivista AI - Celery Worker
echo ========================================
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start Celery worker
echo Starting worker...
celery -A tasks worker --loglevel=info --concurrency=1 --pool=solo

echo.
echo Worker stopped.
pause
