# 📚 Archivista AI v2.5.0 (Alpha 2.5) - **Phase 4: Production-Ready Intelligent Document Management** 🚀🏭

**Sistema Enterprise-Ready per l'Archiviazione, Elaborazione e Monitoraggio di Documenti con Framework di Diagnosi Errori Avanzato**

Archivista AI è un'applicazione web avanzata **production-ready** che utilizza l'intelligenza artificiale per processare, indicizzare e rendere interrogabili documenti scientifici e accademici pesanti. Il sistema integra un **framework completo di diagnosi e gestione errori** con **monitoraggio avanzato** e **deployment ottimizzato per documenti di grandi dimensioni**.

## ✨ Caratteristiche Principali

### 🤖 **Core AI Features**
- 💬 **Chat Multi-Modale**: Interfaccia conversazionale avanzata con supporto immagini e documenti
- 🔍 **Ricerca Semantica**: Motore di ricerca intelligente con comprensione del contesto
- 📝 **Editor Avanzato**: Modifica professionale delle anteprime con editor rich-text
- 🗂️ **Archivio Intelligente**: Organizzazione automatica e categorizzazione dei documenti
- 🎓 **Planner Accademico**: Gestione completa corsi, lezioni e attività didattiche
- 🧠 **Grafo della Conoscenza**: Mappa interattiva delle connessioni concettuali con confidence scoring
- 🎮 **Sistema Gamificato**: XP, achievement e monitoraggio progresso accademico

### 🚨 **Enterprise Error Management**
- 🔍 **Framework Diagnosi Errori**: Classificazione automatica errori con 10 stati di processamento
- 🔄 **Sistema Retry Intelligente**: Backoff esponenziale con limiti categoria-specifici
- 🚫 **Quarantena Automatica**: Isolamento file problematici con analisi dettagliata
- 📊 **Monitoraggio Avanzato**: Metriche real-time di sistema, processamento ed errori
- 📧 **Alerting Intelligente**: Notifiche email per condizioni critiche con anti-spam
- 💚 **Health Checks**: Verifica salute componenti con report dettagliati

### 🏭 **Production-Ready Features**
- 🐳 **Containerizzazione Ottimizzata**: Multi-stage build con sicurezza hardening
- ⚙️ **Configurazione Produzione**: Resource limits ottimizzati per documenti pesanti
- 🔧 **Deployment Automatizzato**: Script automatico con verifica prerequisiti
- 📈 **Performance Monitoring**: Tracking throughput e utilizzo risorse
- 💾 **Backup Automatici**: Backup giornalieri con retention management
- 🌐 **Load Balancing**: Architettura high-availability per scalability

### 🔧 **Technical Excellence**
- 🤖 **Elaborazione AI**: Estrazione automatica di metadati, riassunti e anteprime
- 🔄 **Elaborazione Asincrona**: Processamento in background con Celery e Redis
- 📊 **Dashboard Unificata**: Interfaccia web moderna con integrazione completa
- 🔐 **Persistenza Dati**: Database SQLite avanzato con backup automatico
- 📋 **Logging Strutturato**: Log JSON con correlation ID e analisi avanzata

## 📱 Architettura Multi-Pagina

L'applicazione utilizza un'architettura multi-pagina ottimizzata per diverse funzionalità:

### 💬 **Chat** (Pagina Principale)
- **Interfaccia conversazionale** con i documenti
- **Supporto multimodale** (testo + immagini)
- **Ricerca semantica** in tempo reale
- **Chat history** e contesto persistente

### 🗂️ **Archivio**
- **Esplorazione documenti** con filtri avanzati
- **Visualizzazione metadati** estratti dall'AI
- **Ricerca full-text** e semantica
- **Gestione categorie** e organizzazione

### 📝 **Editor**
- **Editor rich-text avanzato** con Streamlit Quill
- **Modifica anteprime** generate dall'AI
- **Visualizzatore documenti** affiancato
- **Auto-salvataggio** e validazione modifiche

