# 📁 Scripts - Script Operativi e Utility

Questa cartella contiene tutti gli script operativi, di deployment e utility del progetto Archivista AI.

## 📂 Struttura Organizzata

### 🚀 **operations/** - Script di Processamento
Script per le operazioni principali del sistema:
- `archivista_processing.py` - Elaborazione documenti principale
- `batch_operations.py` - Operazioni in batch
- `export_manager.py` - Gestione esportazioni

### ⚙️ **deployment/** - Script di Deployment
Script per il deployment e configurazione del sistema:
- `deploy.sh` - Script deployment principale
- `deployment_automation.py` - Automazione deployment
- `database_migration.py` - Migrazioni database
- `monitoring_setup.py` - Configurazione monitoring

### 🔧 **utilities/** - Utility Varie
Script di utilità e supporto:
- `file_utils.py` - Utilità per gestione file
- `puliscitutti.py` - Script di pulizia

## 🎯 **Utilizzo**

### Per Operazioni
```bash
# Elaborazione documenti
python scripts/operations/archivista_processing.py

# Operazioni batch
python scripts/operations/batch_operations.py

# Esportazioni
python scripts/operations/export_manager.py
```

### Per Deployment
```bash
# Deployment automatico
chmod +x scripts/deployment/deploy.sh
./scripts/deployment/deploy.sh

# Migrazioni database
python scripts/deployment/database_migration.py

# Setup monitoring
python scripts/deployment/monitoring_setup.py
```

### Per Utility
```bash
# Pulizia file
python scripts/utilities/puliscitutti.py

# Utilità file
python scripts/utilities/file_utils.py
```

## 📋 **Manutenzione**

- ✅ **Script documentati** con commenti e docstring
- ✅ **Error handling** implementato
- ✅ **Logging strutturato** utilizzato
- ✅ **Configurazioni esterne** per parametrizzazione

## 🔒 **Best Practices**

- Utilizzare sempre percorsi assoluti o relativi corretti
- Verificare dipendenze prima dell'esecuzione
- Controllare log per diagnosticare problemi
- Testare script in ambiente di sviluppo prima della produzione
