# 🚀 Production Deployment - Archivista AI v2.5.0 - **CENTRALIZZAZIONE COMPLETATA**

## Guida Completa per Deployment in Produzione

Questa guida fornisce tutto il necessario per deployare **Archivista AI v2.5.0** in ambiente di produzione, ottimizzato per il processamento di molti documenti pesanti in modalità single-user con **centralizzazione completata** e **dashboard unificata production-ready**.

**✅ STATO ATTUALE**: 8 Settimane Completate | 254 Test | 30/30 Deployment Tasks | Production-Ready

## 📋 Sommario

- [🚀 Avvio Rapido](#-avvio-rapido)
- [🏗️ Architettura di Produzione](#️-architettura-di-produzione)
- [⚙️ Configurazione](#️-configurazione)
- [📊 Monitoraggio](#-monitoraggio)
- [🔧 Manutenzione](#-manutenzione)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📈 Ottimizzazioni](#-ottimizzazioni)

## 🚀 Avvio Rapido

### Prerequisiti
- Docker e Docker Compose
- Minimo 8GB RAM, 100GB disco
- Python 3.11+ (per sviluppo)

### Deploy Automatico
```bash
# 1. Clona il repository
git clone <repository-url>
cd archivista-ai

# 2. Avvia tutto automaticamente
chmod +x deploy.sh
./deploy.sh

# 3. Verifica l'installazione
docker-compose -f docker-compose.prod.yml ps
```

### Accesso alle Interfacce
- 🌐 **Dashboard principale**: http://localhost:8501
- 📊 **Monitoraggio Celery**: http://localhost:5555
- 📚 **Documentazione**: http://localhost:8501 (tab "Docs")

## 🏗️ Architettura di Produzione

```
┌─────────────────────────────────────────────────────────────────┐
│                    🐳 DOCKER PRODUCTION STACK                   │
├─────────────────────────────────────────────────────────────────┤
│  🟡 Webapp (4GB RAM)      │  🟢 Worker (8GB RAM)             │
│  • Streamlit Dashboard    │  • Document Processing           │
│  • Error Framework UI     │  • AI Model Integration          │
│  • Real-time Monitoring   │  • Bayesian Knowledge Engine     │
│  • User Interface         │  • Retry Logic                   │
├─────────────────────────────────────────────────────────────────┤
│  🟠 Flower (Monitoring)   │  🔵 Beat (Scheduler)             │
│  • Celery Dashboard       │  • Periodic Tasks                │
│  • Task Queue Monitor     │  • Health Checks                 │
│  • Performance Metrics     │  • Backup Scheduling             │
├─────────────────────────────────────────────────────────────────┤
│  🔴 Redis (256MB)         │  🟣 Backup (Automated)           │
│  • Message Broker          │  • Daily Backups                 │
│  • Task Queue              │  • Retention Management          │
│  • Cache Storage           │  • Archive Management            │
├─────────────────────────────────────────────────────────────────┤
│  🟤 Log Rotation          │  📁 Persistent Volumes           │
│  • Automatic Log Cleanup   │  • Document Storage              │
│  • Archive Management      │  • Database Persistence          │
│  • Size Management         │  • Configuration Storage         │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Configurazione

### File di Configurazione

#### `docker-compose.prod.yml`
```yaml
# Servizi ottimizzati per documenti pesanti
webapp:
  deploy:
    resources:
      limits:
        memory: 4G    # Memoria per UI e documenti
        cpus: '1.0'
      reservations:
        memory: 2G
        cpus: '0.5'

worker:
  deploy:
    resources:
      limits:
        memory: 8G    # Memoria elevata per processing
        cpus: '2.0'
      reservations:
        memory: 4G
        cpus: '1.0'
```

#### Configurazione Redis Ottimizzata
```bash
# redis.conf - Configurazione produzione
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
save 900 1
```

#### Configurazione Celery
```python
# config/celery_config.py
task_soft_time_limit = 600  # 10 minuti per documenti pesanti
task_time_limit = 900       # 15 minuti max
worker_max_tasks_per_child = 50
```

### Variabili d'Ambiente

#### Produzione
```bash
# .env.production
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://host.docker.internal:11434
STREAMLIT_SERVER_HEADLESS=true
CELERY_WORKER_CONCURRENCY=2
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

#### Sviluppo
```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379/0
```

## 📊 Monitoraggio

### Dashboard Unificata
- **URL**: http://localhost:8501
- **Funzionalità**:
  - 📊 Stato processamento real-time
  - 🚨 Gestione errori e quarantena
  - 🔄 Sistema retry intelligente
  - 📈 Analisi trend e performance

### Celery Flower
- **URL**: http://localhost:5555
- **Monitoraggio**:
  - Task queue status
  - Worker performance
  - Task execution history
  - Error tracking

### Health Checks
```bash
# Verifica salute servizi
curl http://localhost:8501/_stcore/health
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Monitoraggio risorse
docker stats
```

### Log Centralizzati
```bash
# Visualizza tutti i log
docker-compose -f docker-compose.prod.yml logs -f

# Log specifici
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f webapp

# Log con filtri
docker-compose -f docker-compose.prod.yml logs -f | grep ERROR
```

## 🔧 Manutenzione

### Backup Automatici
- **Frequenza**: Giornaliera
- **Retention**: 7 giorni
- **Location**: `./backups/`
- **Comando manuale**:
```bash
docker-compose -f docker-compose.prod.yml exec backup \
  tar czf /archive/backup-manual-$(date +%Y%m%d-%H%M%S).tar.gz -C /backup .
```

### Aggiornamenti
```bash
# 1. Backup preventivo
./deploy.sh backup

# 2. Aggiorna codice
git pull

# 3. Deploy aggiornamenti
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# 4. Verifica
docker-compose -f docker-compose.prod.yml ps
```

### Pulizia Sistema
```bash
# Pulizia container fermi
docker container prune -f

# Pulizia immagini dangling
docker image prune -f

# Pulizia volumi inutilizzati
docker volume prune -f

# Pulizia completa
docker system prune -a --volumes
```

## 🛠️ Troubleshooting

### Problemi Comuni

#### 1. Servizi non si avviano
```bash
# Verifica log dettagliati
docker-compose -f docker-compose.prod.yml logs [service-name]

# Verifica risorse disponibili
docker system df

# Verifica conflitti porte
netstat -tulpn | grep :8501
```

#### 2. Worker non processa documenti
```bash
# Verifica connessione Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Verifica configurazione Celery
docker-compose -f docker-compose.prod.yml exec worker python -c "
import redis
r = redis.Redis(host='redis', port=6379)
print('Redis connection:', r.ping())
"

# Verifica servizi AI
docker-compose -f docker-compose.prod.yml exec worker python -c "
from config import initialize_services
try:
    initialize_services()
    print('AI services: OK')
except Exception as e:
    print('AI services error:', e)
"
```

#### 3. Memoria insufficiente
```bash
# Verifica utilizzo memoria
docker stats

# Aumenta limiti nel docker-compose.prod.yml
services:
  worker:
    deploy:
      resources:
        limits:
          memory: 12G  # Aumenta se necessario
```

#### 4. Errori di processamento documenti
```bash
# Verifica log worker
docker-compose -f docker-compose.prod.yml logs worker | tail -50

# Verifica stato documenti
docker-compose -f docker-compose.prod.yml exec webapp python -c "
from error_diagnosis_framework import get_processing_status_summary
import json
print(json.dumps(get_processing_status_summary(), indent=2))
"
```

### Debug Avanzato

#### Accesso ai Container
```bash
# Accesso interattivo
docker-compose -f docker-compose.prod.yml exec webapp bash
docker-compose -f docker-compose.prod.yml exec worker bash

# Debug Python
docker-compose -f docker-compose.prod.yml exec worker python -c "
from archivista_processing import process_document_task
print('Processing function available')
"
```

#### Analisi Performance
```bash
# Metriche sistema
docker-compose -f docker-compose.prod.yml exec webapp python -c "
from advanced_monitoring import get_system_status
import json
status = get_system_status()
print(json.dumps(status, indent=2))
"
```

## 📈 Ottimizzazioni

### Per Documenti Molto Pesanti

#### 1. Chunked Processing
```python
# In archivista_processing.py
CHUNK_SIZE = 1000  # Processa documenti in chunk da 1000 pagine
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB max per documento
```

#### 2. Memory Management
```python
# Configurazione ottimizzata
WORKER_MEMORY_LIMIT = "8G"
WORKER_CPU_LIMIT = "2.0"
WORKER_CONCURRENCY = 1  # Un documento alla volta per documenti pesanti
```

#### 3. Storage Optimization
```yaml
# Volumi separati per performance
volumes:
  document_processing:
    driver_opts:
      type: tmpfs  # Storage temporaneo veloce
      device: tmpfs
```

### Scalabilità Verticale

#### Aumentare Risorse
```bash
# Per documenti molto pesanti, aumenta risorse
services:
  worker:
    deploy:
      resources:
        limits:
          memory: 16G  # Per documenti >100MB
          cpus: '4.0'  # Più CPU per processing parallelo
```

#### Ottimizzazioni Database
```sql
-- Indici ottimizzati per documenti pesanti
CREATE INDEX idx_processing_status_file_state ON document_processing_status(file_name, processing_state);
CREATE INDEX idx_error_log_category_severity ON processing_error_log(error_category, error_type);
```

## 🔒 Sicurezza

### Configurazione di Sicurezza
```bash
# Crea certificati SSL (opzionale)
openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes

# Configura firewall
ufw allow 8501
ufw allow 5555
```

### Hardening Container
```dockerfile
# Security hardening nel Dockerfile.prod
RUN useradd --create-home --shell /bin/bash --uid 1000 archivista
USER archivista

# Rimuovi tool non necessari
RUN apt-get purge -y gcc g++ build-essential && apt-get autoremove -y
```

## 📋 Checklist Pre-Produzione

### Prima del Deployment
- [ ] Verifica spazio disco (minimo 100GB)
- [ ] Test connessione Ollama
- [ ] Configura modelli AI necessari
- [ ] Test processamento documento di prova
- [ ] Verifica backup automatico
- [ ] Configura monitoring alerts

### Dopo il Deployment
- [ ] Verifica tutte le interfacce web
- [ ] Test processamento documento
- [ ] Controlla log per errori
- [ ] Verifica backup automatico
- [ ] Test ripristino da backup
- [ ] Configura monitoring alerts

## 📞 Supporto

### Log Importanti
```bash
# Log applicazione
docker-compose -f docker-compose.prod.yml logs webapp

# Log processamento
docker-compose -f docker-compose.prod.yml logs worker

# Log errori
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

### Metriche da Monitorare
- **CPU Usage**: Mantenere sotto 80%
- **Memory Usage**: Mantenere sotto 90%
- **Disk Space**: Mantenere sopra 20% libero
- **Error Rate**: Mantenere sotto 10%
- **Processing Queue**: Monitorare lunghezza coda

### Contatti e Documentazione
- 📚 **Documentazione**: `DOCS/` directory
- 🐛 **Issues**: GitHub Issues
- 📖 **API Docs**: http://localhost:8501 (Docs tab)

## 🎯 Ottimizzazioni Specifiche

### Per il Tuo Caso d'Uso (Documenti Pesanti)

#### 1. Configurazione Worker Ottimizzata
```yaml
worker:
  environment:
    - CELERY_WORKER_PREFETCH_MULTIPLIER=1  # Un task alla volta
    - CELERY_TASK_ACKS_LATE=1              # Ack dopo processamento
    - CELERYD_MAX_TASKS_PER_CHILD=25       # Riavvio dopo 25 task
```

#### 2. Memory Management
```python
# In configurazione
MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100MB max
CHUNK_SIZE = 500                       # Chunk più piccoli
PROCESSING_TIMEOUT = 1800              # 30 minuti timeout
```

#### 3. Storage Strategy
```yaml
# Volumi ottimizzati
volumes:
  hot_storage:  # Documenti attivi
    driver_opts:
      type: tmpfs
  warm_storage: # Documenti recenti
    driver_opts:
      type: none
      o: bind
      device: ./recent_docs
  cold_storage: # Archivio storico
    driver_opts:
      type: none
      o: bind
      device: ./archive
```

## 🚀 Comandi Rapidi

```bash
# Avvio completo
./deploy.sh

# Stato servizi
docker-compose -f docker-compose.prod.yml ps

# Log real-time
docker-compose -f docker-compose.prod.yml logs -f

# Backup manuale
docker-compose -f docker-compose.prod.yml exec backup \
  tar czf /archive/backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /backup .

# Health check
curl http://localhost:8501/_stcore/health

# Riavvio servizi
docker-compose -f docker-compose.prod.yml restart

# Stop completo
docker-compose -f docker-compose.prod.yml down
```

---

**🎉 Congratulazioni! Il tuo sistema Archivista AI è ora deployato in produzione e ottimizzato per processare molti documenti pesanti in modalità single-user.**

**Monitora sempre i log e le metriche per garantire prestazioni ottimali!**
