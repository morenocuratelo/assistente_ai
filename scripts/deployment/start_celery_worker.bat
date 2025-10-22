@echo off
echo ========================================
echo    Archivista AI - Celery Worker
echo ========================================
echo.
echo Starting Celery worker...
echo This will listen for document processing tasks
echo.
echo Make sure Redis is running first!
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start Celery worker
echo Starting worker...
celery -A tasks worker --loglevel=info --concurrency=2 --pool=solo

echo.
echo Worker stopped.
pause
