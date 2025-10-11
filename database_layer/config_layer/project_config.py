# Project Configuration - Configurazione progetti
"""
Sistema configurazione per gestione progetti in Archivista AI.

Fornisce:
- Gestione configurazione progetto
- Impostazioni progetto specifiche
- Template configurazione progetto
- Validazione configurazione progetto
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from .database_config import DatabaseConfig

logger = logging.getLogger('ProjectConfig')

class ProjectConfig:
    """
    Configurazione progetto per Archivista AI.

    Gestisce impostazioni specifiche progetto e
    fornisce template per nuovi progetti.
    """

    def __init__(self, project_id: str, config_data: Dict[str, Any] = None):
        """
        Inizializza configurazione progetto.

        Args:
            project_id: ID univoco progetto
            config_data: Dati configurazione progetto
        """
        self.project_id = project_id
        self.config_data = config_data or {}

        # Template configurazione progetto
        self.default_config = {
            'project_info': {
                'id': project_id,
                'name': f"Progetto {project_id}",
                'description': '',
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            },
            'database': {
                'enabled': True,
                'auto_backup': True,
                'backup_frequency_days': 7,
                'retention_days': 30
            },
            'features': {
                'chat_enabled': True,
                'archive_enabled': True,
                'editor_enabled': True,
                'academic_enabled': True,
                'knowledge_graph_enabled': True,
                'ai_suggestions_enabled': True
            },
            'ai_settings': {
                'model_provider': 'ollama',  # ollama, openai
                'embedding_model': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
                'max_tokens': 4096,
                'temperature': 0.7
            },
            'ui_settings': {
                'theme': 'auto',
                'language': 'it',
                'items_per_page': 20,
                'enable_animations': True
            },
            'permissions': {
                'public_read': False,
                'public_write': False,
                'allow_guests': False,
                'require_authentication': True
            }
        }

        # Merge con configurazione fornita
        self._merge_config()

        logger.info(f"ProjectConfig inizializzato per progetto: {project_id}")

    def _merge_config(self):
        """Merge configurazione utente con template default"""
        def deep_merge(base: Dict, update: Dict) -> Dict:
            """Merge ricorsivo dizionari"""
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        self.config_data = deep_merge(self.default_config, self.config_data)

    def save_to_file(self, config_dir: str = None) -> bool:
        """
        Salva configurazione progetto su file.

        Args:
            config_dir: Directory configurazione

        Returns:
            True se salvato con successo
        """
        try:
            if config_dir is None:
                config_dir = f"db_memoria/project_{self.project_id}"

            config_path = Path(config_dir)
            config_path.mkdir(parents=True, exist_ok=True)

            config_file = config_path / "project_config.json"

            # Salva configurazione
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configurazione progetto salvata: {config_file}")
            return True

        except Exception as e:
            logger.error(f"Errore salvataggio configurazione progetto: {e}")
            return False

    def load_from_file(self, config_dir: str = None) -> bool:
        """
        Carica configurazione progetto da file.

        Args:
            config_dir: Directory configurazione

        Returns:
            True se caricata con successo
        """
        try:
            if config_dir is None:
                config_dir = f"db_memoria/project_{self.project_id}"

            config_file = Path(config_dir) / "project_config.json"

            if not config_file.exists():
                logger.warning(f"File configurazione progetto non trovato: {config_file}")
                return False

            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            self.config_data = loaded_config
            logger.info(f"Configurazione progetto caricata: {config_file}")
            return True

        except Exception as e:
            logger.error(f"Errore caricamento configurazione progetto: {e}")
            return False

    def get_project_info(self) -> Dict[str, Any]:
        """Restituisce informazioni progetto"""
        return self.config_data.get('project_info', {})

    def get_database_config(self) -> DatabaseConfig:
        """Restituisce configurazione database progetto"""
        return DatabaseConfig(project_id=self.project_id)

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Verifica se feature è abilitata.

        Args:
            feature: Nome feature da verificare

        Returns:
            True se feature abilitata
        """
        return self.config_data.get('features', {}).get(feature, False)

    def get_ai_settings(self) -> Dict[str, Any]:
        """Restituisce impostazioni AI progetto"""
        return self.config_data.get('ai_settings', {})

    def get_ui_settings(self) -> Dict[str, Any]:
        """Restituisce impostazioni UI progetto"""
        return self.config_data.get('ui_settings', {})

    def update_project_info(self, name: str = None, description: str = None) -> bool:
        """
        Aggiorna informazioni progetto.

        Args:
            name: Nome progetto
            description: Descrizione progetto

        Returns:
            True se aggiornato con successo
        """
        try:
            project_info = self.config_data['project_info']

            if name is not None:
                project_info['name'] = name

            if description is not None:
                project_info['description'] = description

            project_info['updated_at'] = datetime.now().isoformat()

            logger.info(f"Informazioni progetto aggiornate: {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore aggiornamento informazioni progetto: {e}")
            return False

    def enable_feature(self, feature: str) -> bool:
        """
        Abilita feature progetto.

        Args:
            feature: Nome feature da abilitare

        Returns:
            True se abilitata con successo
        """
        try:
            if 'features' not in self.config_data:
                self.config_data['features'] = {}

            self.config_data['features'][feature] = True

            logger.info(f"Feature abilitata: {feature} per progetto {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore abilitazione feature: {e}")
            return False

    def disable_feature(self, feature: str) -> bool:
        """
        Disabilita feature progetto.

        Args:
            feature: Nome feature da disabilitare

        Returns:
            True se disabilitata con successo
        """
        try:
            if 'features' not in self.config_data:
                self.config_data['features'] = {}

            self.config_data['features'][feature] = False

            logger.info(f"Feature disabilitata: {feature} per progetto {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore disabilitazione feature: {e}")
            return False

    def validate_config(self) -> Dict[str, Any]:
        """
        Valida configurazione progetto.

        Returns:
            Report validazione
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # Verifica struttura obbligatoria
            required_sections = ['project_info', 'features']
            for section in required_sections:
                if section not in self.config_data:
                    report['errors'].append(f"Sezione obbligatoria mancante: {section}")
                    report['valid'] = False

            # Verifica project_info
            project_info = self.config_data.get('project_info', {})
            if not project_info.get('id'):
                report['errors'].append("Project ID obbligatorio")
                report['valid'] = False

            if not project_info.get('name'):
                report['warnings'].append("Nome progetto vuoto")

            # Verifica features
            features = self.config_data.get('features', {})
            core_features = ['chat_enabled', 'archive_enabled']
            for feature in core_features:
                if feature not in features:
                    report['warnings'].append(f"Feature core non configurata: {feature}")

            # Verifica AI settings
            ai_settings = self.config_data.get('ai_settings', {})
            if not ai_settings.get('model_provider'):
                report['warnings'].append("Provider AI non specificato")

        except Exception as e:
            report['errors'].append(f"Errore validazione configurazione: {e}")
            report['valid'] = False

        return report

    def export_config(self) -> str:
        """
        Esporta configurazione come JSON string.

        Returns:
            Configurazione in formato JSON
        """
        try:
            return json.dumps(self.config_data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Errore esportazione configurazione: {e}")
            return "{}"

    def import_config(self, config_json: str) -> bool:
        """
        Importa configurazione da JSON string.

        Args:
            config_json: Configurazione in formato JSON

        Returns:
            True se importata con successo
        """
        try:
            imported_config = json.loads(config_json)

            # Validazione configurazione importata
            temp_config = ProjectConfig(self.project_id, imported_config)
            validation = temp_config.validate_config()

            if not validation['valid']:
                logger.error(f"Configurazione importata non valida: {validation['errors']}")
                return False

            self.config_data = imported_config
            logger.info(f"Configurazione progetto importata: {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore importazione configurazione: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Restituisce riepilogo configurazione progetto.

        Returns:
            Dizionario riepilogo configurazione
        """
        return {
            'project_id': self.project_id,
            'project_name': self.config_data['project_info'].get('name', ''),
            'features_enabled': [k for k, v in self.config_data.get('features', {}).items() if v],
            'ai_provider': self.config_data.get('ai_settings', {}).get('model_provider', 'unknown'),
            'database_enabled': self.config_data.get('database', {}).get('enabled', False),
            'validation_status': self.validate_config(),
            'config_size': len(json.dumps(self.config_data))
        }

    @classmethod
    def create_from_template(cls, project_id: str, template: str = 'default') -> 'ProjectConfig':
        """
        Crea configurazione progetto da template.

        Args:
            project_id: ID progetto
            template: Nome template

        Returns:
            ProjectConfig con template applicato
        """
        templates = {
            'default': {},
            'academic': {
                'project_info': {
                    'name': 'Progetto Accademico',
                    'description': 'Progetto per gestione documenti accademici'
                },
                'features': {
                    'academic_enabled': True,
                    'knowledge_graph_enabled': True
                }
            },
            'research': {
                'project_info': {
                    'name': 'Progetto Ricerca',
                    'description': 'Progetto per ricerca e analisi documenti'
                },
                'features': {
                    'knowledge_graph_enabled': True,
                    'ai_suggestions_enabled': True
                },
                'ai_settings': {
                    'temperature': 0.3  # Più deterministico per ricerca
                }
            },
            'personal': {
                'project_info': {
                    'name': 'Archivio Personale',
                    'description': 'Archivio documenti personali'
                },
                'permissions': {
                    'public_read': False,
                    'public_write': False,
                    'require_authentication': True
                }
            }
        }

        template_data = templates.get(template, {})
        return cls(project_id, template_data)

    def list_available_templates(self) -> List[str]:
        """
        Lista template disponibili.

        Returns:
            Lista nomi template
        """
        return ['default', 'academic', 'research', 'personal']

    def clone_from_project(self, source_project_id: str) -> bool:
        """
        Clona configurazione da altro progetto.

        Args:
            source_project_id: ID progetto sorgente

        Returns:
            True se clonata con successo
        """
        try:
            source_config = ProjectConfig(source_project_id)
            if source_config.load_from_file():
                # Modifica ID progetto
                self.config_data = source_config.config_data.copy()
                self.config_data['project_info']['id'] = self.project_id
                self.config_data['project_info']['name'] = f"Copia di {source_config.get_project_info().get('name', 'Progetto')}"

                logger.info(f"Configurazione clonata da {source_project_id} a {self.project_id}")
                return True
            else:
                logger.error(f"Impossibile caricare configurazione progetto sorgente: {source_project_id}")
                return False

        except Exception as e:
            logger.error(f"Errore clonazione configurazione: {e}")
            return False

    def reset_to_default(self) -> bool:
        """
        Ripristina configurazione di default.

        Returns:
            True se ripristinata con successo
        """
        try:
            self.config_data = self.default_config.copy()
            self.config_data['project_info']['id'] = self.project_id

            logger.info(f"Configurazione progetto ripristinata a default: {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore ripristino configurazione: {e}")
            return False

    def get_feature_flags(self) -> Dict[str, bool]:
        """
        Restituisce feature flags progetto.

        Returns:
            Dizionario feature flags
        """
        return self.config_data.get('features', {}).copy()

    def set_feature_flags(self, feature_flags: Dict[str, bool]) -> bool:
        """
        Imposta feature flags progetto.

        Args:
            feature_flags: Dizionario feature flags

        Returns:
            True se impostate con successo
        """
        try:
            if 'features' not in self.config_data:
                self.config_data['features'] = {}

            self.config_data['features'].update(feature_flags)

            logger.info(f"Feature flags aggiornate per progetto: {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore impostazione feature flags: {e}")
            return False
