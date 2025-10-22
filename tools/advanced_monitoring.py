"""
Sistema di Monitoraggio Avanzato e Alerting
Implementa logging strutturato, metriche real-time e notifiche intelligenti.
"""
import os
import json
import time
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sqlite3
import psutil
import threading

from error_diagnosis_framework import (
    error_framework,
    ProcessingState,
    ErrorCategory,
    ErrorSeverity
)

# --- CONFIGURAZIONE ---

@dataclass
class MonitoringConfig:
    """Configurazione per il sistema di monitoraggio"""
    # Alerting
    enable_email_alerts: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    alert_recipients: List[str] = None

    # Thresholds
    error_rate_threshold: float = 10.0  # 10% error rate
    critical_error_threshold: int = 5   # 5 errori critici
    quarantine_threshold: int = 10      # 10 file in quarantena
    processing_stuck_threshold: int = 300  # 5 minuti

    # Collection intervals (secondi)
    metrics_collection_interval: int = 60
    health_check_interval: int = 30
    log_rotation_interval: int = 3600  # 1 ora

    # Retention
    log_retention_days: int = 30
    metrics_retention_days: int = 90

    def __post_init__(self):
        if self.alert_recipients is None:
            self.alert_recipients = []

# --- SISTEMA LOGGING STRUTTURATO ---

