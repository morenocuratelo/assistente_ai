#!/usr/bin/env python3
"""
Emergency Rollback Plan for Production
Piano rollback emergenza per ambiente produzione
"""

import os
import sys
import shutil
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import tarfile
import sqlite3
from pathlib import Path

class RollbackManager:
    """Gestore rollback emergenza per produzione"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Configurazione rollback
        self.rollback_timeout = 300  # 5 minuti
        self.max_rollback_attempts = 3
        self.backup_base_dir = "backups"

        # Stati rollback
        self.rollback_states = {
            "pending": "Rollback pianificato",
            "in_progress": "Rollback in esecuzione",
            "completed": "Rollback completato",
            "failed": "Rollback fallito",
            "cancelled": "Rollback cancellato"
        }

    def setup_logging(self):
        """Configura logging per rollback"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rollback.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def detect_deployment_issue(self) -> Dict[str, any]:
        """Rileva issue deployment che richiedono rollback"""
        self.logger.info("Detecting deployment issues...")

        issues = {
            "critical_issues": [],
            "warning_issues": [],
            "info_issues": []
        }

        try:
            # Verifica health system
            health_status = self.check_system_health()
            if not health_status["healthy"]:
                issues["critical_issues"].append({
                    "type": "system_health",
                    "message": "System health check failed",
                    "details": health_status
                })

            # Verifica database connectivity
            if not self.check_database_connectivity():
                issues["critical_issues"].append({
                    "type": "database",
                    "message": "Database connectivity failed"
                })

            # Verifica servizi AI
            if not self.check_ai_services():
                issues["critical_issues"].append({
                    "type": "ai_services",
                    "message": "AI services unavailable"
                })

            # Verifica performance
            performance_metrics = self.check_performance_metrics()
            if performance_metrics["degraded"]:
                issues["warning_issues"].append({
                    "type": "performance",
                    "message": "Performance degraded",
                    "details": performance_metrics
                })

            # Verifica error rate
            error_rate = self.check_error_rate()
            if error_rate > 10:  # 10% error rate
                issues["critical_issues"].append({
                    "type": "error_rate",
                    "message": f"High error rate: {error_rate}%"
                })

            return issues

        except Exception as e:
            self.logger.error(f"Issue detection failed: {str(e)}")
            return {"critical_issues": [{"type": "detection_error", "message": str(e)}]}

    def check_system_health(self) -> Dict[str, any]:
        """Verifica health del sistema"""
        health = {
            "healthy": True,
            "checks": []
        }

        try:
            # Verifica CPU e memoria
            import psutil

            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent

            health["checks"].append({"component": "cpu", "status": "ok" if cpu_usage < 90 else "critical"})
            health["checks"].append({"component": "memory", "status": "ok" if memory_usage < 90 else "critical"})

            if cpu_usage > 90 or memory_usage > 90:
                health["healthy"] = False

        except Exception as e:
            health["healthy"] = False
            health["checks"].append({"component": "system", "status": "error", "message": str(e)})

        return health

    def check_database_connectivity(self) -> bool:
        """Verifica connettività database"""
        try:
            # Trova database files
            db_files = self.find_database_files()

            for db_file in db_files:
                if os.path.exists(db_file):
                    with sqlite3.connect(db_file) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()

                        if result[0] != 1:
                            return False

            return True

        except Exception as e:
            self.logger.error(f"Database connectivity check failed: {str(e)}")
            return False

    def find_database_files(self) -> List[str]:
        """Trova file database"""
        db_files = [
            "test_metadata.sqlite",
            "metadata.sqlite",
            "db_memoria/metadata.sqlite",
            "db_memoria/chroma.sqlite3"
        ]

        existing_files = []
        for db_file in db_files:
            if os.path.exists(db_file):
                existing_files.append(db_file)

        return existing_files

    def check_ai_services(self) -> bool:
        """Verifica servizi AI"""
        try:
            # Verifica configurazione AI
            ai_config = os.getenv("OPENAI_API_KEY")
            if not ai_config:
                return False

            # Qui implementare test chiamate AI
            # Per ora solo verifica configurazione

            return True

        except Exception as e:
            self.logger.error(f"AI services check failed: {str(e)}")
            return False

    def check_performance_metrics(self) -> Dict[str, any]:
        """Verifica metriche performance"""
        metrics = {
            "degraded": False,
            "response_time": 0,
            "throughput": 0,
            "memory_usage": 0
        }

        try:
            import psutil

            # Verifica memoria
            memory = psutil.virtual_memory()
            metrics["memory_usage"] = memory.percent

            if memory.percent > 85:
                metrics["degraded"] = True

        except Exception as e:
            self.logger.error(f"Performance check failed: {str(e)}")
            metrics["degraded"] = True

        return metrics

    def check_error_rate(self) -> float:
        """Verifica error rate"""
        try:
            # Qui implementare verifica error rate da log
            # Per ora return 0 (no errors)
            return 0.0

        except Exception as e:
            self.logger.error(f"Error rate check failed: {str(e)}")
            return 100.0

    def initiate_emergency_rollback(self, reason: str) -> bool:
        """Avvia rollback emergenza"""
        self.logger.critical(f"EMERGENCY ROLLBACK INITIATED: {reason}")

        try:
            # Crea record rollback
            rollback_record = self.create_rollback_record("emergency", reason)

            # Trova backup più recente
            latest_backup = self.find_latest_backup()

            if not latest_backup:
                self.logger.error("No backup found for rollback")
                return False

            # Esegui rollback
            success = self.execute_rollback(latest_backup, rollback_record)

            if success:
                self.logger.critical("EMERGENCY ROLLBACK COMPLETED SUCCESSFULLY")
                self.update_rollback_record(rollback_record["id"], "completed")
                return True
            else:
                self.logger.critical("EMERGENCY ROLLBACK FAILED")
                self.update_rollback_record(rollback_record["id"], "failed")
                return False

        except Exception as e:
            self.logger.error(f"Emergency rollback failed: {str(e)}")
            return False

    def create_rollback_record(self, rollback_type: str, reason: str) -> Dict:
        """Crea record rollback"""
        record = {
            "id": f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": rollback_type,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": [],
            "errors": []
        }

        # Salva record
        record_file = f"rollback_{record['id']}.json"
        with open(record_file, 'w') as f:
            json.dump(record, f, indent=2)

        return record

    def update_rollback_record(self, rollback_id: str, status: str, step: Optional[str] = None, error: Optional[str] = None):
        """Aggiorna record rollback"""
        record_file = f"rollback_{rollback_id}.json"

        if not os.path.exists(record_file):
            return

        try:
            with open(record_file, 'r') as f:
                record = json.load(f)

            record["status"] = status

            if step:
                record["steps"].append({
                    "step": step,
                    "timestamp": datetime.now().isoformat()
                })

            if error:
                record["errors"].append({
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })

            with open(record_file, 'w') as f:
                json.dump(record, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to update rollback record: {str(e)}")

    def find_latest_backup(self) -> Optional[str]:
        """Trova backup più recente"""
        try:
            backup_dir = f"{self.backup_base_dir}/daily"

            if not os.path.exists(backup_dir):
                return None

            latest_backup = None
            latest_time = 0

            for item in os.listdir(backup_dir):
                if item.startswith("full_backup_") and item.endswith(".tar.gz"):
                    backup_path = os.path.join(backup_dir, item)
                    backup_time = os.path.getmtime(backup_path)

                    if backup_time > latest_time:
                        latest_time = backup_time
                        latest_backup = backup_path

            return latest_backup

        except Exception as e:
            self.logger.error(f"Error finding latest backup: {str(e)}")
            return None

    def execute_rollback(self, backup_path: str, rollback_record: Dict) -> bool:
        """Esegue rollback da backup"""
        self.logger.info(f"Executing rollback from: {backup_path}")

        try:
            # Verifica backup
            if not self.verify_backup_integrity(backup_path):
                raise Exception("Backup integrity verification failed")

            # Crea backup stato attuale
            current_backup = self.create_current_state_backup()
            if current_backup:
                self.logger.info(f"Current state backup created: {current_backup}")

            # Estrai backup
            extract_dir = f"rollback_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(extract_dir, exist_ok=True)

            self.update_rollback_record(rollback_record["id"], "in_progress", "extracting_backup")

            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(extract_dir)

            # Ripristina database
            self.update_rollback_record(rollback_record["id"], "in_progress", "restoring_database")
            if not self.restore_database(extract_dir):
                raise Exception("Database restore failed")

            # Ripristina configurazione
            self.update_rollback_record(rollback_record["id"], "in_progress", "restoring_config")
            if not self.restore_configuration(extract_dir):
                raise Exception("Configuration restore failed")

            # Ripristina uploads
            self.update_rollback_record(rollback_record["id"], "in_progress", "restoring_uploads")
            if not self.restore_uploads(extract_dir):
                raise Exception("Uploads restore failed")

            # Verifica ripristino
            self.update_rollback_record(rollback_record["id"], "in_progress", "verifying_restore")
            if not self.verify_restore():
                raise Exception("Restore verification failed")

            # Pulisci directory temporanea
            shutil.rmtree(extract_dir)

            self.logger.info("Rollback execution completed")
            return True

        except Exception as e:
            self.logger.error(f"Rollback execution failed: {str(e)}")
            self.update_rollback_record(rollback_record["id"], "failed", error=str(e))
            return False

    def verify_backup_integrity(self, backup_path: str) -> bool:
        """Verifica integrità backup"""
        try:
            if not os.path.exists(backup_path):
                return False

            # Verifica archivio tar.gz
            with tarfile.open(backup_path, 'r:gz') as tar:
                # Prova a leggere manifest
                manifest_member = tar.getmember('manifest.json')
                if not manifest_member:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Backup integrity check failed: {str(e)}")
            return False

    def create_current_state_backup(self) -> Optional[str]:
        """Crea backup stato attuale prima rollback"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pre_rollback_backup_{timestamp}"
            backup_path = f"{self.backup_base_dir}/emergency/{backup_name}"

            os.makedirs(f"{self.backup_base_dir}/emergency", exist_ok=True)

            # Backup database attuale
            db_files = self.find_database_files()
            for db_file in db_files:
                if os.path.exists(db_file):
                    shutil.copy2(db_file, f"{backup_path}/")

            # Backup configurazione attuale
            config_files = ["src/config/", "pyproject.toml", "requirements.txt"]
            for config_file in config_files:
                if os.path.exists(config_file):
                    if os.path.isdir(config_file):
                        shutil.copytree(config_file, f"{backup_path}/{os.path.basename(config_file)}")
                    else:
                        shutil.copy2(config_file, backup_path)

            return backup_path

        except Exception as e:
            self.logger.error(f"Pre-rollback backup failed: {str(e)}")
            return None

    def restore_database(self, extract_dir: str) -> bool:
        """Ripristina database da backup"""
        try:
            # Trova file database nel backup
            db_files = self.find_database_files()

            for db_file in db_files:
                backup_db = os.path.join(extract_dir, os.path.basename(db_file))

                if os.path.exists(backup_db):
                    # Backup database attuale
                    current_backup = f"{db_file}.current"
                    if os.path.exists(db_file):
                        shutil.copy2(db_file, current_backup)

                    # Ripristina database
                    shutil.copy2(backup_db, db_file)

                    # Verifica ripristino
                    if not self.verify_database_integrity(db_file):
                        # Ripristina backup se verifica fallita
                        if os.path.exists(current_backup):
                            shutil.copy2(current_backup, db_file)
                        return False

                    # Rimuovi backup temporaneo
                    if os.path.exists(current_backup):
                        os.remove(current_backup)

            return True

        except Exception as e:
            self.logger.error(f"Database restore failed: {str(e)}")
            return False

    def verify_database_integrity(self, db_path: str) -> bool:
        """Verifica integrità database"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()

                return result[0] == "ok"

        except Exception as e:
            self.logger.error(f"Database integrity check failed: {str(e)}")
            return False

    def restore_configuration(self, extract_dir: str) -> bool:
        """Ripristina configurazione da backup"""
        try:
            config_backup = os.path.join(extract_dir, "config")

            if os.path.exists(config_backup):
                # Backup configurazione attuale
                current_config_backup = "config_current_backup"
                if os.path.exists("src/config"):
                    shutil.move("src/config", current_config_backup)

                # Ripristina configurazione
                shutil.move(config_backup, "src/config")

                # Rimuovi backup se ripristino ok
                if os.path.exists(current_config_backup):
                    shutil.rmtree(current_config_backup)

            return True

        except Exception as e:
            self.logger.error(f"Configuration restore failed: {str(e)}")
            return False

    def restore_uploads(self, extract_dir: str) -> bool:
        """Ripristina uploads da backup"""
        try:
            uploads_backup = os.path.join(extract_dir, "uploads")

            if os.path.exists(uploads_backup):
                # Backup uploads attuali
                current_uploads_backup = "uploads_current_backup"
                for upload_dir in ["uploads", "documents", "static"]:
                    if os.path.exists(upload_dir):
                        shutil.move(upload_dir, f"{current_uploads_backup}_{upload_dir}")

                # Ripristina uploads
                shutil.move(uploads_backup, "uploads")

                # Rimuovi backup se ripristino ok
                if os.path.exists(current_uploads_backup):
                    shutil.rmtree(current_uploads_backup)

            return True

        except Exception as e:
            self.logger.error(f"Uploads restore failed: {str(e)}")
            return False

    def verify_restore(self) -> bool:
        """Verifica che il ripristino sia stato completato correttamente"""
        try:
            # Verifica database
            if not self.check_database_connectivity():
                return False

            # Verifica configurazione
            if not os.path.exists("src/config"):
                return False

            # Verifica servizi AI
            if not self.check_ai_services():
                return False

            # Verifica health system
            health = self.check_system_health()
            if not health["healthy"]:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Restore verification failed: {str(e)}")
            return False

    def schedule_rollback_check(self, interval_minutes: int = 5):
        """Configura verifica rollback periodica"""
        self.logger.info(f"Scheduling rollback check every {interval_minutes} minutes")

        # Qui implementare scheduling
        # Per ora solo configurazione

        schedule_config = {
            "rollback_check": {
                "interval_minutes": interval_minutes,
                "enabled": True,
                "auto_rollback_threshold": {
                    "error_rate": 15,
                    "response_time": 5000,
                    "memory_usage": 95
                }
            }
        }

        config_file = "rollback_schedule.json"
        with open(config_file, 'w') as f:
            json.dump(schedule_config, f, indent=2)

        self.logger.info(f"Rollback check schedule configured: {config_file}")

    def generate_rollback_report(self) -> str:
        """Genera report rollback"""
        report = {
            "rollback_summary": {
                "report_date": datetime.now().isoformat(),
                "available_backups": self.list_available_backups(),
                "rollback_history": self.get_rollback_history(),
                "system_health": self.check_system_health(),
                "auto_rollback_configured": os.path.exists("rollback_schedule.json")
            }
        }

        report_file = f"rollback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Rollback report generated: {report_file}")
        return report_file

    def list_available_backups(self) -> List[Dict]:
        """Lista backup disponibili per rollback"""
        backups = []

        try:
            backup_dir = f"{self.backup_base_dir}/daily"

            if os.path.exists(backup_dir):
                for item in os.listdir(backup_dir):
                    if item.startswith("full_backup_") and item.endswith(".tar.gz"):
                        backup_path = os.path.join(backup_dir, item)

                        try:
                            stat = os.stat(backup_path)
                            backups.append({
                                "path": backup_path,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "verified": self.verify_backup_integrity(backup_path)
                            })
                        except (OSError, IOError):
                            pass

        except Exception as e:
            self.logger.error(f"Error listing backups: {str(e)}")

        # Ordina per data modifica
        backups.sort(key=lambda x: x["modified"], reverse=True)

        return backups

    def get_rollback_history(self) -> List[Dict]:
        """Ottiene history rollback"""
        history = []

        try:
            for file in os.listdir("."):
                if file.startswith("rollback_") and file.endswith(".json"):
                    try:
                        with open(file, 'r') as f:
                            record = json.load(f)
                            history.append(record)
                    except Exception:
                        pass

        except Exception as e:
            self.logger.error(f"Error reading rollback history: {str(e)}")

        # Ordina per timestamp
        history.sort(key=lambda x: x["timestamp"], reverse=True)

        return history

    def run_emergency_procedures(self):
        """Esegue procedure emergenza"""
        self.logger.critical("RUNNING EMERGENCY PROCEDURES")

        try:
            # 1. Verifica issue
            issues = self.detect_deployment_issue()

            if not issues["critical_issues"]:
                self.logger.info("No critical issues detected")
                return

            # 2. Valuta se rollback necessario
            rollback_needed = self.evaluate_rollback_necessity(issues)

            if rollback_needed:
                # 3. Avvia rollback
                reason = f"Critical issues detected: {len(issues['critical_issues'])} issues"
                success = self.initiate_emergency_rollback(reason)

                if success:
                    self.logger.critical("EMERGENCY ROLLBACK COMPLETED")
                else:
                    self.logger.critical("EMERGENCY ROLLBACK FAILED - MANUAL INTERVENTION REQUIRED")

            # 4. Notifica team
            self.notify_emergency_team(issues)

        except Exception as e:
            self.logger.error(f"Emergency procedures failed: {str(e)}")

    def evaluate_rollback_necessity(self, issues: Dict) -> bool:
        """Valuta se rollback è necessario"""
        # Rollback necessario se:
        # - Issue critici > 0
        # - Error rate > 20%
        # - System health fallito

        if issues["critical_issues"]:
            return True

        # Verifica error rate
        if self.check_error_rate() > 20:
            return True

        # Verifica system health
        health = self.check_system_health()
        if not health["healthy"]:
            return True

        return False

    def notify_emergency_team(self, issues: Dict):
        """Notifica team emergenza"""
        self.logger.critical("NOTIFYING EMERGENCY TEAM")

        notification = {
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "system_health": self.check_system_health(),
            "recommended_action": "rollback" if self.evaluate_rollback_necessity(issues) else "investigate"
        }

        # Qui implementare notifiche email, Slack, PagerDuty
        # Per ora solo log

        self.logger.critical(f"EMERGENCY NOTIFICATION: {json.dumps(notification, indent=2)}")