### ✨ **Nuovo**
- **Creazione documenti** direttamente nell'app
- **Template personalizzati** per diversi tipi di contenuto
- **Integrazione AI** per generazione assistita
- **Salvataggio automatico** nel database

## 🚀 Avvio Rapido

### ⚡ Iniziamo in 3 minuti!

#### Opzione 1: Deployment Produzione (Raccomandato per Documenti Pesanti)

```bash
# 1. Deploy automatico ottimizzato per documenti pesanti
chmod +x deploy.sh
./deploy.sh

# 2. Verifica servizi production-ready
docker-compose -f docker-compose.prod.yml ps

# 3. Accesso interfacce enterprise
# 🌐 Dashboard Unificata: http://localhost:8501
# 📊 Monitoraggio Celery: http://localhost:5555
# 🔬 Monitoraggio Avanzato: http://localhost:8501 (tab Monitoraggio)
```

#### Opzione 2: Sviluppo Standard

```bash
# 1. Avvia servizi base
docker-compose up -d

# 2. Verifica servizi
docker-compose ps

# 3. Accesso sviluppo
# 🌐 Web UI: http://localhost:8501
# 📊 Monitor: http://localhost:5555
```

#### Opzione 3: Installazione Manuale

```bash
# 1. Installa e avvia Redis
start_redis.bat

# 2. Installa dipendenze Python (include framework errori avanzato)
pip install -r requirements.txt

# 3. Avvia worker con configurazione ottimizzata
start_celery_worker.bat

# 4. Avvia applicazione con framework diagnosi errori
streamlit run main_new_architecture.py

# 5. Accesso: http://localhost:8501
```

#### ⚠️ Prerequisiti per Ollama (IA)

Prima di iniziare, assicurati che **Ollama** sia installato e in esecuzione:

```bash
# Verifica modelli disponibili
ollama list

# Se necessario, scarica i modelli richiesti
ollama pull llama3        # Per processamento documenti
ollama pull llava-llama3  # Per chat multimodale
```

### 🎯 Deployment Produzione per Documenti Pesanti

Per utilizzo con molti documenti pesanti, utilizza il deployment ottimizzato:

```bash
# Deploy produzione completo
./deploy.sh

# Servizi ottimizzati:
# 🟡 Webapp (4GB RAM) - Dashboard con framework errori
# 🟢 Worker (8GB RAM) - Processamento documenti pesanti
# 🔴 Redis (256MB) - Message broker ottimizzato
# 🟠 Flower - Monitoraggio avanzato
# 🔵 Beat - Scheduler task periodici
# 🟣 Backup - Backup automatici giornalieri
```

**Interfacce Disponibili:**
- 🌐 **Dashboard Unificata**: http://localhost:8501 (tutte le funzionalità integrate)
- 📊 **Monitoraggio Celery**: http://localhost:5555 (task queue avanzata)
- 🔬 **Monitoraggio Sistema**: http://localhost:8501 (health checks e metriche)
- 📋 **Log Centralizzati**: Accessibili tramite dashboard

## 📋 Prerequisiti

- **Python**: 3.11+
- **Redis**: Server Redis in esecuzione
- **RAM**: Almeno 4GB
- **Spazio**: 2GB disponibile
- **Docker**: (Opzionale) Per deployment containerizzato

## 🏗️ Architettura del Sistema

### Componenti Principali

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Celery Worker │    │     Redis       │
│                 │    │                 │    │   (Message      │
│ - Interfaccia   │    │ - Task Processing│    │    Broker)      │
│ - Upload File   │    │ - AI Processing │    │                 │
│ - Query Engine  │    │ - Indexing      │    │ - Task Queue    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   LlamaIndex    │
                    │                 │
                    │ - Vector Store  │
                    │ - Embeddings    │
                    │ - LLM Models    │
                    └─────────────────┘
