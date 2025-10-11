# 🐳 Docker Deployment per Archivista AI v2.4.0 (Alpha 2.4)

Questa guida spiega come eseguire Archivista AI v2.4.0 (Alpha 2.4) - **Phase 3: Intelligent Academic Ecosystem** utilizzando Docker e Docker Compose per un ambiente completamente containerizzato con architettura multi-pagina avanzata e sistema di gamification integrato.

## 📋 Prerequisiti

- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Docker Compose V2
- Almeno 4GB di RAM disponibile
- 2GB di spazio disco disponibile

## 🚀 Avvio Rapido con Docker

### ⚡ Iniziamo in 2 minuti!

#### Passo 1: Avvia Tutto Automaticamente
```bash
# Scarica il progetto e avvia tutti i servizi
git clone <repository-url>
cd archivista-ai

# Avvia tutti i servizi con un comando
docker-compose up -d
```

#### Passo 2: Verifica l'Installazione
```bash
# Controlla che tutti i servizi siano attivi
docker-compose ps

# Dovresti vedere:
# NAME                COMMAND                  SERVICE             STATUS
# archivista-redis    "docker-entrypoint.s…"   redis               running
# archivista-webapp   "streamlit run main.…"   webapp              running
# archivista-worker   "celery -A tasks wo…"   worker              running
```

#### Passo 3: Configura Ollama (IA)
```bash
# Verifica che Ollama sia in esecuzione sul sistema host
ollama list

# Se necessario, scarica i modelli richiesti
ollama pull llama3        # Per l'indicizzazione
ollama pull llava-llama3  # Per la chat multimodale
```

#### Passo 4: Accedi all'Applicazione
- 🌐 **Interfaccia Web**: http://localhost:8501
- 📊 **Dashboard Monitoraggio**: http://localhost:5555 (Flower)
- 🤖 **Ollama API**: http://localhost:11434 (host)

#### Passo 5: Test dell'Installazione
```bash
# Test connessione Redis
docker-compose exec redis redis-cli ping
# Risposta attesa: PONG

# Test worker Celery
docker-compose logs worker

# Test interfaccia web
# Apri http://localhost:8501 e verifica che carichi
```

### 🔧 Arresto e Pulizia
```bash
# Arresta tutti i servizi (mantieni dati)
docker-compose down

# Arresta e rimuovi tutto (cancella dati)
docker-compose down -v

# Pulizia completa del sistema Docker
docker system prune -a --volumes
```

## 📁 Struttura dei Servizi

### 🔴 Redis (Message Broker)
- **Immagine**: `redis:alpine`
- **Porta**: 6379
- **Funzione**: Message broker per Celery

### 🟡 Worker (Task Processing)
- **Build**: Dockerfile personalizzato
- **Comando**: `celery -A tasks worker --loglevel=info`
- **Funzione**: Elaborazione background dei documenti

### 🟢 Webapp (Interfaccia Utente)
- **Build**: Dockerfile personalizzato
- **Porta**: 8501
- **Comando**: `streamlit run main.py --server.port 8501 --server.address 0.0.0.0`
- **Accesso**: http://localhost:8501

## 📊 Monitoraggio e Debug

### Visualizza Log
```bash
# Log di tutti i servizi
docker-compose logs

# Log di un servizio specifico
docker-compose logs webapp
docker-compose logs worker
docker-compose logs redis

# Log in tempo reale
docker-compose logs -f
docker-compose logs -f worker
```

### Stato dei Servizi
```bash
# Stato di tutti i servizi
docker-compose ps

# Stato specifico
docker-compose ps webapp
```

### Accesso ai Container
```bash
# Accesso al container Webapp
docker-compose exec webapp bash

# Accesso al container Worker
docker-compose exec worker bash

# Accesso al container Redis
docker-compose exec redis redis-cli
```

## 📂 Gestione Dati

### Volumi Docker
- `redis_data`: Persistenza dati Redis
- `./db_memoria`: Database SQLite dell'applicazione
- `./documenti_da_processare`: Documenti da processare
- `./documenti_archiviati`: Documenti processati

### Backup Dati
```bash
# Backup manuali
docker run --rm -v $(pwd)/db_memoria:/backup -v archivista-redis:/redis alpine tar czf backup.tar.gz /backup /redis

# Restore
# 1. Arresta i servizi: docker-compose down
# 2. Ripristina i file
# 3. Riavvia: docker-compose up -d
```

## 🔧 Configurazione

### Variabili d'Ambiente
Il file `docker-compose.yml` configura automaticamente:
```yaml
environment:
  - REDIS_URL=redis://redis:6379/0
```

