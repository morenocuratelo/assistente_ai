# 🚀 Comandi Terminale - Archivista AI

Raccolta completa dei comandi più utilizzati per lo sviluppo e gestione di Archivista AI.

## 📋 Sommario Rapido

### Docker (Produzione)
```bash
docker-compose up --build
docker-compose up -d
docker-compose down
```

### Sviluppo Locale
```bash
streamlit run main.py --server.port 8501
```

### Dependency Management
```bash
pip-compile requirements.in
pip install -r requirements.txt
```

---

## 🐳 Docker Commands

### Avvio Servizi
```bash
# Avvio completo (produzione)
docker-compose up -d

# Avvio con rebuild automatico
docker-compose up --build -d

# Avvio solo servizi specifici
docker-compose up -d redis webapp
docker-compose up -d worker beat
```

### Arresto Servizi
```bash
# Arresto normale (mantiene dati)
docker-compose down

# Arresto completo (rimuove anche container)
docker-compose down --remove-orphans

# Arresto e pulizia volumi (CANCELLA DATI!)
docker-compose down -v
```

### Stato e Monitoraggio
```bash
# Stato servizi
docker-compose ps

# Log tutti i servizi
docker-compose logs

# Log servizio specifico
docker-compose logs webapp
docker-compose logs worker
docker-compose logs redis

# Log in tempo reale
docker-compose logs -f
docker-compose logs -f worker

# Log ultimo 100 righe
docker-compose logs --tail=100 webapp
```

### Build e Ricostruzione
```bash
# Build immagini
docker-compose build

# Build senza cache
docker-compose build --no-cache

# Build servizio specifico
docker-compose build webapp
docker-compose build worker

# Ricostruzione completa
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Debug e Accesso Container
```bash
# Accesso al container
docker-compose exec webapp bash
docker-compose exec worker bash
docker-compose exec redis redis-cli

# Esegui comando nel container
docker-compose exec webapp python -c "print('test')"
docker-compose exec redis redis-cli ping

# Visualizza processi attivi
docker-compose top

# Statistiche risorse
docker-compose exec webapp ps aux
```

### Pulizia Sistema
```bash
# Pulizia container fermi
docker container prune

# Pulizia immagini dangling
docker image prune

# Pulizia completa (ATTENZIONE!)
docker system prune -a --volumes

# Pulizia solo volumi inutilizzati
docker volume prune
```

---

## 🐍 Python & Dependency Management

### Ambiente Virtuale
```bash
# Creazione ambiente virtuale
python -m venv venv

# Attivazione ambiente (Windows)
venv\Scripts\activate

# Attivazione ambiente (Linux/Mac)
source venv/bin/activate

# Disattivazione
deactivate
```

### pip-tools (Dependency Management)
```bash
# Compila requirements.txt da requirements.in
pip-compile requirements.in

# Compila con upgrade dipendenze
pip-compile --upgrade requirements.in

# Installa dipendenze
pip install -r requirements.txt

# Installa in modalità sviluppo
pip install -e .

# Verifica dipendenze installate
pip list

# Esporta ambiente
pip freeze > requirements.txt
```

### Installazione Manuale
```bash
# Installa dipendenze principali
pip install streamlit llama-index celery redis

# Installa dipendenze sviluppo
pip install pytest black flake8

# Installa tutto da requirements.txt
pip install -r requirements.txt
```

---

## 🎯 Streamlit Development

### Avvio Applicazione
```bash
# Avvio normale
streamlit run main.py

# Avvio con configurazione specifica
streamlit run main.py --server.port 8501 --server.address 0.0.0.0

# Avvio con reload automatico
streamlit run main.py --server.headless true

# Avvio con debug
streamlit run main.py --logger.level=debug
```

### Configurazione Server
```bash
# Specifica porta
streamlit run main.py --server.port 8502

# Accesso da remoto
streamlit run main.py --server.address 0.0.0.0

# Disabilita CORS (per sviluppo)
streamlit run main.py --server.enableCORS false

# Configurazione completa
streamlit run main.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --theme.base dark
```

### Debug e Testing
```bash
# Verifica configurazione
streamlit config show

# Test configurazione
streamlit hello

# Cache management
streamlit cache clear

# Gestione completa cache documenti
python cache_management_example.py --status
python cache_management_example.py --all
python cache_management_example.py --vector-store-only

# Pulizia selettiva cache
python cache_management_example.py --streamlit-only
python cache_management_example.py --performance-only
python cache_management_example.py --search-only

# Visualizza informazioni sistema
streamlit --version
```

---

## 🔄 Celery Task Management

### Avvio Worker
```bash
# Avvio worker principale
celery -A celery_app.celery_app worker --loglevel=info

# Avvio con configurazione Windows
celery -A celery_app.celery_app worker --loglevel=info --pool=solo

# Avvio con concorrenza specifica
celery -A celery_app.celery_app worker --loglevel=info --concurrency=4

# Avvio con logging su file
celery -A celery_app.celery_app worker --loglevel=info --logfile=celery_worker.log
```

### Avvio Scheduler (Beat)
```bash
# Avvio scheduler task periodiche
celery -A celery_app.celery_app beat --loglevel=info

# Avvio con configurazione specifica
celery -A celery_app.celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule
```

### Monitoraggio Task
```bash
# Visualizza task attive
celery -A celery_app.celery_app inspect active

# Visualizza worker registrati
celery -A celery_app.celery_app inspect registered

# Statistiche worker
celery -A celery_app.celery_app inspect stats

# Ping worker
celery -A celery_app.celery_app inspect ping
```

### Controllo Task
```bash
# Lista code disponibili
celery -A celery_app.celery_app inspect active_queues

# Revoca task specifica
celery -A celery_app.celery_app control revoke <task_id>

