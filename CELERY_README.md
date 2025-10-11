# Celery + Redis Setup per Archivista AI v2.4.0 (Alpha 2.4)

Questa guida spiega come configurare e utilizzare Celery con Redis per l'elaborazione asincrona delle task in Archivista AI v2.4.0 (Alpha 2.4) - **Phase 3: Intelligent Academic Ecosystem** con architettura multi-pagina avanzata e sistema di gamification.

## 🆕 Architettura Multi-Pagina (v2.4.0+)

**IMPORTANTE**: Archivista AI v2.4.0 (Alpha 2.4) utilizza un'architettura multi-pagina avanzata completa con 6 pagine specializzate per l'ecosistema accademico intelligente. Il processamento dei documenti avviene completamente in background tramite task Celery asincrone, mentre l'interfaccia utente è organizzata in pagine ottimizzate per funzioni specifiche con sistema di gamification integrato.

### 🔄 Nuovo Workflow

1. **UI (Streamlit)**: L'utente carica documenti nella cartella `documenti_da_processare/`
2. **Pulsante "Scansiona nuovi documenti"**: L'utente clicca il pulsante nella UI
3. **Invio Task**: La UI invia task Celery per ogni nuovo documento
4. **Worker Celery**: Il worker in background processa i documenti
5. **Aggiornamento Status**: Il worker aggiorna `archivista_status.json` per feedback UI
6. **Completamento**: I documenti processati appaiono automaticamente nell'archivio

### 📋 Task Principale: `process_document_task`

Il task principale per il processamento documenti è ora `process_document_task` in `tasks.py`:

```python
from tasks import process_document_task

# Processa un singolo documento
result = process_document_task.delay("/path/to/document.pdf")
```

**Funzionalità del Task:**
- ✅ Estrazione testo completo dal PDF
- ✅ Indicizzazione con LlamaIndex
- ✅ Creazione anteprima AI
- ✅ Estrazione metadati con LLM
- ✅ Aggiornamento database SQLite
- ✅ Spostamento file in `documenti_archiviati/`
- ✅ Aggiornamento file di stato per feedback UI

## 📋 Prerequisiti

- Python 3.8+
- Redis server in esecuzione
- Dipendenze installate (celery, redis)

## 🚀 Installazione e Configurazione

### 1. Installazione Redis

#### Opzione A: Windows nativo
```bash
# Scarica Redis da: https://github.com/microsoftarchive/redis/releases
# Estrai redis-server.exe nella directory del progetto
# Oppure usa Chocolatey:
choco install redis-64
```

#### Opzione B: Windows Subsystem for Linux (WSL)
```bash
wsl --install
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

#### Opzione C: Docker (se disponibile)
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 2. Avvio Redis

#### Windows:
```bash
# Usa lo script fornito
start_redis.bat
```

#### Linux/WSL:
```bash
redis-server --port 6379 --protected-mode no
```

### 3. Verifica Installazione

```bash
# Test connessione Redis
python test_celery.py
```

## ⚙️ Configurazione Celery

### File di Configurazione

- **`tasks.py`**: Configurazione principale Celery e task di esempio
- **`archivista_tasks.py`**: Task specifiche per Archivista AI
- **`test_celery.py`**: Script di test per verificare la configurazione

### Variabili d'Ambiente

```bash
# URL Redis (default: redis://localhost:6379/0)
REDIS_URL=redis://localhost:6379/0
```

## 🎯 Utilizzo delle Task

### Task Disponibili

#### 1. Controllo Nuovi Documenti
```python
from tasks import check_for_new_documents

# Esecuzione asincrona
result = check_for_new_documents.delay()

# Attesa risultato
result_value = result.get(timeout=30)
print(result_value)
```

#### 2. Processamento Documento in Background
```python
from tasks import process_document_background

# Processa un singolo documento
result = process_document_background.delay(
    file_path="/path/to/document.pdf",
    metadata={"title": "Titolo documento", "authors": ["Autore 1"]}
)
```

#### 3. Generazione Riassunto
```python
from tasks import generate_summary

result = generate_summary.delay(
    document_id="doc_123",
    query="Riassumi il contenuto principale"
)
```

#### 4. Ricerca Documenti Simili
```python
from tasks import search_similar_documents

result = search_similar_documents.delay(
    query="intelligenza artificiale",
    top_k=5
)
```

#### 5. Pulizia Storage
```python
from tasks import cleanup_storage

result = cleanup_storage.delay(days_old=30)
```

### Task Batch Processing
```python
from archivista_tasks import batch_process_documents

file_paths = [
    "/path/to/doc1.pdf",
    "/path/to/doc2.pdf",
    "/path/to/doc3.docx"
]

metadata_list = [
    {"title": "Documento 1"},
    {"title": "Documento 2"},
    {"title": "Documento 3"}
]

result = batch_process_documents.delay(file_paths, metadata_list)
```

## 🖥️ Avvio Servizi Celery

### 🚀 Avvio Rapido (Windows)

```bash
# 1. Avvia Redis
start_redis.bat

# 2. In un nuovo terminale, avvia il Worker Celery
start_celery_worker.bat

# 3. Avvia l'applicazione Streamlit
streamlit run main.py
```

### 🐳 Avvio con Docker (Raccomandato)

```bash
# 1. Avvia tutti i servizi con Docker Compose
docker-compose up -d

