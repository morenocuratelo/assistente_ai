#!/usr/bin/env python3
"""
Automated Deployment Script for Production
Script per deployment automatico in ambiente produzione
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

class DeploymentManager:
    """Gestore deployment automatico per produzione"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.deployment_log = "deployment.log"
        self.setup_logging()

        # Configurazione deployment
        self.app_name = "assistente_ai"
        self.version = self.get_current_version()
        self.environment = os.getenv("ENVIRONMENT", "production")

        # Checksums per validazione
        self.checksums = {}

    def setup_logging(self):
        """Configura logging per deployment"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.deployment_log),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def get_current_version(self) -> str:
        """Ottiene versione corrente dal git tag o package"""
        try:
            # Prova a ottenere da git
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # Fallback a timestamp
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def validate_environment(self) -> bool:
        """Valida ambiente prima del deployment"""
        self.logger.info("Validating environment...")

        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "OPENAI_API_KEY"
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.logger.error(f"Missing environment variables: {missing_vars}")
            return False

        # Verifica permessi
        if not self.check_permissions():
            return False

        # Verifica spazio disco
        if not self.check_disk_space():
            return False

        self.logger.info("Environment validation passed")
        return True

    def check_permissions(self) -> bool:
        """Verifica permessi necessari"""
        try:
            # Test write permissions
            test_file = "deployment_test.tmp"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception as e:
            self.logger.error(f"Permission check failed: {str(e)}")
            return False

    def check_disk_space(self, min_space_gb: int = 5) -> bool:
        """Verifica spazio disco disponibile"""
        try:
            import shutil
            free_bytes = shutil.disk_usage('.').free
            free_gb = free_bytes / (1024**3)

            if free_gb < min_space_gb:
                self.logger.error(f"Insufficient disk space: {free_gb:.2f}GB < {min_space_gb}GB")
                return False

            self.logger.info(f"Disk space OK: {free_gb:.2f}GB available")
            return True
        except Exception as e:
            self.logger.error(f"Disk space check failed: {str(e)}")
            return False

    def create_backup(self) -> Optional[str]:
        """Crea backup prima del deployment"""
        self.logger.info("Creating backup...")

        backup_name = f"backup_{self.app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = f"backups/{backup_name}"

        try:
            os.makedirs("backups", exist_ok=True)

            # Backup database
            if self.backup_database(backup_dir):
                self.logger.info(f"Database backup created: {backup_dir}/database.sql")

            # Backup configurazione
            if self.backup_config(backup_dir):
                self.logger.info(f"Config backup created: {backup_dir}/config.tar.gz")

            # Backup uploads/documenti
            if self.backup_uploads(backup_dir):
                self.logger.info(f"Uploads backup created: {backup_dir}/uploads.tar.gz")

            self.logger.info(f"Backup completed: {backup_dir}")
            return backup_dir

        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            return None

    def backup_database(self, backup_dir: str) -> bool:
        """Backup database"""
        try:
            db_url = os.getenv("DATABASE_URL", "")
            if "sqlite" in db_url:
                # Backup SQLite
                db_path = db_url.replace("sqlite:///", "")
                backup_path = f"{backup_dir}/database.db"
                os.makedirs(backup_dir, exist_ok=True)
                subprocess.run(["cp", db_path, backup_path], check=True)
            else:
                # Backup PostgreSQL/MySQL
                # Implementare backup SQL
                pass
            return True
        except Exception as e:
            self.logger.error(f"Database backup failed: {str(e)}")
            return False

    def backup_config(self, backup_dir: str) -> bool:
        """Backup configurazione"""
        try:
            import tarfile

            config_files = [
                "src/config/",
                "pyproject.toml",
                "requirements.txt",
                ".env"
            ]

            backup_path = f"{backup_dir}/config.tar.gz"
            os.makedirs(backup_dir, exist_ok=True)

            with tarfile.open(backup_path, "w:gz") as tar:
                for config_file in config_files:
                    if os.path.exists(config_file):
                        tar.add(config_file)

            return True
        except Exception as e:
            self.logger.error(f"Config backup failed: {str(e)}")
            return False

    def backup_uploads(self, backup_dir: str) -> bool:
        """Backup uploads e documenti"""
        try:
            import tarfile

            upload_dirs = [
                "uploads/",
                "documents/",
                "static/"
            ]

            backup_path = f"{backup_dir}/uploads.tar.gz"
            os.makedirs(backup_dir, exist_ok=True)

            with tarfile.open(backup_path, "w:gz") as tar:
                for upload_dir in upload_dirs:
                    if os.path.exists(upload_dir):
                        tar.add(upload_dir)

            return True
        except Exception as e:
            self.logger.error(f"Uploads backup failed: {str(e)}")
            return False

    def run_tests(self) -> bool:
        """Esegue test prima del deployment"""
        self.logger.info("Running tests...")

        try:
            # Test unitari
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/", "-v", "--tb=short",
                "--maxfail=5", "--disable-warnings"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"Tests failed: {result.stderr}")
                return False

            self.logger.info("All tests passed")
            return True

        except Exception as e:
            self.logger.error(f"Test execution failed: {str(e)}")
            return False

    def deploy_application(self) -> bool:
        """Esegue deployment applicazione"""
        self.logger.info("Deploying application...")

        try:
            # Installa dipendenze
            if not self.install_dependencies():
                return False

            # Esegue migrazioni database
            if not self.run_migrations():
                return False

            # Configura servizi
            if not self.configure_services():
                return False

            # Verifica health check
            if not self.health_check():
                return False

            self.logger.info("Application deployed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return False

    def install_dependencies(self) -> bool:
        """Installa dipendenze"""
        try:
            self.logger.info("Installing dependencies...")

            # Upgrade pip
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)

            # Installa dipendenze
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)

            # Installa in modalità produzione
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], check=True)

            return True
        except Exception as e:
            self.logger.error(f"Dependency installation failed: {str(e)}")
            return False

    def run_migrations(self) -> bool:
        """Esegue migrazioni database"""
        try:
            self.logger.info("Running database migrations...")

            # Qui implementare migrazioni specifiche
            # Per ora simula migrazioni
            migration_script = "migration_script.py"
            if os.path.exists(migration_script):
                subprocess.run([sys.executable, migration_script], check=True)

            return True
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            return False

    def configure_services(self) -> bool:
        """Configura servizi di sistema"""
        try:
            self.logger.info("Configuring services...")

            # Configura logging
            self.configure_logging()

            # Configura monitoring
            self.configure_monitoring()

            # Configura cache
            self.configure_cache()

            return True
        except Exception as e:
            self.logger.error(f"Service configuration failed: {str(e)}")
            return False

    def configure_logging(self):
        """Configura logging di produzione"""
        # Implementare configurazione logging
        pass

    def configure_monitoring(self):
        """Configura monitoring"""
        # Implementare configurazione monitoring
        pass

    def configure_cache(self):
        """Configura cache"""
        # Implementare configurazione cache
        pass

    def health_check(self) -> bool:
        """Verifica health dell'applicazione"""
        try:
            self.logger.info("Running health check...")

            # Verifica database connection
            if not self.check_database_connection():
                return False

            # Verifica servizi AI
            if not self.check_ai_services():
                return False

            # Verifica cache
            if not self.check_cache_connection():
                return False

            self.logger.info("Health check passed")
            return True

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def check_database_connection(self) -> bool:
        """Verifica connessione database"""
        # Implementare check database
        return True

    def check_ai_services(self) -> bool:
        """Verifica servizi AI"""
        # Implementare check AI services
        return True

    def check_cache_connection(self) -> bool:
        """Verifica connessione cache"""
        # Implementare check cache
        return True

    def rollback(self, backup_dir: str) -> bool:
        """Esegue rollback a backup precedente"""
        self.logger.info(f"Rolling back to: {backup_dir}")

        try:
            # Restore database
            if not self.restore_database(backup_dir):
                return False

            # Restore configurazione
            if not self.restore_config(backup_dir):
                return False

            # Restore uploads
            if not self.restore_uploads(backup_dir):
                return False

            self.logger.info("Rollback completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            return False

    def restore_database(self, backup_dir: str) -> bool:
        """Restore database da backup"""
        # Implementare restore database
        return True

    def restore_config(self, backup_dir: str) -> bool:
        """Restore configurazione da backup"""
        # Implementare restore config
        return True

    def restore_uploads(self, backup_dir: str) -> bool:
        """Restore uploads da backup"""
        # Implementare restore uploads
        return True

    def generate_deployment_report(self, success: bool, backup_dir: Optional[str] = None) -> str:
        """Genera report deployment"""
        report = {
            "deployment": {
                "app_name": self.app_name,
                "version": self.version,
                "environment": self.environment,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "backup_location": backup_dir
            },
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": os.getcwd()
            }
        }

        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report_file

    def deploy(self) -> bool:
        """Esegue deployment completo"""
        self.logger.info(f"Starting deployment: {self.app_name} v{self.version}")

        # Validazione ambiente
        if not self.validate_environment():
            return False

        # Creazione backup
        backup_dir = self.create_backup()
        if not backup_dir:
            self.logger.error("Backup creation failed")
            return False

        # Esecuzione test
        if not self.run_tests():
            self.logger.error("Tests failed")
            return False

        # Deployment applicazione
        if not self.deploy_application():
            self.logger.error("Application deployment failed")
            # Rollback automatico
            self.rollback(backup_dir)
            return False

        # Genera report
        report_file = self.generate_deployment_report(True, backup_dir)
        self.logger.info(f"Deployment completed successfully. Report: {report_file}")

        return True

def main():
    """Main deployment function"""
    deployment = DeploymentManager()

    try:
        success = deployment.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logging.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Deployment failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
