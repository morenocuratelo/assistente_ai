#!/bin/bash

# 🚀 Script di Deployment Production - Archivista AI v3.0
# Automatizza il deployment del sistema ottimizzato per documenti pesanti

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzioni utility
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# === PREREQUISITI ===

check_prerequisites() {
    log_info "Verifica prerequisiti..."

    # Verifica Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker non installato. Installa Docker prima di continuare."
        exit 1
    fi

    # Verifica Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose non disponibile. Installa Docker Compose."
        exit 1
    fi

    # Verifica spazio disco (minimo 5GB)
    FREE_SPACE=$(df . | awk 'NR==2 {print $4}' | sed 's/.$//')
    if [ "$FREE_SPACE" -lt 5242880 ]; then  # 5GB in KB
        log_error "Spazio insufficiente. Richiesti almeno 5GB."
        exit 1
    fi

    log_success "Prerequisiti verificati"
}

# === PREPARAZIONE AMBIENTE ===

prepare_environment() {
    log_info "Preparazione ambiente di produzione..."

    # Crea directory necessarie
    mkdir -p data/redis logs backups config

    # Crea file di configurazione Redis ottimizzato
    cat > redis.conf << EOF
# Redis Production Configuration
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 300
daemonize no
supervised no
loglevel notice
logfile "/data/redis.log"
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data
replica-serve-stale-data yes
replica-read-only no
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
replica-priority 100
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
aof-rewrite-incremental-fsync yes
EOF

    # Crea configurazione Celery ottimizzata
    cat > config/celery_config.py << EOF
# Celery Production Configuration
import os

# Broker settings
broker_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
result_backend = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 50

# Task settings
task_soft_time_limit = 600  # 10 minuti
task_time_limit = 900       # 15 minuti
task_ignore_result = False
task_store_eager_result = True

# Queue settings
task_default_queue = 'archivista'
task_default_exchange = 'archivista'
task_default_exchange_type = 'direct'
task_default_routing_key = 'archivista'

# Security
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
result_accept_content = ['json']

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
EOF

    # Crea configurazione monitoring
    cat > config/monitoring_config.json << EOF
{
  "enable_email_alerts": false,
  "error_rate_threshold": 10.0,
  "critical_error_threshold": 5,
  "quarantine_threshold": 10,
  "processing_stuck_threshold": 300,
  "metrics_collection_interval": 60,
  "health_check_interval": 30,
  "log_retention_days": 30,
  "metrics_retention_days": 90
}
EOF

    log_success "Ambiente preparato"
}

# === BUILD E DEPLOY ===

build_and_deploy() {
    log_info "Build e deployment servizi..."

    # Crea network se non esiste
    docker network create archivista-network 2>/dev/null || true

    # Build immagini
    log_info "Building immagini Docker..."
    docker-compose -f docker-compose.prod.yml build --parallel

    # Deploy servizi
    log_info "Avvio servizi in produzione..."
    docker-compose -f docker-compose.prod.yml up -d

    log_success "Servizi avviati"
}

# === VERIFICA DEPLOYMENT ===

verify_deployment() {
    log_info "Verifica deployment..."

    # Attendi avvio servizi
    log_info "Attesa avvio servizi..."
    sleep 30

    # Verifica Redis
    if docker-compose -f docker-compose.prod.yml exec redis redis-cli ping | grep -q PONG; then
        log_success "Redis: OK"
    else
        log_error "Redis: FALLITO"
        exit 1
    fi

    # Verifica Webapp
    if curl -f http://localhost:8501/_stcore/health &>/dev/null; then
        log_success "Webapp: OK (http://localhost:8501)"
    else
        log_warning "Webapp: Non ancora pronta, riprova tra poco"
    fi

    # Verifica Worker
    if docker-compose -f docker-compose.prod.yml ps worker | grep -q "Up"; then
        log_success "Worker: OK"
    else
        log_error "Worker: FALLITO"
        exit 1
    fi

    # Verifica Flower
    if curl -f http://localhost:5555 &>/dev/null; then
        log_success "Flower: OK (http://localhost:5555)"
    else
        log_warning "Flower: Non ancora pronta"
    fi

    log_success "Deployment verificato"
}

# === POST-DEPLOYMENT ===

post_deployment_setup() {
    log_info "Configurazione post-deployment..."

    # Crea primo backup
    log_info "Creazione backup iniziale..."
    docker-compose -f docker-compose.prod.yml exec backup sh -c "tar czf /archive/initial-backup-\$(date +%Y%m%d-%H%M%S).tar.gz -C /backup ."

    # Verifica spazio utilizzato
    DISK_USAGE=$(du -sh . | cut -f1)
    log_info "Spazio utilizzato: $DISK_USAGE"

    log_success "Setup completato"
}

# === MONITORAGGIO ===

show_monitoring_info() {
    log_info "Informazioni di monitoraggio:"
    echo
    echo "🌐 Interfacce disponibili:"
    echo "   • Dashboard principale: http://localhost:8501"
    echo "   • Monitoraggio Celery:   http://localhost:5555"
    echo "   • Documentazione API:    http://localhost:8501 (docs tab)"
    echo
    echo "📊 Servizi attivi:"
    docker-compose -f docker-compose.prod.yml ps
    echo
    echo "📋 Log servizi:"
    echo "   • docker-compose -f docker-compose.prod.yml logs -f"
    echo "   • docker-compose -f docker-compose.prod.yml logs -f worker"
    echo
    echo "🔧 Comandi utili:"
    echo "   • Arresto: docker-compose -f docker-compose.prod.yml down"
    echo "   • Riavvio: docker-compose -f docker-compose.prod.yml restart"
    echo "   • Backup:  docker-compose -f docker-compose.prod.yml exec backup sh -c 'tar czf /archive/backup-manual.tar.gz -C /backup .'"
}

# === MAIN SCRIPT ===

main() {
    echo "🚀 Deployment Production - Archivista AI v3.0"
    echo "=============================================="
    echo

    # Verifica prerequisiti
    check_prerequisites

    # Preparazione ambiente
    prepare_environment

    # Build e deploy
    build_and_deploy

    # Verifica
    verify_deployment

    # Setup post-deployment
    post_deployment_setup

    # Mostra informazioni
    echo
    echo "🎉 DEPLOYMENT COMPLETATO!"
    echo "=========================="
    show_monitoring_info

    log_success "Archivista AI è ora in esecuzione in modalità produzione!"
    log_info "Ottimizzato per processamento documenti pesanti (single-user)"
}

# Gestione segnali
trap 'log_info "Deployment interrotto"; exit 1' INT TERM

# Esegui deployment
main "$@"