def main():
    """Main rollback function"""
    rollback_manager = RollbackManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "emergency":
            # Rollback emergenza
            reason = sys.argv[2] if len(sys.argv) > 2 else "Emergency rollback requested"
            success = rollback_manager.initiate_emergency_rollback(reason)

            if success:
                print("✅ Emergency rollback completed successfully")
                sys.exit(0)
            else:
                print("❌ Emergency rollback failed")
                sys.exit(1)

        elif command == "check":
            # Verifica sistema
            issues = rollback_manager.detect_deployment_issue()

            if issues["critical_issues"]:
                print(f"❌ Critical issues detected: {len(issues['critical_issues'])}")
                for issue in issues["critical_issues"]:
                    print(f"  - {issue['type']}: {issue['message']}")
                sys.exit(1)
            else:
                print("✅ No critical issues detected")
                sys.exit(0)

        elif command == "report":
            # Genera report
            report_file = rollback_manager.generate_rollback_report()
            print(f"📊 Rollback report generated: {report_file}")
            sys.exit(0)

    else:
        print("Usage:")
        print("  python rollback_plan.py emergency [reason]  - Execute emergency rollback")
        print("  python rollback_plan.py check               - Check for deployment issues")
        print("  python rollback_plan.py report              - Generate rollback report")
        sys.exit(1)

if __name__ == "__main__":
    main()