class StructuredLogger:
    """Logger avanzato con dati strutturati e correlazione"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.base_logger = logging.getLogger("ArchivistaAI.Advanced")
        self.base_logger.setLevel(logging.DEBUG)

        # Crea directory log se non esiste
        log_dir = os.path.join("db_memoria", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Formatter strutturato per JSON
        self.json_formatter = logging.Formatter(
            '%(asctime)s|%(name)s|%(levelname)s|%(correlation_id)s|%(message)s'
        )

        # File handler per tutti i log
        self.file_handler = logging.FileHandler(
            os.path.join(log_dir, "archivista_advanced.log")
        )
        self.file_handler.setFormatter(self.json_formatter)

        # Handler specifico per errori critici
        self.error_handler = logging.FileHandler(
            os.path.join(log_dir, "critical_errors.log")
        )
        self.error_handler.setLevel(logging.ERROR)
        self.error_handler.setFormatter(self.json_formatter)

        self.base_logger.addHandler(self.file_handler)
        self.base_logger.addHandler(self.error_handler)

    def log_with_context(self, level: str, message: str,
                        correlation_id: str = None, **context):
        """Log con contesto strutturato"""
        if correlation_id is None:
            correlation_id = error_framework.generate_correlation_id()

        # Crea log entry strutturato
        log_entry = {
            'message': message,
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            **context
        }

        # Log nel formato strutturato
        formatted_message = f"{message} | Context: {json.dumps(context)}"

        if level.upper() == 'CRITICAL':
            self.base_logger.critical(formatted_message, extra={'correlation_id': correlation_id})
        elif level.upper() == 'ERROR':
            self.base_logger.error(formatted_message, extra={'correlation_id': correlation_id})
        elif level.upper() == 'WARNING':
            self.base_logger.warning(formatted_message, extra={'correlation_id': correlation_id})
        elif level.upper() == 'INFO':
            self.base_logger.info(formatted_message, extra={'correlation_id': correlation_id})
        else:
            self.base_logger.debug(formatted_message, extra={'correlation_id': correlation_id})

        return correlation_id

# --- SISTEMA METRICHE ---

class MetricsCollector:
    """Collettore avanzato di metriche di sistema"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.collection_thread = None
        self.running = False

        # Metriche correnti
        self.current_metrics = {
            'system': {},
            'processing': {},
            'errors': {},
            'performance': {}
        }

    def start_collection(self):
        """Avvia la collezione automatica delle metriche"""
        if self.running:
            return

        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()

    def stop_collection(self):
        """Ferma la collezione delle metriche"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)

    def _collection_loop(self):
        """Loop principale di collezione metriche"""
        while self.running:
            try:
                self.collect_all_metrics()
                time.sleep(self.config.metrics_collection_interval)
            except Exception as e:
                print(f"❌ Errore nella collezione metriche: {e}")
                time.sleep(10)  # Attendi prima di riprovare

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Colleziona tutte le metriche disponibili"""
        timestamp = datetime.now()

        # Metriche di sistema
        self.current_metrics['system'] = self._collect_system_metrics()

        # Metriche di processamento
        self.current_metrics['processing'] = self._collect_processing_metrics()

        # Metriche errori
        self.current_metrics['errors'] = self._collect_error_metrics()

        # Metriche performance
        self.current_metrics['performance'] = self._collect_performance_metrics()

        # Salva metriche nel database
        self._save_metrics_to_db(timestamp)

        return self.current_metrics.copy()

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Colleziona metriche di sistema"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'network_io': dict(psutil.net_io_counters()._asdict()),
                'process_count': len(psutil.pids()),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
        except Exception as e:
            return {'error': str(e)}

    def _collect_processing_metrics(self) -> Dict[str, Any]:
        """Colleziona metriche di processamento"""
        try:
            summary = error_framework.get_processing_status_summary()

            return {
                'total_files': summary.get('total_files', 0),
                'pending_files': summary['state_counts'].get('PENDING', 0),
                'processing_files': summary['state_counts'].get('PROCESSING', 0),
                'completed_files': summary['state_counts'].get('COMPLETED', 0),
                'failed_files': summary.get('failed_files', 0),
                'quarantine_count': len(error_framework.get_quarantined_files())
            }
        except Exception as e:
            return {'error': str(e)}

    def _collect_error_metrics(self) -> Dict[str, Any]:
        """Colleziona metriche errori"""
        try:
            error_data = error_framework.get_error_dashboard_data()

            return {
                'total_open_errors': error_data.get('total_open_errors', 0),
                'errors_by_category': error_data.get('errors_by_category', []),
                'errors_by_severity': error_data.get('errors_by_severity', []),
                'recent_error_count': len(error_framework.get_processing_status_summary().get('recent_errors', []))
            }
        except Exception as e:
            return {'error': str(e)}

    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Colleziona metriche performance"""
        try:
            # Calcola throughput
            recent_metrics = error_framework.get_processing_metrics(1)
            if recent_metrics:
                latest = recent_metrics[0]
                return {
                    'throughput_per_hour': latest.total_files * 3600 / max(1, (datetime.now() - latest.created_at.replace(tzinfo=None)).seconds),
                    'avg_processing_time': latest.avg_processing_time,
                    'error_rate': latest.error_rate,
                    'success_rate': 100 - latest.error_rate
                }
            else:
                return {'throughput_per_hour': 0, 'error_rate': 0, 'success_rate': 100}
        except Exception as e:
            return {'error': str(e)}

    def _save_metrics_to_db(self, timestamp: datetime):
        """Salva metriche nel database"""
        try:
            with error_framework.db_connect() as conn:
                cursor = conn.cursor()

                # Crea tabella metriche avanzate se non esiste
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS advanced_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL,
                        metric_data TEXT, -- JSON dettagliato
                        created_at TEXT NOT NULL
                    )
                """)

                # Salva ogni categoria di metriche
                for category, metrics in self.current_metrics.items():
                    for metric_name, metric_value in metrics.items():
                        if metric_name != 'error':  # Skip error fields
                            cursor.execute("""
                                INSERT INTO advanced_metrics
                                (timestamp, metric_type, metric_name, metric_value, metric_data, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                timestamp.isoformat(),
                                category,
                                metric_name,
                                metric_value if isinstance(metric_value, (int, float)) else 0,
                                json.dumps(metrics),
                                timestamp.isoformat()
                            ))

                conn.commit()

        except Exception as e:
            print(f"❌ Errore salvataggio metriche: {e}")

    def get_metrics_history(self, hours: int = 24) -> Dict[str, List]:
        """Recupera storico metriche"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with error_framework.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM advanced_metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time.isoformat(),))

                metrics = cursor.fetchall()

                # Organizza per tipo
                history = {}
                for metric in metrics:
                    metric_type = metric['metric_type']
                    if metric_type not in history:
                        history[metric_type] = []

                    history[metric_type].append({
                        'timestamp': metric['timestamp'],
                        'name': metric['metric_name'],
                        'value': metric['metric_value'],
                        'data': json.loads(metric['metric_data']) if metric['metric_data'] else {}
                    })

                return history

        except Exception as e:
            print(f"❌ Errore recupero storico metriche: {e}")
            return {}

# --- SISTEMA ALERTING ---

class AlertManager:
    """Gestore avanzato di alerting e notifiche"""

    def __init__(self, config: MonitoringConfig, logger: StructuredLogger):
        self.config = config
        self.logger = logger
        self.alert_history = []
        self.last_alert_times = {}

    def check_and_send_alerts(self, metrics: Dict[str, Any]):
        """Verifica condizioni e invia alert se necessario"""
        alerts_sent = []

        # Alert tasso errori elevato
        if self._check_error_rate_alert(metrics):
            alert = self._send_error_rate_alert(metrics)
            if alert:
                alerts_sent.append(alert)

        # Alert errori critici
        if self._check_critical_errors_alert(metrics):
            alert = self._send_critical_errors_alert(metrics)
            if alert:
                alerts_sent.append(alert)

        # Alert quarantena piena
        if self._check_quarantine_alert(metrics):
            alert = self._send_quarantine_alert(metrics)
            if alert:
                alerts_sent.append(alert)

        # Alert processamento bloccato
        if self._check_stuck_processing_alert(metrics):
            alert = self._send_stuck_processing_alert(metrics)
            if alert:
                alerts_sent.append(alert)

        return alerts_sent

    def _check_error_rate_alert(self, metrics: Dict[str, Any]) -> bool:
        """Verifica se il tasso di errore supera la soglia"""
        processing_metrics = metrics.get('processing', {})
        error_rate = processing_metrics.get('error_rate', 0)

        return error_rate > self.config.error_rate_threshold

    def _check_critical_errors_alert(self, metrics: Dict[str, Any]) -> bool:
        """Verifica se ci sono troppi errori critici"""
        error_metrics = metrics.get('errors', {})
        critical_errors = sum(
            error['count'] for error in error_metrics.get('errors_by_severity', [])
            if error.get('error_type') == 'critical'
        )

        return critical_errors >= self.config.critical_error_threshold

    def _check_quarantine_alert(self, metrics: Dict[str, Any]) -> bool:
        """Verifica se la quarantena è troppo piena"""
        processing_metrics = metrics.get('processing', {})
        quarantine_count = processing_metrics.get('quarantine_count', 0)

        return quarantine_count >= self.config.quarantine_threshold

    def _check_stuck_processing_alert(self, metrics: Dict[str, Any]) -> bool:
        """Verifica se ci sono processi bloccati"""
        # Implementa logica per rilevare processi stuck
        # Per ora, verifica se ci sono file PROCESSING da troppo tempo
        try:
            with error_framework.db_connect() as conn:
                cursor = conn.cursor()
                cutoff_time = datetime.now() - timedelta(seconds=self.config.processing_stuck_threshold)

                cursor.execute("""
                    SELECT COUNT(*) as stuck_count FROM document_processing_status
                    WHERE processing_state = 'PROCESSING' AND updated_at < ?
                """, (cutoff_time.isoformat(),))

                result = cursor.fetchone()
                return result['stuck_count'] > 0

        except Exception as e:
            print(f"❌ Errore verifica processi bloccati: {e}")
            return False

    def _send_error_rate_alert(self, metrics: Dict[str, Any]) -> Optional[Dict]:
        """Invia alert per tasso errori elevato"""
        return self._send_alert(
            "HIGH_ERROR_RATE",
            f"⚠️ Tasso errori elevato: {metrics['processing'].get('error_rate', 0):.1f}%",
            {
                'error_rate': metrics['processing'].get('error_rate', 0),
                'failed_files': metrics['processing'].get('failed_files', 0),
                'total_files': metrics['processing'].get('total_files', 0)
            }
        )

    def _send_critical_errors_alert(self, metrics: Dict[str, Any]) -> Optional[Dict]:
        """Invia alert per errori critici"""
        return self._send_alert(
            "CRITICAL_ERRORS",
            f"🚨 {self._get_critical_error_count(metrics)} errori critici rilevati",
            {
                'critical_errors': self._get_critical_error_count(metrics),
                'error_details': metrics['errors'].get('errors_by_severity', [])
            }
        )

    def _send_quarantine_alert(self, metrics: Dict[str, Any]) -> Optional[Dict]:
        """Invia alert per quarantena piena"""
        return self._send_alert(
            "QUARANTINE_FULL",
            f"🚫 Quarantena contiene {metrics['processing'].get('quarantine_count', 0)} file",
            {
                'quarantine_count': metrics['processing'].get('quarantine_count', 0),
                'quarantine_files': error_framework.get_quarantined_files(limit=5)
            }
        )

    def _send_stuck_processing_alert(self, metrics: Dict[str, Any]) -> Optional[Dict]:
        """Invia alert per processi bloccati"""
        return self._send_alert(
            "STUCK_PROCESSING",
            "🔄 Rilevati processi di processamento bloccati",
            {
                'stuck_threshold_seconds': self.config.processing_stuck_threshold,
                'detection_time': datetime.now().isoformat()
            }
        )

    def _send_alert(self, alert_type: str, message: str, context: Dict[str, Any]) -> Optional[Dict]:
        """Invia alert generico"""
        # Evita spam: max 1 alert ogni 5 minuti per tipo
        current_time = time.time()
        last_alert = self.last_alert_times.get(alert_type, 0)

        if current_time - last_alert < 300:  # 5 minuti
            return None

        self.last_alert_times[alert_type] = current_time

        # Log dell'alert
        correlation_id = self.logger.log_with_context(
            'WARNING',
            f"ALERT: {message}",
            alert_type=alert_type,
            **context
        )

        # Invia email se configurato
        if self.config.enable_email_alerts and self.config.alert_recipients:
            email_sent = self._send_email_alert(alert_type, message, context)
        else:
            email_sent = False

        alert_record = {
            'type': alert_type,
            'message': message,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'correlation_id': correlation_id,
            'email_sent': email_sent
        }

        self.alert_history.append(alert_record)
        return alert_record

    def _send_email_alert(self, alert_type: str, message: str, context: Dict[str, Any]) -> bool:
        """Invia alert via email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = ', '.join(self.config.alert_recipients)
            msg['Subject'] = f"Archivista AI - Alert: {alert_type}"

            # Corpo email
            body = f"""
Archivista AI - Alert di Sistema

Tipo: {alert_type}
Messaggio: {message}
Timestamp: {datetime.now().isoformat()}

Dettagli:
{json.dumps(context, indent=2)}

Dashboard: [Link alla dashboard di monitoraggio]
"""
            msg.attach(MimeText(body, 'plain'))

            # Invia email
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"❌ Errore invio email alert: {e}")
            return False

    def _get_critical_error_count(self, metrics: Dict[str, Any]) -> int:
        """Conta errori critici dalle metriche"""
        error_metrics = metrics.get('errors', {})
        return sum(
            error['count'] for error in error_metrics.get('errors_by_severity', [])
            if error.get('error_type') == 'critical'
        )

    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Recupera storico alert"""
        return self.alert_history[-limit:] if self.alert_history else []

# --- SISTEMA HEALTH CHECK ---

class HealthChecker:
    """Sistema di controllo salute componenti"""

    def __init__(self, config: MonitoringConfig, logger: StructuredLogger):
        self.config = config
        self.logger = logger
        self.health_status = {}

    def perform_health_check(self) -> Dict[str, Any]:
        """Esegue controllo completo salute sistema"""
        checks = {
            'database': self._check_database,
            'ai_services': self._check_ai_services,
            'file_system': self._check_file_system,
            'celery_worker': self._check_celery_worker,
            'disk_space': self._check_disk_space,
            'memory_usage': self._check_memory_usage
        }

        results = {}
        overall_status = 'healthy'

        for check_name, check_func in checks.items():
            try:
                result = check_func()
                results[check_name] = result

                if result['status'] != 'healthy':
                    overall_status = 'degraded' if overall_status == 'healthy' else 'unhealthy'

            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                overall_status = 'unhealthy'

        # Salva stato salute
        self.health_status = {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }

        return self.health_status

    def _check_database(self) -> Dict[str, Any]:
        """Verifica salute database"""
        try:
            with error_framework.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM papers")
                count = cursor.fetchone()[0]

                return {
                    'status': 'healthy',
                    'message': f'Database OK, {count} documenti',
                    'document_count': count,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Errore database: {e}',
                'timestamp': datetime.now().isoformat()
            }

    def _check_ai_services(self) -> Dict[str, Any]:
        """Verifica servizi AI"""
        try:
            from config import initialize_services
            initialize_services()

            # Verifica modelli caricati
            from llama_index.core import Settings
            llm_status = 'OK' if Settings.llm else 'Non disponibile'
            embed_status = 'OK' if Settings.embed_model else 'Non disponibile'

            status = 'healthy' if Settings.llm and Settings.embed_model else 'degraded'

            return {
                'status': status,
                'message': f'LLM: {llm_status}, Embeddings: {embed_status}',
                'llm_available': Settings.llm is not None,
                'embeddings_available': Settings.embed_model is not None,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Errore servizi AI: {e}',
                'timestamp': datetime.now().isoformat()
            }

    def _check_file_system(self) -> Dict[str, Any]:
        """Verifica file system"""
        try:
            # Verifica directory principali
            dirs_to_check = [
                "documenti_da_processare",
                "Dall_Origine_alla_Complessita",
                "db_memoria"
            ]

            missing_dirs = []
            for dir_path in dirs_to_check:
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_path)

            if missing_dirs:
                return {
                    'status': 'degraded',
                    'message': f'Directory mancanti: {", ".join(missing_dirs)}',
                    'missing_directories': missing_dirs,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'Tutte le directory presenti',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Errore verifica file system: {e}',
                'timestamp': datetime.now().isoformat()
            }

    def _check_celery_worker(self) -> Dict[str, Any]:
        """Verifica worker Celery"""
        # Implementazione base - in produzione usa celery inspect
        return {
            'status': 'unknown',
            'message': 'Stato worker non verificabile automaticamente',
            'timestamp': datetime.now().isoformat()
        }

    def _check_disk_space(self) -> Dict[str, Any]:
        """Verifica spazio disco"""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = disk_usage.percent

            if usage_percent > 90:
                status = 'unhealthy'
                message = f'Spazio disco critico: {usage_percent:.1f}%'
            elif usage_percent > 80:
                status = 'degraded'
                message = f'Spazio disco elevato: {usage_percent:.1f}%'
            else:
                status = 'healthy'
                message = f'Spazio disco OK: {usage_percent:.1f}%'

            return {
                'status': status,
                'message': message,
                'disk_usage_percent': usage_percent,
                'free_space_gb': disk_usage.free / (1024**3),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Errore verifica disco: {e}',
                'timestamp': datetime.now().isoformat()
            }

    def _check_memory_usage(self) -> Dict[str, Any]:
        """Verifica utilizzo memoria"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            if usage_percent > 95:
                status = 'unhealthy'
                message = f'Memoria critica: {usage_percent:.1f}%'
            elif usage_percent > 85:
                status = 'degraded'
                message = f'Memoria elevata: {usage_percent:.1f}%'
            else:
                status = 'healthy'
                message = f'Memoria OK: {usage_percent:.1f}%'

            return {
                'status': status,
                'message': message,
                'memory_usage_percent': usage_percent,
                'available_memory_gb': memory.available / (1024**3),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Errore verifica memoria: {e}',
                'timestamp': datetime.now().isoformat()
            }

# --- SISTEMA PRINCIPALE MONITORAGGIO ---

class AdvancedMonitoringSystem:
    """Sistema principale di monitoraggio avanzato"""

    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.logger = StructuredLogger(self.config)
        self.metrics_collector = MetricsCollector(self.config)
        self.alert_manager = AlertManager(self.config, self.logger)
        self.health_checker = HealthChecker(self.config, self.logger)

        # Thread per controlli automatici
        self.monitoring_thread = None
        self.running = False

    def start_monitoring(self):
        """Avvia il sistema di monitoraggio completo"""
        if self.running:
            return

        self.running = True

        # Avvia collezione metriche
        self.metrics_collector.start_collection()

        # Avvia thread principale monitoraggio
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        self.logger.log_with_context('INFO', 'Sistema di monitoraggio avanzato avviato')

    def stop_monitoring(self):
        """Ferma il sistema di monitoraggio"""
        self.running = False
        self.metrics_collector.stop_collection()

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        self.logger.log_with_context('INFO', 'Sistema di monitoraggio avanzato fermato')

    def _monitoring_loop(self):
        """Loop principale di monitoraggio"""
        while self.running:
            try:
                # Colleziona metriche
                metrics = self.metrics_collector.collect_all_metrics()

                # Esegui controlli salute
                health_status = self.health_checker.perform_health_check()

                # Verifica e invia alert
                alerts = self.alert_manager.check_and_send_alerts(metrics)

                # Log riepilogo ogni ora
                if datetime.now().minute == 0:
                    self._log_hourly_summary(metrics, health_status, alerts)

                time.sleep(self.config.health_check_interval)

            except Exception as e:
                self.logger.log_with_context('ERROR', f'Errore nel loop di monitoraggio: {e}')
                time.sleep(10)

    def _log_hourly_summary(self, metrics: Dict, health: Dict, alerts: List):
        """Log riepilogo orario"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'health_status': health.get('overall_status', 'unknown'),
            'total_files': metrics.get('processing', {}).get('total_files', 0),
            'error_rate': metrics.get('processing', {}).get('error_rate', 0),
            'alerts_sent': len(alerts),
            'system_cpu': metrics.get('system', {}).get('cpu_percent', 0),
            'system_memory': metrics.get('system', {}).get('memory_percent', 0)
        }

        self.logger.log_with_context(
            'INFO',
            'Riepilogo orario sistema',
            **summary
        )

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Restituisce stato completo del sistema"""
        try:
            # Colleziona metriche fresche
            metrics = self.metrics_collector.collect_all_metrics()

            # Esegui health check
            health = self.health_checker.perform_health_check()

            # Recupera alert recenti
            recent_alerts = self.alert_manager.get_alert_history(10)

            return {
                'timestamp': datetime.now().isoformat(),
                'health': health,
                'metrics': metrics,
                'recent_alerts': recent_alerts,
                'monitoring_status': 'running' if self.running else 'stopped'
            }

        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'monitoring_status': 'error'
            }

# --- ISTANZA GLOBALE ---
monitoring_system = AdvancedMonitoringSystem()

# --- FUNZIONI DI UTILITÀ PUBBLICHE ---

def start_advanced_monitoring(config: MonitoringConfig = None):
    """Avvia il sistema di monitoraggio avanzato"""
    global monitoring_system

    if config:
        monitoring_system = AdvancedMonitoringSystem(config)

    monitoring_system.start_monitoring()
    return monitoring_system

def stop_advanced_monitoring():
    """Ferma il sistema di monitoraggio avanzato"""
    monitoring_system.stop_monitoring()

def get_system_status():
    """Recupera stato attuale del sistema"""
    return monitoring_system.get_comprehensive_status()

def get_metrics_dashboard_data():
    """Recupera dati per dashboard metriche avanzate"""
    try:
        status = get_system_status()

        # Organizza dati per dashboard
        dashboard_data = {
            'health_status': status.get('health', {}).get('overall_status', 'unknown'),
            'current_metrics': status.get('metrics', {}),
            'health_checks': status.get('health', {}).get('checks', {}),
            'recent_alerts': status.get('recent_alerts', []),
            'monitoring_active': status.get('monitoring_status') == 'running'
        }

        return dashboard_data

    except Exception as e:
        return {
            'error': str(e),
            'health_status': 'error',
            'monitoring_active': False
        }

# --- INTEGRAZIONE CON DASHBOARD ESISTENTE ---

def enhance_dashboard_with_advanced_monitoring():
    """Migliora la dashboard esistente con funzionalità avanzate"""
    st.header("🔬 Monitoraggio Avanzato")

    # Status sistema
    status = get_system_status()

    if 'error' in status:
        st.error(f"❌ Errore sistema monitoraggio: {status['error']}")
        return

    # Health overview
    health = status.get('health', {})
    overall_status = health.get('overall_status', 'unknown')

    col1, col2, col3 = st.columns(3)

    with col1:
        status_color = {'healthy': '🟢', 'degraded': '🟡', 'unhealthy': '🔴'}.get(overall_status, '⚪')
        st.metric("💚 Stato Sistema", f"{status_color} {overall_status.title()}")

    with col2:
        st.metric("📊 Metriche Attive", "✅ Rilevamento" if status.get('monitoring_active') else "❌ Inattivo")

    with col3:
        recent_alerts = len(status.get('recent_alerts', []))
        st.metric("🚨 Alert Recenti", recent_alerts)

    # Health checks dettagliati
    st.subheader("🔍 Controlli Salute Dettagliati")

    checks = health.get('checks', {})
    if checks:
        cols = st.columns(min(len(checks), 4))

        for i, (check_name, check_result) in enumerate(checks.items()):
            col_idx = i % 4
            with cols[col_idx]:
                status_icon = {
                    'healthy': '🟢',
                    'degraded': '🟡',
                    'unhealthy': '🔴',
                    'error': '❌'
                }.get(check_result.get('status'), '⚪')

                st.write(f"**{status_icon} {check_name.title()}**")
                st.caption(check_result.get('message', 'N/A'))

    # Metriche real-time
    st.subheader("📈 Metriche Real-time")

    metrics = status.get('metrics', {})

    tab1, tab2, tab3 = st.tabs(["🖥️ Sistema", "⚙️ Processing", "🚨 Errori"])

    with tab1:
        system_metrics = metrics.get('system', {})
        if system_metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("🖥️ CPU", f"{system_metrics.get('cpu_percent', 0):.1f}%")

            with col2:
                st.metric("🧠 Memoria", f"{system_metrics.get('memory_percent', 0):.1f}%")

            with col3:
                st.metric("💾 Disco", f"{system_metrics.get('disk_usage_percent', 0):.1f}%")

            with col4:
                uptime = system_metrics.get('uptime_seconds', 0)
                st.metric("⏱️ Uptime", f"{uptime/3600:.1f}h")

    with tab2:
        processing_metrics = metrics.get('processing', {})
        if processing_metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📚 Totali", processing_metrics.get('total_files', 0))

            with col2:
                st.metric("⏳ In Attesa", processing_metrics.get('pending_files', 0))

            with col3:
                st.metric("🔄 In Corso", processing_metrics.get('processing_files', 0))

            with col4:
                st.metric("✅ Completati", processing_metrics.get('completed_files', 0))

    with tab3:
        error_metrics = metrics.get('errors', {})
        if error_metrics:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🚨 Errori Aperti", error_metrics.get('total_open_errors', 0))

            with col2:
                st.metric("📊 Errori Recenti", error_metrics.get('recent_error_count', 0))

            with col3:
                categories = error_metrics.get('errors_by_category', [])
                top_category = categories[0]['error_category'] if categories else 'N/A'
                st.metric("🏆 Categoria Top", top_category)

    # Alert recenti
    st.subheader("🚨 Alert Recenti")

    recent_alerts = status.get('recent_alerts', [])
    if recent_alerts:
        for alert in recent_alerts[:5]:
            alert_type = alert.get('type', 'UNKNOWN')
            message = alert.get('message', 'N/A')
            timestamp = alert.get('timestamp', 'N/A')

            st.write(f"**{alert_type}** - {message}")
            st.caption(f"📅 {timestamp}")
    else:
        st.info("✅ Nessun alert recente")

    # Azioni rapide
    st.subheader("⚡ Azioni Rapide")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Health Check Manuale", use_container_width=True):
            health = monitoring_system.health_checker.perform_health_check()
            st.success(f"✅ Health check completato: {health.get('overall_status', 'unknown')}")
            st.rerun()

    with col2:
        if st.button("📊 Colleziona Metriche", use_container_width=True):
            metrics = monitoring_system.metrics_collector.collect_all_metrics()
            st.success(f"✅ Metriche aggiornate: {len(metrics)} categorie")
            st.rerun()

    with col3:
        if st.button("🚨 Test Alert", use_container_width=True):
            test_alert = monitoring_system.alert_manager._send_alert(
                "TEST_ALERT",
                "Questo è un alert di test del sistema di monitoraggio",
                {'test': True, 'timestamp': datetime.now().isoformat()}
            )
            if test_alert:
                st.success("✅ Alert di test inviato")
            else:
                st.error("❌ Errore invio alert di test")

# --- CONFIGURAZIONE DEFAULT ---
default_monitoring_config = MonitoringConfig()

if __name__ == "__main__":
    # Test del sistema di monitoraggio
    print("🧪 Testing Advanced Monitoring System...")

    # Avvia sistema
    monitoring = start_advanced_monitoring()

    # Attendi qualche secondo
    time.sleep(5)

    # Recupera stato
    status = get_system_status()
    print(f"📊 System Status: {status.get('health', {}).get('overall_status', 'unknown')}")

    # Ferma sistema
    stop_advanced_monitoring()
    print("✅ Monitoring system test completed")