```

### Tecnologie Utilizzate

- **Frontend**: Streamlit 1.49.1
- **AI Framework**: LlamaIndex 0.14.2
- **Task Queue**: Celery 5.5.3 + Redis 5.2.1
- **Database**: SQLite con SQLAlchemy
- **Document Processing**: PyMuPDF, python-docx
- **Container**: Docker + Docker Compose
- **ML Models**: HuggingFace Transformers, Sentence Transformers

## 📁 Struttura del Progetto

```
archivista-ai/
├── 📄 main.py                 # Applicazione Streamlit principale
├── 📄 tasks.py                # Configurazione Celery e task
├── 📄 archivista_processing.py # Task specifiche per l'archiviazione
├── 📄 config.py               # Configurazione LlamaIndex
├── 📄 file_utils.py           # Utilità per la gestione file
├── 📄 tools.py                # Strumenti AI e ricerca web
├── 📄 prompt_manager.py       # Gestione prompt LLM
├── 📄 requirements.txt        # Dipendenze Python
├── 📄 requirements.in         # Dipendenze di base
├── 🐳 Dockerfile             # Containerizzazione
├── 🐳 docker-compose.yml     # Orchestrazione servizi
├── 📚 CELERY_README.md       # Documentazione Celery
├── 📚 DOCKER_README.md       # Documentazione Docker
├── 📚 README.md              # Questo file
├── 📁 pages/                 # Pagine dell'applicazione multi-pagina
│   ├── 1_💬_Chat.py          # Chat principale (conversazionale)
│   ├── 2_🗂️_Archivio.py      # Esplorazione e gestione archivio
│   ├── 3_📝_Editor.py         # Editor avanzato anteprime
│   ├── 4_✨_Nuovo.py          # Creazione nuovi documenti
│   ├── 5_🎓_Carriera.py       # Planner accademico con IA
│   └── 6_🧠_Grafo.py          # Grafo delle connessioni concettuali
└── 📁 db_memoria/            # Database e indici
    ├── metadata.sqlite       # Database metadati
    ├── index_store.json      # Store degli indici
    └── vector_store.json     # Vector store
```

## 🔧 Configurazione

### Variabili d'Ambiente

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434

# Directory
DOCS_TO_PROCESS_DIR=documenti_da_processare
PROCESSED_DOCS_DIR=documenti_archiviati
DB_STORAGE_DIR=db_memoria
```

### Configurazione LLM

Il sistema utilizza un'architettura duale per ottimizzare le prestazioni:

- **llama3**: Per l'indicizzazione e l'estrazione metadati (veloce e stabile)
- **llava-llama3**: Per la chat multimodale (supporta testo e immagini)

**Prerequisiti:**
- **Ollama** deve essere installato e in esecuzione sul sistema host
- I modelli `llama3` e `llava-llama3` devono essere scaricati

**Modelli Supportati:**
- **Ollama** (default): Modelli locali con supporto multimodale
- **OpenAI**: GPT-3.5, GPT-4 (richiede API key)
- **HuggingFace**: Modelli open-source

## 📖 Guida Utente

### Utilizzo Base

1. **Caricamento Documenti**
   - Copia i file PDF/DOCX nella cartella `documenti_da_processare/`
   - Clicca su "🔍 Scansiona nuovi documenti" nell'interfaccia
   - I documenti vengono processati automaticamente in background

2. **Ricerca e Interrogazione**
   - Utilizza la chat per interrogare i documenti
   - Applica filtri per autore, anno, o documento specifico
   - Visualizza anteprime AI e metadati estratti

3. **Gestione Archivio**
   - Modifica metadati dei documenti
   - Elimina documenti non più necessari
   - Esporta risultati di ricerca

### Funzionalità Avanzate

- **Ricerca Semantica**: Comprensione del contesto e significato
- **Filtri Intelligenti**: Filtraggio per metadati e contenuto
- **Anteprime AI**: Riassunti automatici generati dall'IA
- **Elaborazione Batch**: Processamento multiplo di documenti
- **Monitoraggio**: Dashboard per tracciare l'elaborazione

## 🐳 Deployment con Docker

### Servizi Disponibili