# 2. Visualizza i log
docker-compose logs -f

# 3. Arresta tutti i servizi
docker-compose down

# 4. Ricostruisci le immagini (dopo modifiche al codice)
docker-compose up --build -d
```

**Servizi Disponibili:**
- **UI**: http://localhost:8501 (Streamlit)
- **Flower**: http://localhost:5555 (Monitor Celery)
- **Redis**: localhost:6379 (Message Broker)

### 🔧 Avvio Manuale

#### 1. Avvio Worker Celery

```bash
# Terminale 1 - Worker principale
python -m celery -A tasks worker --loglevel=info --concurrency=2

# Con configurazione specifica per Windows
python -m celery -A tasks worker --loglevel=info --pool=solo

# Con logging su file
python -m celery -A tasks worker --loglevel=info --logfile=celery_worker.log
```

### 2. Avvio Beat Scheduler (Task Periodiche)

```bash
# Terminale 2 - Scheduler per task periodiche
python -m celery -A tasks beat --loglevel=info
```

### 3. Avvio Flower (Monitor Web - Opzionale)

```bash
# Installa Flower
pip install flower

# Avvia Flower
python -m flower -A tasks --port=5555
```

## 📊 Monitoraggio

### 1. Flower Dashboard
- URL: http://localhost:5555
- Funzionalità: Monitor task, statistiche, gestione worker

### 2. Comandi Celery

```bash
# Visualizza task attive
python -m celery -A tasks inspect active

# Visualizza worker registrati
python -m celery -A tasks inspect registered

# Statistiche worker
python -m celery -A tasks inspect stats

# Revoca task
python -m celery -A tasks control revoke <task_id>
```

## 🔧 Task Pianificate

Le seguenti task sono configurate per l'esecuzione automatica:

### Controllo Nuovi Documenti
- **Frequenza**: Ogni 30 minuti
- **Task**: `check_for_new_documents`
- **Scopo**: Verifica presenza nuovi file da processare

### Pulizia Task Vecchie
- **Frequenza**: Ogni giorno alle 2:00
- **Task**: `cleanup_old_tasks`
- **Scopo**: Rimuove risultati task completate dopo 24 ore

## 🛠️ Integrazione con Streamlit

### Esempio di Utilizzo in main.py

```python
import streamlit as st
from tasks import process_document_background

def process_document_ui(file_path):
    """Processa documento con UI feedback"""

    if st.button("Processa Documento"):
        with st.spinner("Avvio processamento..."):
            # Invia task asincrona
            task = process_document_background.delay(file_path)

            # Salva task ID in session state
            st.session_state.task_id = task.id

            st.success("Task avviata!")

    # Controlla stato task
    if 'task_id' in st.session_state:
        task_id = st.session_state.task_id
        task = process_document_background.AsyncResult(task_id)

        if task.state == 'PENDING':
            st.info("Task in coda...")
        elif task.state == 'PROGRESS':
            st.info(f"Processamento in corso... {task.info}")
        elif task.state == 'SUCCESS':
            st.success("Processamento completato!")
            st.json(task.result)
            del st.session_state.task_id
        elif task.state == 'FAILURE':
            st.error("Errore nel processamento!")
            st.error(str(task.info))
            del st.session_state.task_id
```

## 🔍 Troubleshooting

### Problemi Comuni

#### 1. Redis Connection Error
```bash
# Verifica che Redis sia in esecuzione
redis-cli ping

# Controlla configurazione
python -c "import redis; r=redis.Redis(); print(r.ping())"
```

#### 2. Celery Worker non si avvia
```bash
# Controlla configurazione
python -c "from tasks import celery_app; print('OK')"

# Avvia con debug
python -m celery -A tasks worker --loglevel=debug
```

#### 3. Task non vengono eseguite
```bash
# Verifica coda messaggi
python -m celery -A tasks inspect active

# Controlla configurazione broker
python -c "from tasks import celery_app; print(celery_app.conf.broker_url)"
```

### Log e Debug

```bash
# Log dettagliati
python -m celery -A tasks worker --loglevel=debug

# Log su file
python -m celery -A tasks worker --loglevel=info --logfile=celery.log
```

## 📈 Performance Tuning

### Configurazione Worker
```python
# tasks.py - Modifica configurazione
celery_app.conf.update(
    worker_prefetch_multiplier=4,  # Aumenta per più task parallele
    worker_max_tasks_per_child=2000,  # Aumenta per meno restart
    task_acks_late=True,  # Migliore gestione errori
)
```

### Pool Worker
```bash
# Per CPU intensive
python -m celery -A tasks worker --pool=prefork --concurrency=4

# Per I/O intensive
python -m celery -A tasks worker --pool=gevent --concurrency=100
```

## 🔒 Sicurezza

### Redis Security
```bash
# Configura password Redis
redis-server --requirepass your_password

# Aggiorna configurazione Celery
REDIS_URL=redis://:password@localhost:6379/0
```

### Task Security
```python
# Limita task eseguibili
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Solo JSON
    result_serializer='json',
)
```

## 📚 Riferimenti

- [Documentazione Celery](https://docs.celeryproject.org/)
- [Documentazione Redis](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Best Practices Celery](https://www.celeryproject.org/best-practices.html)

---

**Nota**: Assicurati che Redis sia sempre in esecuzione prima di avviare i worker Celery. Le task falliranno se non riescono a connettersi al broker Redis.