# Termina tutti i worker
celery -A celery_app.celery_app control shutdown

# Riavvia tutti i worker
celery -A celery_app.celery_app control pool_restart
```

---

## 🔴 Redis Operations

### Avvio e Configurazione
```bash
# Avvio Redis (Windows)
redis-server.exe redis.windows.conf

# Avvio Redis (Linux)
redis-server --port 6379 --protected-mode no

# Test connessione
redis-cli ping

# Verifica stato
redis-cli info
```

### Operazioni Base
```bash
# Lista chiavi
redis-cli keys *

# Visualizza contenuto chiave
redis-cli get <chiave>

# Elimina chiave
redis-cli del <chiave>

# Verifica memoria utilizzata
redis-cli info memory

# Salva dati su disco
redis-cli save

# Ultimo salvataggio
redis-cli lastsave
```

### Debug Redis
```bash
# Monitora comandi in tempo reale
redis-cli monitor

# Visualizza connessioni attive
redis-cli client list

# Informazioni server
redis-cli info server

# Statistiche lente
redis-cli slowlog get 10
```

---

## 📊 Monitoring & Debugging

### Flower Dashboard (Celery Monitor)
```bash
# Avvio Flower
celery -A celery_app.celery_app flower --port=5555

# Avvio con configurazione specifica
celery -A celery_app.celery_app flower --port=5555 --address=0.0.0.0

# Accesso: http://localhost:5555
```

### Test Servizi
```bash
# Test Redis
redis-cli ping

# Test connessione Python-Redis
python -c "import redis; r=redis.Redis(host='localhost'); print(r.ping())"

# Test Celery connection
python -c "from celery_app import celery_app; print(celery_app.connection().ping())"

# Test configurazione LlamaIndex
python -c "from llama_index.core import Settings; print('LlamaIndex OK')"
```

### Debug Application
```bash
# Test import moduli principali
python -c "import streamlit, celery, llama_index; print('All imports OK')"

# Test configurazione ambiente
python -c "import os; print('REDIS_URL:', os.getenv('REDIS_URL', 'Not set'))"

# Test connessione Ollama
python -c "import requests; response = requests.get('http://localhost:11434/api/tags'); print('Ollama OK' if response.status_code == 200 else 'Ollama Error')"

# Test cache management system
python cache_management_example.py --status
python cache_management_example.py --dry-run
```

---

## 🔧 Development Workflow

### Setup Iniziale
```bash
# 1. Crea ambiente virtuale
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia servizi
docker-compose up -d redis
redis-server.exe redis.windows.conf  # Se non usi Docker

# 4. Avvia worker Celery
celery -A celery_app.celery_app worker --loglevel=info --pool=solo

# 5. Avvia applicazione (nuovo terminale)
streamlit run main.py --server.port 8501
```

### Sviluppo Quotidiano
```bash
# 1. Attiva ambiente
venv\Scripts\activate

# 2. Avvia servizi (se necessario)
docker-compose up -d

# 3. Avvia worker Celery (terminale 1)
celery -A celery_app.celery_app worker --loglevel=info

# 4. Avvia applicazione (terminale 2)
streamlit run main.py

# 5. Monitoraggio (terminale 3)
docker-compose logs -f worker
```

### Dopo Modifiche al Codice
```bash
# Ricarica applicazione Streamlit
# (Streamlit ha hot-reload automatico)

# Ricarica worker Celery
# Riavvia il processo worker

# Aggiorna dipendenze
pip-compile requirements.in
pip install -r requirements.txt

# Ricostruisci container Docker
docker-compose up --build -d
```

---

## 🚨 Comandi di Emergenza

### Force Stop
```bash
# Forza arresto tutti i container
docker-compose kill

# Rimuovi tutti i container
docker-compose rm -f

# Pulizia completa (usa con cautela!)
docker system prune -a --volumes
```

### Reset Database
```bash
# Arresta servizi
docker-compose down

# Rimuovi volumi database
docker volume rm $(docker volume ls -q | grep archivista)

# Riavvia servizi
docker-compose up -d

# Reset completo cache documenti
python cache_management_example.py --all
```

### Recovery Servizi
```bash
# Se Redis non parte
redis-cli shutdown
redis-server.exe redis.windows.conf

# Se Celery worker crasha
# Riavvia il processo worker

# Se Streamlit non risponde
# Riavvia: streamlit run main.py
```

---

## 📝 Note Importanti

### Configurazione Windows
- Usa `--pool=solo` per Celery su Windows
- Redis potrebbe richiedere configurazione speciale
- Usa percorsi Windows nel docker-compose.yml (`//c/path/...`)

### Performance
- Monitora memoria Redis: `redis-cli info memory`
- Controlla worker attivi: `celery -A celery_app inspect active`
- Usa `htop` o Task Manager per monitorare risorse

### Troubleshooting
1. **Controlla sempre i log**: `docker-compose logs [servizio]`
2. **Verifica connessioni**: `redis-cli ping`
3. **Test configurazione**: `python test_app.py`
4. **Monitor risorse**: `docker stats`

### Backup Dati
```bash
# Backup database
cp -r db_memoria db_memoria.backup.$(date +%Y%m%d_%H%M%S)

# Backup documenti
cp -r documenti_da_processare documenti_da_processare.backup.$(date +%Y%m%d_%H%M%S)
```

---

## 🔗 Riferimenti Utili

- **Documentazione Docker**: `DOCKER_README.md`
- **Documentazione Celery**: `CELERY_README.md`
- **Documentazione Cache Management**: `CACHE_MANAGEMENT_README.md`
- **Configurazione**: `docker-compose.yml`
- **Dipendenze**: `requirements.in`

---

*Questo file viene aggiornato automaticamente con i comandi più utilizzati nel progetto Archivista AI.*
