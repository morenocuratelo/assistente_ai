#!/usr/bin/env python3
"""
Advanced Monitoring Setup for Production
Sistema di monitoring e alerting per ambiente produzione
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class MonitoringMetrics:
    """Metriche di monitoring del sistema"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    database_connections: int
    cache_hits: int
    cache_misses: int
    api_response_time: float
    active_users: int
    error_rate: float

class ProductionMonitor:
    """Sistema di monitoring avanzato per produzione"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history: List[MonitoringMetrics] = []
        self.alerts_configured = False
        self._setup_monitoring()

    def _setup_monitoring(self):
        """Configura il sistema di monitoring"""
        # Configurazione logging strutturato
        self._setup_structured_logging()

        # Configurazione metriche
        self._setup_metrics_collection()

        # Configurazione alerting
        self._setup_alerting()

        self.logger.info("Production monitoring system initialized")

    def _setup_structured_logging(self):
        """Configura logging strutturato per produzione"""
        log_format = {
            "timestamp": "%Y-%m-%d %H:%M:%S",
            "level": "%(levelname)s",
            "service": "assistente_ai",
            "component": "%(name)s",
            "message": "%(message)s",
            "trace_id": "%(trace_id)s",
            "user_id": "%(user_id)s"
        }

        # Configurazione handler per file JSON
        os.makedirs("logs", exist_ok=True)

        json_handler = logging.FileHandler("logs/production.json")
        json_handler.setFormatter(json.dumps(log_format))
        self.logger.addHandler(json_handler)

    def _setup_metrics_collection(self):
        """Configura raccolta metriche"""
        self.metrics_interval = 30  # secondi
        self.retention_period = 24 * 60 * 60  # 24 ore

        # Metriche da monitorare
        self.monitored_metrics = {
            "system": ["cpu", "memory", "disk", "network"],
            "application": ["response_time", "error_rate", "throughput"],
            "database": ["connections", "query_time", "pool_usage"],
            "cache": ["hits", "misses", "evictions"],
            "users": ["active", "sessions", "requests"]
        }

    def _setup_alerting(self):
        """Configura sistema di alerting"""
        self.alert_rules = {
            "cpu_usage": {"threshold": 80, "severity": "warning"},
            "memory_usage": {"threshold": 85, "severity": "critical"},
            "error_rate": {"threshold": 5, "severity": "critical"},
            "response_time": {"threshold": 2000, "severity": "warning"},
            "database_connections": {"threshold": 90, "severity": "warning"}
        }

        self.alert_channels = {
            "email": "admin@assistente-ai.com",
            "slack": "production-alerts",
            "pagerduty": "production-team"
        }

        self.alerts_configured = True

    def collect_system_metrics(self) -> Dict[str, float]:
        """Raccoglie metriche di sistema"""
        import psutil

        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            }
        }

        return metrics

    def collect_application_metrics(self) -> Dict[str, float]:
        """Raccoglie metriche applicazione"""
        # Simula metriche applicazione (da integrare con metriche reali)
        metrics = {
            "active_users": 0,  # Da implementare con session tracking
            "api_response_time": 0,  # Da implementare con middleware
            "error_rate": 0,  # Da implementare con error tracking
            "cache_hits": 0,  # Da implementare con cache metrics
            "cache_misses": 0  # Da implementare con cache metrics
        }

        return metrics

    def check_alerts(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Verifica se ci sono alert da generare"""
        alerts = []

        for metric_name, value in metrics.items():
            if metric_name in self.alert_rules:
                rule = self.alert_rules[metric_name]
                if value > rule["threshold"]:
                    alert = {
                        "timestamp": datetime.now(),
                        "metric": metric_name,
                        "value": value,
                        "threshold": rule["threshold"],
                        "severity": rule["severity"],
                        "message": f"{metric_name} exceeded threshold: {value} > {rule['threshold']}"
                    }
                    alerts.append(alert)

        return alerts

    def send_alert(self, alert: Dict[str, Any]):
        """Invia alert tramite i canali configurati"""
        if not self.alerts_configured:
            return

        # Log alert
        self.logger.warning(f"ALERT: {alert['message']}")

        # Qui implementare invio email, Slack, PagerDuty
        # Per ora solo logging

    def run_monitoring_cycle(self):
        """Esegue un ciclo completo di monitoring"""
        try:
            # Raccogli metriche
            system_metrics = self.collect_system_metrics()
            app_metrics = self.collect_application_metrics()

            # Combina metriche
            all_metrics = {**system_metrics, **app_metrics}

            # Crea record metriche
            metrics_record = MonitoringMetrics(
                timestamp=datetime.now(),
                **all_metrics
            )

            # Salva nella history
            self.metrics_history.append(metrics_record)

            # Pulisci history vecchia
            self._cleanup_old_metrics()

            # Verifica alert
            alerts = self.check_alerts(all_metrics)
            for alert in alerts:
                self.send_alert(alert)

            # Log metriche
            self.logger.info(f"Metrics collected: {len(all_metrics)} metrics")

        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {str(e)}")

    def _cleanup_old_metrics(self):
        """Pulisce metriche vecchie oltre il retention period"""
        cutoff_time = datetime.now() - timedelta(seconds=self.retention_period)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]

    def get_health_status(self) -> Dict[str, Any]:
        """Restituisce status health del sistema"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "No metrics available"}

        latest = self.metrics_history[-1]

        # Valuta health based on latest metrics
        issues = []
        if latest.cpu_usage > 90:
            issues.append("High CPU usage")
        if latest.memory_usage > 90:
            issues.append("High memory usage")
        if latest.error_rate > 5:
            issues.append("High error rate")

        if issues:
            return {
                "status": "unhealthy",
                "issues": issues,
                "metrics": {
                    "cpu": latest.cpu_usage,
                    "memory": latest.memory_usage,
                    "error_rate": latest.error_rate
                }
            }
        else:
            return {
                "status": "healthy",
                "message": "All systems operational",
                "metrics": {
                    "cpu": latest.cpu_usage,
                    "memory": latest.memory_usage,
                    "error_rate": latest.error_rate
                }
            }

    def generate_report(self) -> Dict[str, Any]:
        """Genera report di monitoring"""
        if not self.metrics_history:
            return {"error": "No metrics available"}

        # Calcola statistiche
        cpu_values = [m.cpu_usage for m in self.metrics_history]
        memory_values = [m.memory_usage for m in self.metrics_history]

        report = {
            "period": {
                "start": self.metrics_history[0].timestamp,
                "end": self.metrics_history[-1].timestamp
            },
            "averages": {
                "cpu_usage": sum(cpu_values) / len(cpu_values),
                "memory_usage": sum(memory_values) / len(memory_values)
            },
            "peaks": {
                "cpu_usage": max(cpu_values),
                "memory_usage": max(memory_values)
            },
            "current_status": self.get_health_status(),
            "alerts_count": len([a for a in self.metrics_history if hasattr(a, 'alerts')])
        }

        return report

# Istanza globale monitor
production_monitor = ProductionMonitor()

def start_monitoring():
    """Avvia monitoring in background"""
    import threading

    def monitoring_loop():
        while True:
            try:
                production_monitor.run_monitoring_cycle()
                time.sleep(production_monitor.metrics_interval)
            except Exception as e:
                production_monitor.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(60)  # Attendi 1 minuto prima di riprovare

    # Avvia thread monitoring
    monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitor_thread.start()
    production_monitor.logger.info("Production monitoring started")

if __name__ == "__main__":
    start_monitoring()
