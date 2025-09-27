@echo off
echo ========================================
echo Archivista AI - Redis Server Starter
echo ========================================
echo.

REM Controlla se Redis è installato
if not exist "redis-server.exe" (
    echo ❌ Redis non trovato nella directory corrente.
    echo.
    echo Per installare Redis su Windows:
    echo 1. Scarica Redis da: https://github.com/microsoftarchive/redis/releases
    echo 2. Estrai redis-server.exe nella directory del progetto
    echo 3. Oppure usa: choco install redis-64
    echo.
    echo In alternativa, puoi usare WSL:
    echo wsl --install
    echo sudo apt install redis-server
    echo sudo service redis-server start
    echo.
    pause
    exit /b 1
)

echo ✅ Redis trovato. Avvio del server...
echo.

REM Avvia Redis server
redis-server.exe --port 6379 --protected-mode no

echo.
echo Redis server avviato sulla porta 6379
echo Premi Ctrl+C per fermare il server
echo.

pause