### Modifica Configurazione
```bash
# Modifica docker-compose.yml per personalizzazioni
nano docker-compose.yml

# Ricostruisci e riavvia
docker-compose up --build -d
```

## 🛠️ Sviluppo con Docker

### Modifiche al Codice
```bash
# Dopo modifiche al codice Python
docker-compose up --build -d

# Per modifiche solo al worker
docker-compose build worker
docker-compose up -d worker
```

### Debug Interattivo
```bash
# Avvia container in modalità interattiva
docker-compose run --rm worker bash

# Dentro il container
cd /app
python -c "from tasks import process_document_task; print('OK')"
```

## 🔍 Troubleshooting

### Problema: Porta Occupata
```bash
# Verifica porte occupate
netstat -an | grep :8501
netstat -an | grep :6379

# Modifica porte in docker-compose.yml
ports:
  - "8502:8501"  # Cambia porta Webapp
```

### Problema: Container non si Avvia
```bash
# Visualizza log dettagliati
docker-compose logs [service-name]

# Ricostruisci l'immagine
docker-compose build --no-cache [service-name]

# Rimuovi container e riavvia
docker-compose down
docker-compose up -d
```

### Problema: Redis Connection Error
```bash
# Verifica che Redis sia in esecuzione
docker-compose ps redis

# Log Redis
docker-compose logs redis

# Test connessione
docker-compose exec redis redis-cli ping
```

### Problema: Worker non Processa Task
```bash
# Verifica log worker
docker-compose logs worker

# Verifica connessione Redis
docker-compose exec worker python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Verifica task attive
docker-compose exec worker python -m celery -A tasks inspect active
```

## 📈 Performance Tuning

### Aumenta Worker
```yaml
# In docker-compose.yml
worker:
  command: celery -A tasks worker --loglevel=info --concurrency=4 --pool=solo
```

### Limiti Risorse
```yaml
# Aggiungi in docker-compose.yml
worker:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
```

## 🔒 Sicurezza

### Network Isolation
```yaml
# Aggiungi in docker-compose.yml
networks:
  archivista-network:
    driver: bridge

services:
  redis:
    networks:
      - archivista-network
  # ... altri servizi
```

### Environment Variables
```bash
# Crea file .env
REDIS_PASSWORD=your_secure_password
REDIS_URL=redis://:password@redis:6379/0

# Modifica docker-compose.yml
environment:
  - REDIS_URL=${REDIS_URL}
```

## 🧪 Test dell'Installazione

### 1. Test Redis
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### 2. Test Worker
```bash
# Invia un task di test
docker-compose exec worker python -c "
from tasks import check_for_new_documents
result = check_for_new_documents.delay()
print('Task ID:', result.id)
print('Status:', result.status)
"
```

### 3. Test UI
- Apri http://localhost:8501
- Verifica che l'interfaccia si carichi
- Controlla che lo stato mostri "Non avviato"

## 📚 Comandi Utili

### Gestione Servizi
```bash
# Avvia servizi
docker-compose up -d

# Arresta servizi
docker-compose down

# Riavvia servizi
docker-compose restart

# Ricostruisci immagini
docker-compose build --no-cache

# Aggiorna servizi
docker-compose up --build -d
```

### Pulizia
```bash
# Rimuovi container e network
docker-compose down

# Rimuovi anche i volumi (cancella dati)
docker-compose down -v

# Pulizia completa
docker system prune -a --volumes
```

## 🔄 Aggiornamento

### Da Versione Precedente
```bash
# 1. Backup dati importanti
cp -r db_memoria db_memoria.backup
cp -r documenti_archiviati documenti_archiviati.backup

# 2. Scarica aggiornamenti
git pull

# 3. Ricostruisci e riavvia
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📞 Supporto

Se incontri problemi:

1. **Controlla i log**: `docker-compose logs -f`
2. **Verifica stato servizi**: `docker-compose ps`
3. **Test connessione Redis**: `docker-compose exec redis redis-cli ping`
4. **Controlla documentazione**: `CELERY_README.md`

## 🎯 Vantaggi di Docker

- ✅ **Ambiente isolato**: Nessun conflitto con sistema host
- ✅ **Facile deployment**: Un comando per avviare tutto
- ✅ **Consistenza**: Stesso ambiente su qualsiasi sistema
- ✅ **Scalabilità**: Facile aggiungere più worker
- ✅ **Portabilità**: Funziona su Windows, Mac, Linux
- ✅ **Gestione semplificata**: Volumi per persistenza dati

---

**Docker semplifica l'installazione e l'utilizzo di Archivista AI, fornendo un ambiente consistente e facilmente gestibile.**
