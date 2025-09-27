# 📚 Archivista AI v1.3.0 (Alpha 1.3)

**Sistema Intelligente per l'Archiviazione e l'Interrogazione di Documenti Scientifici**

Archivista AI è un'applicazione web avanzata che utilizza l'intelligenza artificiale per processare, indicizzare e rendere interrogabili documenti scientifici in formato PDF e DOCX. Il sistema è basato su LlamaIndex e offre un'interfaccia utente moderna costruita con Streamlit.

## ✨ Caratteristiche Principali

- 🔍 **Ricerca Intelligente**: Interrogazione semantica dei documenti con supporto per filtri avanzati
- 🤖 **Elaborazione AI**: Estrazione automatica di metadati, riassunti e anteprime
- 📁 **Gestione Documenti**: Organizzazione automatica e categorizzazione dei file
- 🔄 **Elaborazione Asincrona**: Processamento in background con Celery e Redis
- 🐳 **Containerizzazione**: Deployment semplificato con Docker
- 📊 **Dashboard Interattiva**: Interfaccia web moderna e responsiva
- 🔐 **Persistenza Dati**: Database SQLite con backup automatico

## 🚀 Avvio Rapido

### Con Docker (Raccomandato)

```bash
# 1. Clona il repository
git clone <repository-url>
cd archivista-ai

# 2. Avvia tutti i servizi
docker-compose up -d

# 3. Accedi all'applicazione
# UI: http://localhost:8501
# Monitor: http://localhost:5555
```

### Installazione Manuale

```bash
# 1. Installa Redis
start_redis.bat  # Windows

# 2. Installa dipendenze Python
pip install -r requirements.txt

# 3. Avvia il worker Celery
start_celery_worker.bat

# 4. Avvia l'applicazione
streamlit run main.py
```

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
├── 📄 archivista_tasks.py     # Task specifiche per l'archiviazione
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

- **[Guida Celery](CELERY_README.md)**: Configurazione task queue e Redis
- **[Guida Docker](DOCKER_README.md)**: Deployment containerizzato
- **[API Reference](docs/api.md)**: Documentazione API (se disponibile)

## 🔄 Changelog

### Versione 1.3.0 (Alpha 1.3) - 2025-01-XX

**🆕 Nuove Funzionalità:**
- ✅ Architettura Celery completa per elaborazione asincrona
- ✅ Containerizzazione Docker completa
- ✅ Dashboard di monitoraggio Flower
- ✅ Sistema di status in tempo reale
- ✅ Supporto per modelli LLM multipli

**🔧 Miglioramenti:**
- ✅ Ottimizzazione performance processamento
- ✅ Migliore gestione errori e recovery
- ✅ Interfaccia utente migliorata
- ✅ Documentazione completa

**🐛 Bug Fixes:**
- ✅ Risoluzione problemi di memoria
- ✅ Fix gestione file di grandi dimensioni
- ✅ Miglioramento stabilità worker

### Versioni Precedenti

- **v1.2.2**: Miglioramenti UI e ottimizzazioni
- **v1.0.2**: Release iniziale con funzionalità base

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
