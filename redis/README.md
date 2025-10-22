# 🔴 Redis - Server e Strumenti Cache

Questa cartella contiene tutti i file relativi a Redis, il sistema di cache e message broker utilizzato dal progetto Archivista AI.

## 📂 Struttura Organizzata

### ⚙️ **bin/** - Eseguibili e Binari
**File eseguibili Redis:**
- `redis-server.exe` - Server Redis principale
- `redis-cli.exe` - Client command line per Redis
- `redis-benchmark.exe` - Strumento per benchmark performance
- `redis-check-aof.exe` - Strumento per verificare file AOF
- `redis-check-dump.exe` - Strumento per verificare dump RDB

**File di debug:**
- `redis-*.pdb` - Debug symbols per troubleshooting

### ⚙️ **config/** - Configurazioni
**File di configurazione:**
- `redis.windows.conf` - Configurazione principale per Windows
- `redis.windows-service.conf` - Configurazione per esecuzione come servizio Windows

## 🚀 **Utilizzo**

### Avvio Redis
```bash
# Dalla cartella principale del progetto
start_redis.bat

# Oppure direttamente
redis\bin\redis-server.exe redis\config\redis.windows.conf
```

### Accesso Redis CLI
```bash
# Client command line
redis\bin\redis-cli.exe

# Connessione specifica
redis\bin\redis-cli.exe -h 127.0.0.1 -p 6379
```

### Verifica Stato
```bash
# Controlla processi Redis
redis\bin\redis-cli.exe ping

# Verifica configurazione
redis\bin\redis-cli.exe info server
```

## 🔧 **Configurazione**

### Configurazione Windows
- **Porta**: 6379 (default)
- **Bind**: 127.0.0.1 (localhost)
- **Max Memory**: Configurato per utilizzo ottimale
- **Persistence**: AOF e RDB abilitati

### Ottimizzazioni
- **Memory policy**: allkeys-lru per gestione memoria
- **TCP keepalive**: Abilitato per connessioni stabili
- **Log level**: Notice per produzione

## 📊 **Monitoraggio**

### Metriche Importanti
```bash
# Info generali
redis\bin\redis-cli.exe info

# Memoria utilizzata
redis\bin\redis-cli.exe info memory

# Statistiche chiavi
redis\bin\redis-cli.exe dbsize
```

### Troubleshooting
```bash
# Verifica connessioni
redis\bin\redis-cli.exe info clients

# Controlla replicazione (se utilizzata)
redis\bin\redis-cli.exe info replication
```

## 🔒 **Sicurezza**

- ✅ **Bind locale** - Redis accessibile solo da localhost
- ✅ **Protected mode** - Abilitato per sicurezza
- ✅ **Password** - Configurabile tramite requirepass
- ✅ **Network isolation** - Non esposto su rete pubblica

## 📋 **Manutenzione**

### Backup
```bash
# Salva stato corrente
redis\bin\redis-cli.exe save

# Backup configurazione
copy redis\config\redis.windows.conf redis\config\redis.windows.conf.backup
```

### Aggiornamenti
1. Scaricare nuova versione Redis
2. Sostituire eseguibili in `bin/`
3. Testare funzionalità
4. Aggiornare configurazione se necessario

## 🚨 **Troubleshooting**

### Problemi Comuni

**Redis non si avvia:**
```bash
# Controlla log
redis\bin\redis-server.exe redis\config\redis.windows.conf --loglevel verbose

# Verifica porte libere
netstat -ano | findstr :6379
```

**Performance lente:**
```bash
# Controlla memoria
redis\bin\redis-cli.exe info memory

# Verifica fragmentazione
redis\bin\redis-cli.exe info memory | findstr mem_fragmentation
```

**Connessioni rifiutate:**
```bash
# Verifica se Redis è in esecuzione
redis\bin\redis-cli.exe ping

# Controlla configurazione bind
type redis\config\redis.windows.conf | findstr bind
```

## 📞 **Supporto**

Per problemi Redis:
1. Controllare i log del server
2. Verificare configurazione
3. Testare connettività
4. Consultare documentazione ufficiale Redis

**Redis** - Cache e message broker ad alte prestazioni per Archivista AI! ⚡