- **Webapp**: Interfaccia utente (http://localhost:8501)
- **Worker**: Elaborazione background documenti
- **Redis**: Message broker e cache
- **Flower**: Monitoraggio task (http://localhost:5555)

### Comandi Docker

```bash
# Avvia tutti i servizi
docker-compose up -d

# Visualizza log
docker-compose logs -f

# Arresta servizi
docker-compose down

# Ricostruisci immagini
docker-compose up --build -d
```

## 🔍 Troubleshooting

### Problemi Comuni

1. **Ollama non raggiungibile**
   ```bash
   # Verifica che Ollama sia in esecuzione
   ollama list

   # Avvia Ollama
   ollama serve

   # Scarica i modelli necessari
   ollama pull llama3
   ollama pull llava-llama3
   ```

2. **Redis non si avvia**
   ```bash
   # Verifica che Redis sia installato
   redis-cli ping

   # Avvia Redis manualmente
   redis-server
   ```

3. **Worker Celery non risponde**
   ```bash
   # Verifica connessione Redis
   python -c "import redis; r=redis.Redis(); print(r.ping())"

   # Riavvia worker
   docker-compose restart worker
   ```

4. **Documenti non processati**
   ```bash
   # Verifica log worker
   docker-compose logs worker

   # Controlla cartella documenti
   ls -la documenti_da_processare/
   ```

5. **Errore "LLM non disponibile"**
   - Verifica che Ollama sia in esecuzione
   - Controlla che i modelli siano scaricati
   - Verifica la connessione di rete
   - Controlla i log dell'applicazione

6. **Errore modulo "statistics"**
   - Il modulo `statistics.py` è stato rinominato in `archive_statistics.py`
   - Se vedi errori di importazione, aggiorna i tuoi script
   - Usa: `from archive_statistics import get_comprehensive_stats`

### Log e Debug

```bash
# Log completi
docker-compose logs -f

# Log specifico servizio
docker-compose logs webapp
docker-compose logs worker

# Accesso container
docker-compose exec webapp bash
docker-compose exec worker bash
```

## 📈 Performance

### Ottimizzazioni

- **Worker Paralleli**: Configura più worker per elaborazione simultanea
- **Chunk Size**: Ottimizza la dimensione dei chunk per l'indicizzazione
- **Cache Redis**: Utilizza Redis per caching intelligente
- **Modelli LLM**: Scegli modelli appropriati per le tue esigenze

### Monitoraggio

- **Flower Dashboard**: Monitora task e performance
- **Redis Insight**: Analizza l'utilizzo della memoria
- **Log Analysis**: Controlla i log per identificare bottleneck

## 🔒 Sicurezza

- **Container Isolation**: Servizi isolati in container Docker
- **Network Security**: Configurazione di rete sicura
- **Data Encryption**: Crittografia dei dati sensibili
- **Access Control**: Controllo degli accessi all'interfaccia

## 🤝 Contribuire

### Linee Guida per i Contributi

1. Fork il repository
2. Crea un branch per la tua feature (`git checkout -b feature/nuova-feature`)
3. Committa i tuoi cambiamenti (`git commit -am 'Aggiungi nuova feature'`)
4. Push al branch (`git push origin feature/nuova-feature`)
5. Crea una Pull Request

### Struttura del Codice

- **Modularità**: Codice organizzato in moduli separati
- **Documentazione**: Commenti e docstring per tutte le funzioni
- **Testing**: Test unitari per le funzionalità critiche
- **Type Hints**: Annotazioni di tipo per Python

## 📚 Documentazione Dettagliata

### 🚨 **Framework Diagnosi Errori**
- **[Framework Errori](error_diagnosis_framework.py)**: Sistema completo diagnosi e gestione errori
- **[Sistema Retry](retry_framework.py)**: Retry intelligente con backoff esponenziale
- **[Monitoraggio Avanzato](advanced_monitoring.py)**: Metriche e alerting avanzati

### 🐳 **Deployment Produzione**
- **[Deploy Produzione](PRODUCTION_README.md)**: Guida completa deployment enterprise
- **[Docker Produzione](docker-compose.prod.yml)**: Configurazione ottimizzata documenti pesanti
- **[Script Deploy](deploy.sh)**: Automazione deployment con verifiche

### 🔧 **Documentazione Tecnica**
- **[Guida Celery](CELERY_README.md)**: Configurazione task queue e Redis
- **[Guida Docker](DOCKER_README.md)**: Deployment containerizzato
- **[API Reference](docs/api.md)**: Documentazione API (se disponibile)

### 📊 **Dashboard e Monitoraggio**
- **[Dashboard Unificata](unified_dashboard.py)**: Interfaccia integrata tutti i componenti
- **[Monitoraggio Dashboard](monitoring_dashboard.py)**: Dashboard dedicata monitoraggio
- **[Demo Integrazione](integration_demo.py)**: Demo completa tutti i framework

## 🔄 Changelog

### Versione 3.0.0 - Ottobre 2025 - **Phase 4: Production-Ready Enterprise Document Management** 🚀🏭

**🏭 Rivoluzione Enterprise: Dal Sistema Personale al Framework Aziendale**

**🚨 Framework Completo Diagnosi e Gestione Errori:**
- ✅ **10 Stati di Processamento**: PENDING → QUEUED → PROCESSING → FAILED_* → COMPLETED
- ✅ **Classificazione Automatica Errori**: Categorizzazione intelligente per tipo e severità
- ✅ **Sistema Quarantena**: Isolamento automatico file problematici con metadati
- ✅ **Logging Strutturato**: Log JSON con correlation ID e analisi avanzata
- ✅ **Error Recovery**: Strategie di recovery automatico con retry intelligente

**🔄 Sistema Retry Avanzato:**
- ✅ **Backoff Esponenziale**: Algoritmo intelligente con jitter per evitare thundering herd
- ✅ **Retry Categoria-Specifici**: Limiti diversi basati su tipo errore (IOError: 5 retry, APIError: 2 retry)
- ✅ **Queue Management**: Gestione code priorità per documenti pesanti
- ✅ **Smart Retry Scheduling**: Calcolo automatico tempi ottimali per retry
- ✅ **Retry Analytics**: Monitoraggio e analisi pattern retry

**📊 Monitoraggio e Alerting Avanzato:**
- ✅ **Metriche Real-time**: Sistema, processamento, errori, performance
- ✅ **Health Checks Multi-componente**: Database, AI services, file system, worker
- ✅ **Alerting Intelligente**: Email notifications con anti-spam e soglie configurabili
- ✅ **Dashboard Unificata**: Integrazione completa tutti i componenti
- ✅ **Performance Tracking**: Throughput, utilizzo risorse, trend storici

**🏭 Deployment Produzione Ottimizzato:**
- ✅ **Docker Multi-stage**: Build ottimizzato con sicurezza hardening
- ✅ **Resource Management**: 8GB worker, 4GB webapp per documenti pesanti
- ✅ **Automated Backup**: Backup giornalieri con retention 7 giorni
- ✅ **Log Rotation**: Gestione automatica log con compressione
- ✅ **Production Script**: Deploy automatico con verifiche prerequisiti

**🎛️ Dashboard Integration:**
- ✅ **Unified Interface**: Dashboard singola per tutti i componenti
- ✅ **Real-time Progress**: Tracking live progresso processamento
- ✅ **Failed Files Management**: Interface interattiva gestione file problematici
- ✅ **Error Trend Analysis**: Analisi pattern e trend errori storici
- ✅ **Interactive Actions**: Azioni correttive direttamente da dashboard

**🔧 Technical Architecture:**
- ✅ **Modular Framework**: Componenti indipendenti e integrabili
- ✅ **Production Configuration**: File configurazione ottimizzati documenti pesanti
- ✅ **Security Hardening**: User non-root, network isolation, resource limits
- ✅ **Scalability Ready**: Architettura predisposta per scaling orizzontale
- ✅ **Enterprise Monitoring**: Integrazione Prometheus/Grafana ready

### Versione 2.4.0 (Alpha 2.4) - Novembre 2025 - **Phase 3: Intelligent Academic Ecosystem** 🎓🤖

**🎯 Rivoluzione dell'Apprendimento: Dal Document Organizer all'AI Study Companion**

**🧠 Sistema Gamificato:**
- ✅ **XP & Achievement System**: Guadagna punteggi per attività di apprendimento
- ✅ **Gamification del Learning**: Achievement, badge e traguardi motivazionali
- ✅ **Tracking Performance**: Progressi quanti e storici di apprendimento
- ✅ **Studio Sessions**: Registrazione sessioni di studio con rating produttività

**🎓 Academic Planner Integrato:**
- ✅ **6° Pagina Specializzata**: Carriera accademica completa
- ✅ **Course Management**: Corsi universitari con lezioni e materiali associati
- ✅ **Task Generation AI**: Creazione automatica di attività di apprendimento
- ✅ **Study Planning**: Pianificazione intelligente degli obiettivi accademici

**🧠 Dynamic Knowledge Graph:**
- ✅ **7° Pagina**: Grafo interattivo delle connessioni concettuali
- ✅ **Entity Extraction**: entities concettuali, teorie, autori, formule
- ✅ **Relationship Mapping**: Scoperta connessioni semantiche con confidence scores
- ✅ **Interactive Navigation**: Esplorazione entità e loro vicinanza concettuale

**📊 Database Evoluto:**
- ✅ **Nuove Tabelle**: concept_entities, concept_relationships, user_xp, achievements
- ✅ **Graph Database Capabilities**: Funzionalità avanzate per mappare conoscenze
- ✅ **Entity-Relationship Storage**: Memorizzazione relazioni fra concetti

**🤖 Processing Pipeline Esteso:**
- ✅ **Academic AI Prompts**: Analisi didattica specializzata per NLP
- ✅ **Knowledge Discovery**: Algoritmi avanzati per trovare connessioni nascoste
- ✅ **Multi-layer Analysis**: Keywords + Entities + Relationships profondi

**🔄 User Experience Evoluta:**
- ✅ **Cross-page Navigation**: Collegamenti fra grafi e materiali accademici
- ✅ **Unified Academic Dashboard**: Vista unificata del progresso didattico
- ✅ **Smart Recommendations**: Suggerimenti basati sui pattern di apprendimento

**🔧 Technical Enhancements:**
- ✅ **NetworkX Integration**: Libreria per visualizzazione grafi complessa
- ✅ **Optimized Graph Operations**: Performance elevate per big knowledge graphs
- ✅ **Scalable Entity Storage**: Database ottimizzato per migliaia di entity

**📚 Certification & Achievements:**
- ✅ **Study Streaks**: Ricompense per apprendimento consistente
- ✅ **Course Completion**: Badge per completamento corsi
- ✅ **Knowledge Master**: Traguardi per profondità di comprensione

### Versione 2.2.0 (Alpha 2.2) - Dicembre 2024

**🆕 Nuove Funzionalità:**
- ✅ Sistema di elaborazione asincrona Celery
- ✅ Containerizzazione Docker completa
- ✅ Dashboard di monitoraggio Flower
- ✅ Sistema di status in tempo reale

**🔧 Miglioramenti:**
- ✅ Ottimizzazione performance processamento
- ✅ Migliore gestione errori e recovery
- ✅ Interfaccia utente migliorata

### Versioni Precedenti

- **v1.0.0**: Release iniziale con funzionalità base

## 📞 Supporto

### Community

- **GitHub Issues**: Segnala bug e richiedi feature
- **Discussions**: Discussioni sulla community
- **Documentation**: Controlla la documentazione aggiornata

### Contatti

- **Email**: support@archivista-ai.com
- **GitHub**: https://github.com/your-repo/archivista-ai
- **Documentation**: https://docs.archivista-ai.com

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🙏 Ringraziamenti

- **LlamaIndex Team**: Per l'eccellente framework AI
- **Streamlit Team**: Per l'interfaccia web intuitiva
- **Celery Team**: Per il sistema di task queue robusto
- **Open Source Community**: Per le librerie e tool utilizzati

---

**Archivista AI** - Porta l'intelligenza artificiale nel tuo archivio documentale 🚀
