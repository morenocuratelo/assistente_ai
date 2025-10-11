# Database Configuration - Configurazione centralizzata database
"""
Sistema configurazione unificato per percorsi e parametri database.

Risolve i problemi di configurazione hardcoded identificati nell'analisi:
- Percorsi DB sparsi in file_utils.py e main.py
- Nessun supporto multi-progetto
- Configurazione non environment-aware
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger('DatabaseConfig')

class DatabaseConfig:
    """
    Configurazione centralizzata per database SQLite.

    Fornisce:
    - Percorsi dinamici basati su progetto
    - Configurazione environment-aware
    - Supporto multi-database
    - Validazione percorsi
    """

    def __init__(self, project_id: str = None, environment: str = None):
        """
        Inizializza configurazione database.

        Args:
            project_id: ID progetto per database separato
            environment: Environment (dev, test, prod)
        """
        self.project_id = project_id
        self.environment = environment or self._detect_environment()

        # Configurazione base
        self.base_dir = Path("db_memoria")
        self.default_db_name = "metadata.sqlite"

        # Configurazione environment-specific
        self.env_configs = {
            'development': {
                'base_dir': 'db_memoria',
                'default_db_name': 'metadata_dev.sqlite',
                'create_dirs': True,
                'enable_logging': True
            },
            'testing': {
                'base_dir': 'test_db',
                'default_db_name': 'test_metadata.sqlite',
                'create_dirs': True,
                'enable_logging': False
            },
            'production': {
                'base_dir': 'db_memoria',
                'default_db_name': 'metadata.sqlite',
                'create_dirs': True,
                'enable_logging': True
            }
        }

        logger.info(f"DatabaseConfig inizializzato - Progetto: {project_id}, Environment: {self.environment}")

    def _detect_environment(self) -> str:
        """Rileva environment da variabili ambiente o default"""
        env = os.getenv('ARCHIVISTA_ENV', 'development')

        # Controlla se siamo in test
        if 'pytest' in os.getenv('_', ''):
            return 'testing'

        return env

    def get_database_path(self, db_name: str = None) -> Path:
        """
        Restituisce percorso completo database.

        Args:
            db_name: Nome specifico database

        Returns:
            Percorso completo database
        """
        if db_name is None:
            db_name = self.get_database_name()

        # Costruisci percorso
        if self.project_id:
            # Database per progetto specifico
            db_path = self.base_dir / f"project_{self.project_id}" / db_name
        else:
            # Database globale
            db_path = self.base_dir / db_name

        return db_path

    def get_database_name(self) -> str:
        """Restituisce nome database basato su progetto e environment"""
        env_config = self.env_configs.get(self.environment, {})

        if self.project_id:
            # Database specifico progetto
            base_name = env_config.get('default_db_name', self.default_db_name)
            # Inserisci project_id nel nome
            name_parts = base_name.split('.')
            project_db_name = f"{name_parts[0]}_project_{self.project_id}.{name_parts[1] if len(name_parts) > 1 else 'sqlite'}"
            return project_db_name
        else:
            # Database globale
            return env_config.get('default_db_name', self.default_db_name)

    def get_base_directory(self) -> Path:
        """Restituisce directory base database"""
        env_config = self.env_configs.get(self.environment, {})
        base_dir = env_config.get('base_dir', 'db_memoria')
        return Path(base_dir)

    def ensure_directories_exist(self) -> bool:
        """
        Crea directory necessarie se non esistono.

        Returns:
            True se create con successo
        """
        try:
            env_config = self.env_configs.get(self.environment, {})
            if not env_config.get('create_dirs', True):
                logger.debug("Creazione directory disabilitata per environment")
                return True

            # Crea directory base
            base_dir = self.get_base_directory()
            base_dir.mkdir(parents=True, exist_ok=True)

            # Crea directory progetto se necessario
            if self.project_id:
                project_dir = base_dir / f"project_{self.project_id}"
                project_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Directory database create: {base_dir}")
            return True

        except Exception as e:
            logger.error(f"Errore creazione directory database: {e}")
            return False

    def get_connection_params(self) -> Dict[str, Any]:
        """
        Restituisce parametri connessione ottimizzati.

        Returns:
            Dizionario parametri connessione
        """
        params = {
            'timeout': 20.0,
            'isolation_level': None,  # Autocommit mode
            'check_same_thread': False  # Per Streamlit
        }

        # Parametri environment-specific
        if self.environment == 'testing':
            params.update({
                'timeout': 5.0,
                'check_same_thread': True
            })

        return params

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida configurazione corrente.

        Returns:
            Report validazione
        """
        report = {
            'valid': True,
            'issues': [],
            'warnings': []
        }

        try:
            # Verifica percorsi
            db_path = self.get_database_path()
            base_dir = self.get_base_directory()

            if not base_dir.exists():
                if not self.ensure_directories_exist():
                    report['issues'].append(f"Impossibile creare directory: {base_dir}")
                    report['valid'] = False

            # Verifica permessi
            try:
                test_file = db_path.parent / '.test_write'
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                report['issues'].append(f"Permessi insufficienti per directory: {db_path.parent}")
                report['valid'] = False

            # Warning per percorsi relativi
            if not os.path.isabs(db_path):
                report['warnings'].append("Uso percorsi relativi - verificare working directory")

            # Warning per environment sviluppo
            if self.environment == 'development':
                report['warnings'].append("Environment sviluppo - ottimizzazioni disabilitate")

        except Exception as e:
            report['issues'].append(f"Errore validazione configurazione: {e}")
            report['valid'] = False

        return report

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Restituisce riepilogo configurazione.

        Returns:
            Dizionario riepilogo configurazione
        """
        return {
            'project_id': self.project_id,
            'environment': self.environment,
            'database_path': str(self.get_database_path()),
            'base_directory': str(self.get_base_directory()),
            'connection_params': self.get_connection_params(),
            'validation_report': self.validate_configuration()
        }

    def create_project_database(self, project_id: str) -> bool:
        """
        Crea nuovo database per progetto.

        Args:
            project_id: ID progetto

        Returns:
            True se creato con successo
        """
        try:
            # Crea configurazione per progetto
            project_config = DatabaseConfig(project_id=project_id, environment=self.environment)

            # Crea directory
            if not project_config.ensure_directories_exist():
                return False

            # Crea file database vuoto (SQLite si crea automaticamente)
            db_path = project_config.get_database_path()
            if not db_path.exists():
                # Crea connessione per inizializzare database
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                conn.close()

            logger.info(f"Database progetto creato: {project_id} -> {db_path}")
            return True

        except Exception as e:
            logger.error(f"Errore creazione database progetto {project_id}: {e}")
            return False

    def list_project_databases(self) -> List[str]:
        """
        Lista database progetti esistenti.

        Returns:
            Lista ID progetti con database
        """
        try:
            base_dir = self.get_base_directory()
            project_databases = []

            if base_dir.exists():
                for item in base_dir.iterdir():
                    if item.is_dir() and item.name.startswith('project_'):
                        project_id = item.name.replace('project_', '')
                        project_databases.append(project_id)

            return sorted(project_databases)

        except Exception as e:
            logger.error(f"Errore lista database progetti: {e}")
            return []

    def get_database_size(self) -> Dict[str, int]:
        """
        Restituisce dimensione database.

        Returns:
            Dizionario dimensioni in bytes
        """
        try:
            db_path = self.get_database_path()

            if db_path.exists():
                size = db_path.stat().st_size
                return {'database_size': size}
            else:
                return {'database_size': 0}

        except Exception as e:
            logger.error(f"Errore calcolo dimensione database: {e}")
            return {'database_size': 0}

    def backup_database(self, backup_dir: str = None) -> Optional[str]:
        """
        Crea backup database.

        Args:
            backup_dir: Directory backup (default: db_memoria/backups)

        Returns:
            Percorso backup creato o None se errore
        """
        try:
            if backup_dir is None:
                backup_dir = self.base_dir / "backups"

            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Crea nome backup
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}_{self.get_database_name()}"

            if self.project_id:
                backup_name = f"backup_{timestamp}_project_{self.project_id}.sqlite"
            else:
                backup_name = f"backup_{timestamp}_global.sqlite"

            backup_path = backup_dir / backup_name
            db_path = self.get_database_path()

            if db_path.exists():
                import shutil
                shutil.copy2(db_path, backup_path)
                logger.info(f"Backup creato: {backup_path}")
                return str(backup_path)
            else:
                logger.warning(f"Database non trovato per backup: {db_path}")
                return None

        except Exception as e:
            logger.error(f"Errore creazione backup: {e}")
            return None

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Rimuove backup vecchi.

        Args:
            keep_days: Giorni backup da mantenere

        Returns:
            Numero backup rimossi
        """
        try:
            backup_dir = self.base_dir / "backups"
            if not backup_dir.exists():
                return 0

            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            removed_count = 0
            for backup_file in backup_dir.glob("backup_*.sqlite"):
                file_modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_modified < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1

            if removed_count > 0:
                logger.info(f"Rimossi {removed_count} backup vecchi")

            return removed_count

        except Exception as e:
            logger.error(f"Errore pulizia backup: {e}")
            return 0

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Informazioni ambiente configurazione.

        Returns:
            Dizionario informazioni ambiente
        """
        return {
            'environment': self.environment,
            'project_id': self.project_id,
            'base_directory': str(self.get_base_directory()),
            'database_path': str(self.get_database_path()),
            'config_summary': self.get_config_summary(),
            'supported_environments': list(self.env_configs.keys()),
            'project_databases': self.list_project_databases()
        }
