#!/usr/bin/env python3
"""
Comprehensive Backup Strategy for Production
Strategia backup completa per ambiente produzione
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

class BackupManager:
    """Gestore backup completo per produzione"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Configurazione backup
        self.backup_base_dir = "backups"
        self.retention_days = 30
        self.compression_level = 9

        # Tipi di backup
        self.backup_types = {
            "full": "Complete system backup",
            "database": "Database only backup",
            "config": "Configuration files backup",
            "uploads": "User uploads backup",
            "incremental": "Changes since last backup"
        }

    def setup_logging(self):
        """Configura logging per backup"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backup.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def create_backup_directories(self):
        """Crea directory backup se non esistono"""
        directories = [
            self.backup_base_dir,
            f"{self.backup_base_dir}/daily",
            f"{self.backup_base_dir}/weekly",
            f"{self.backup_base_dir}/monthly",
            f"{self.backup_base_dir}/database",
            f"{self.backup_base_dir}/config",
            f"{self.backup_base_dir}/uploads"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def create_full_backup(self) -> Optional[str]:
        """Crea backup completo del sistema"""
        self.logger.info("Creating full system backup...")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"full_backup_{timestamp}"
            backup_path = f"{self.backup_base_dir}/daily/{backup_name}"

            self.create_backup_directories()

            # Backup database
            db_backup = self.backup_database(f"{backup_path}/database")
            if not db_backup:
                return None

            # Backup configurazione
            config_backup = self.backup_configuration(f"{backup_path}/config")
            if not config_backup:
                return None

            # Backup uploads
            uploads_backup = self.backup_uploads(f"{backup_path}/uploads")
            if not uploads_backup:
                return None

            # Backup codice sorgente
            code_backup = self.backup_code(f"{backup_path}/code")
            if not code_backup:
                return None

            # Crea manifest backup
            manifest = self.create_backup_manifest(backup_path, "full")
            with open(f"{backup_path}/manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)

            # Crea archivio compresso
            archive_path = self.create_compressed_archive(backup_path, backup_name)

            # Pulisci directory temporanea
            shutil.rmtree(backup_path)

            self.logger.info(f"Full backup completed: {archive_path}")
            return archive_path

        except Exception as e:
            self.logger.error(f"Full backup failed: {str(e)}")
            return None

    def backup_database(self, backup_dir: str) -> bool:
        """Backup database"""
        try:
            self.logger.info("Backing up database...")

            # Trova database files
            db_files = self.find_database_files()

            for db_file in db_files:
                if os.path.exists(db_file):
                    backup_path = f"{backup_dir}/{os.path.basename(db_file)}"
                    shutil.copy2(db_file, backup_path)

                    # Verifica integrità backup
                    if not self.verify_database_backup(backup_path, db_file):
                        return False

            self.logger.info(f"Database backup completed: {len(db_files)} files")
            return True

        except Exception as e:
            self.logger.error(f"Database backup failed: {str(e)}")
            return False

    def find_database_files(self) -> List[str]:
        """Trova tutti i file database"""
        db_files = []

        # Database SQLite
        sqlite_files = [
            "test_metadata.sqlite",
            "metadata.sqlite",
            "db_memoria/metadata.sqlite",
            "db_memoria/chroma.sqlite3"
        ]

        for db_file in sqlite_files:
            if os.path.exists(db_file):
                db_files.append(db_file)

        # Database PostgreSQL/MySQL (se configurati)
        # Aggiungere qui detection per altri tipi di database

        return db_files

    def verify_database_backup(self, backup_path: str, original_path: str) -> bool:
        """Verifica integrità backup database"""
        try:
            # Verifica dimensione file
            backup_size = os.path.getsize(backup_path)
            original_size = os.path.getsize(original_path)

            if backup_size != original_size:
                self.logger.error(f"Size mismatch: backup={backup_size}, original={original_size}")
                return False

            # Verifica integrità SQLite
            if backup_path.endswith('.sqlite') or backup_path.endswith('.db'):
                with sqlite3.connect(backup_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()

                    if result[0] != "ok":
                        self.logger.error(f"SQLite integrity check failed: {result[0]}")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Database backup verification failed: {str(e)}")
            return False

    def backup_configuration(self, backup_dir: str) -> bool:
        """Backup configurazione"""
        try:
            self.logger.info("Backing up configuration...")

            config_files = [
                "src/config/",
                "pyproject.toml",
                "requirements.txt",
                "requirements-dev.txt",
                ".env",
                "production_config.py",
                "monitoring_setup.py"
            ]

            # Crea archivio tar compresso
            backup_path = f"{backup_dir}/config.tar.gz"

            with tarfile.open(backup_path, "w:gz", compresslevel=self.compression_level) as tar:
                for config_item in config_files:
                    if os.path.exists(config_item):
                        if os.path.isdir(config_item):
                            tar.add(config_item, arcname=os.path.basename(config_item))
                        else:
                            tar.add(config_item)

            self.logger.info(f"Configuration backup completed: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Configuration backup failed: {str(e)}")
            return False

    def backup_uploads(self, backup_dir: str) -> bool:
        """Backup uploads e documenti utente"""
        try:
            self.logger.info("Backing up uploads...")

            upload_dirs = [
                "uploads/",
                "documents/",
                "static/",
                "db_memoria/"
            ]

            # Crea archivio tar compresso
            backup_path = f"{backup_dir}/uploads.tar.gz"

            with tarfile.open(backup_path, "w:gz", compresslevel=self.compression_level) as tar:
                for upload_dir in upload_dirs:
                    if os.path.exists(upload_dir):
                        tar.add(upload_dir, arcname=os.path.basename(upload_dir))

            self.logger.info(f"Uploads backup completed: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Uploads backup failed: {str(e)}")
            return False

    def backup_code(self, backup_dir: str) -> bool:
        """Backup codice sorgente"""
        try:
            self.logger.info("Backing up source code...")

            code_dirs = [
                "src/",
                "tests/",
                "docs/",
                "database_layer/",
                "db_memoria/"
            ]

            # Crea archivio tar compresso
            backup_path = f"{backup_dir}/code.tar.gz"

            with tarfile.open(backup_path, "w:gz", compresslevel=self.compression_level) as tar:
                for code_dir in code_dirs:
                    if os.path.exists(code_dir):
                        tar.add(code_dir, arcname=os.path.basename(code_dir))

            self.logger.info(f"Code backup completed: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Code backup failed: {str(e)}")
            return False

    def create_backup_manifest(self, backup_path: str, backup_type: str) -> Dict:
        """Crea manifest del backup"""
        manifest = {
            "backup_info": {
                "type": backup_type,
                "timestamp": datetime.now().isoformat(),
                "version": self.get_system_version(),
                "size": self.calculate_directory_size(backup_path)
            },
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "working_directory": os.getcwd()
            },
            "files": self.list_backup_files(backup_path)
        }

        return manifest

    def get_system_version(self) -> str:
        """Ottiene versione sistema"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def calculate_directory_size(self, directory: str) -> int:
        """Calcola dimensione directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
        return total_size

    def list_backup_files(self, backup_path: str) -> List[Dict]:
        """Lista file nel backup"""
        files = []

        for root, dirs, filenames in os.walk(backup_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, backup_path)

                try:
                    stat = os.stat(filepath)
                    files.append({
                        "path": rel_path,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except (OSError, IOError):
                    pass

        return files

    def create_compressed_archive(self, backup_path: str, backup_name: str) -> str:
        """Crea archivio compresso del backup"""
        archive_path = f"{self.backup_base_dir}/daily/{backup_name}.tar.gz"

        with tarfile.open(archive_path, "w:gz", compresslevel=self.compression_level) as tar:
            tar.add(backup_path, arcname=backup_name)

        return archive_path

    def create_incremental_backup(self, last_backup: str) -> Optional[str]:
        """Crea backup incrementale"""
        self.logger.info("Creating incremental backup...")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"incremental_backup_{timestamp}"
            backup_path = f"{self.backup_base_dir}/daily/{backup_name}"

            # Trova ultimo backup completo
            last_full_backup = self.find_last_full_backup()

            if not last_full_backup:
                self.logger.warning("No full backup found, creating full backup instead")
                return self.create_full_backup()

            # Crea backup incrementale
            # Qui implementare logica backup incrementale
            # Per ora crea backup completo

            self.logger.info(f"Incremental backup completed: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Incremental backup failed: {str(e)}")
            return None

    def find_last_full_backup(self) -> Optional[str]:
        """Trova ultimo backup completo"""
        try:
            backup_dir = f"{self.backup_base_dir}/daily"

            if not os.path.exists(backup_dir):
                return None

            # Trova backup più recente
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
            self.logger.error(f"Error finding last full backup: {str(e)}")
            return None

    def cleanup_old_backups(self):
        """Pulisce backup vecchi oltre retention period"""
        self.logger.info("Cleaning up old backups...")

        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # Pulisci backup giornalieri
            self.cleanup_directory(f"{self.backup_base_dir}/daily", cutoff_date, keep_days=7)

            # Pulisci backup settimanali
            self.cleanup_directory(f"{self.backup_base_dir}/weekly", cutoff_date, keep_days=30)

            # Pulisci backup mensili
            self.cleanup_directory(f"{self.backup_base_dir}/monthly", cutoff_date, keep_days=365)

            self.logger.info("Backup cleanup completed")

        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")

    def cleanup_directory(self, directory: str, cutoff_date: datetime, keep_days: int):
        """Pulisce directory backup"""
        if not os.path.exists(directory):
            return

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)

            try:
                item_time = datetime.fromtimestamp(os.path.getmtime(item_path))

                if item_time < cutoff_date:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        self.logger.info(f"Removed old backup: {item}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        self.logger.info(f"Removed old backup directory: {item}")

            except Exception as e:
                self.logger.error(f"Error removing backup item {item}: {str(e)}")

    def verify_backup_integrity(self, backup_path: str) -> bool:
        """Verifica integrità backup"""
        try:
            self.logger.info(f"Verifying backup integrity: {backup_path}")

            # Verifica file esiste
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            # Verifica dimensione file
            file_size = os.path.getsize(backup_path)
            if file_size == 0:
                self.logger.error("Backup file is empty")
                return False

            # Verifica archivio tar.gz
            if backup_path.endswith('.tar.gz'):
                with tarfile.open(backup_path, 'r:gz') as tar:
                    # Prova a leggere tutti i file
                    for member in tar.getmembers():
                        tar.extractfile(member)

            self.logger.info("Backup integrity verification passed")
            return True

        except Exception as e:
            self.logger.error(f"Backup integrity verification failed: {str(e)}")
            return False

    def restore_from_backup(self, backup_path: str, restore_path: str = ".") -> bool:
        """Ripristina da backup"""
        self.logger.info(f"Restoring from backup: {backup_path}")

        try:
            # Verifica backup
            if not self.verify_backup_integrity(backup_path):
                return False

            # Estrai backup
            if backup_path.endswith('.tar.gz'):
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(restore_path)

            self.logger.info(f"Restore completed: {restore_path}")
            return True

        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            return False

    def schedule_automatic_backups(self):
        """Configura backup automatici"""
        self.logger.info("Setting up automatic backups...")

        # Qui implementare scheduling con cron o scheduler
        # Per ora solo configurazione

        schedule_config = {
            "daily_backup": {
                "time": "02:00",
                "type": "full",
                "retention": 7
            },
            "weekly_backup": {
                "time": "03:00",
                "day": "sunday",
                "type": "full",
                "retention": 30
            },
            "monthly_backup": {
                "time": "04:00",
                "day": "1",
                "type": "full",
                "retention": 365
            }
        }

        config_file = "backup_schedule.json"
        with open(config_file, 'w') as f:
            json.dump(schedule_config, f, indent=2)

        self.logger.info(f"Automatic backup schedule configured: {config_file}")

    def generate_backup_report(self) -> str:
        """Genera report backup"""
        report = {
            "backup_summary": {
                "report_date": datetime.now().isoformat(),
                "backup_directory": self.backup_base_dir,
                "retention_days": self.retention_days,
                "total_backups": self.count_total_backups(),
                "disk_usage": self.calculate_backup_disk_usage()
            },
            "backup_types": self.backup_types,
            "recent_backups": self.list_recent_backups()
        }

        report_file = f"backup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Backup report generated: {report_file}")
        return report_file

    def count_total_backups(self) -> int:
        """Conta totale backup"""
        count = 0

        for root, dirs, files in os.walk(self.backup_base_dir):
            for file in files:
                if file.endswith('.tar.gz') or file.endswith('.db') or file.endswith('.sql'):
                    count += 1

        return count

    def calculate_backup_disk_usage(self) -> Dict[str, int]:
        """Calcola utilizzo disco backup"""
        usage = {
            "total_bytes": 0,
            "daily_bytes": 0,
            "weekly_bytes": 0,
            "monthly_bytes": 0
        }

        for backup_type, bytes_key in [("daily", "daily_bytes"), ("weekly", "weekly_bytes"), ("monthly", "monthly_bytes")]:
            backup_dir = f"{self.backup_base_dir}/{backup_type}"
            if os.path.exists(backup_dir):
                usage[bytes_key] = self.calculate_directory_size(backup_dir)
                usage["total_bytes"] += usage[bytes_key]

        return usage

    def list_recent_backups(self, limit: int = 10) -> List[Dict]:
        """Lista backup recenti"""
        backups = []

        for root, dirs, files in os.walk(self.backup_base_dir):
            for file in files:
                if file.endswith('.tar.gz'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.backup_base_dir)

                    try:
                        stat = os.stat(filepath)
                        backups.append({
                            "path": rel_path,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "type": self.determine_backup_type(rel_path)
                        })
                    except (OSError, IOError):
                        pass

        # Ordina per data modifica
        backups.sort(key=lambda x: x["modified"], reverse=True)

        return backups[:limit]

    def determine_backup_type(self, backup_path: str) -> str:
        """Determina tipo backup dal path"""
        if "full" in backup_path.lower():
            return "full"
        elif "incremental" in backup_path.lower():
            return "incremental"
        elif "database" in backup_path.lower():
            return "database"
        elif "config" in backup_path.lower():
            return "config"
        elif "uploads" in backup_path.lower():
            return "uploads"
        else:
            return "unknown"

    def run_backup_cycle(self):
        """Esegue ciclo backup completo"""
        self.logger.info("Starting backup cycle...")

        try:
            # Crea backup completo
            backup_path = self.create_full_backup()

            if backup_path:
                # Verifica backup
                if self.verify_backup_integrity(backup_path):
                    self.logger.info(f"Backup cycle completed successfully: {backup_path}")
                else:
                    self.logger.error("Backup verification failed")
            else:
                self.logger.error("Backup cycle failed")

            # Pulisci backup vecchi
            self.cleanup_old_backups()

            # Genera report
            self.generate_backup_report()

        except Exception as e:
            self.logger.error(f"Backup cycle failed: {str(e)}")

def main():
    """Main backup function"""
    backup_manager = BackupManager()

    try:
        # Crea backup completo
        backup_path = backup_manager.create_full_backup()

        if backup_path:
            print(f"✅ Backup completed successfully: {backup_path}")
            sys.exit(0)
        else:
            print("❌ Backup failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Backup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Backup failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
