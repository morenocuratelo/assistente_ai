@echo off
echo ========================================
echo Archivista AI - Redis Server Starter
echo ========================================
echo.

REM Controlla se Redis è installato nella nuova struttura
if not exist "redis\bin\redis-server.exe" (
    echo ❌ Redis non trovato nella directory redis\bin\
    echo.
    echo Struttura Redis richiesta:
    echo redis\bin\redis-server.exe
    echo redis\config\redis.windows.conf
    echo.
    echo Per installare Redis su Windows:
    echo 1. Scarica Redis da: https://github.com/microsoftarchive/redis/releases
    echo 2. Crea la struttura: redis\bin\ e redis\config\
    echo 3. Estrai eseguibili in redis\bin\
    echo 4. Copia configurazioni in redis\config\
    echo 5. Oppure usa: choco install redis-64
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

REM Avvia Redis server con configurazione
redis\bin\redis-server.exe redis\config\redis.windows.conf --port 6379 --protected-mode no

echo.
echo Redis server avviato sulla porta 6379
echo Premi Ctrl+C per fermare il server
echo.

pause
