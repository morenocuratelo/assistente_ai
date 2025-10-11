# Esempio Utilizzo Database Layer - Fase 0
"""
Esempio pratico di utilizzo del nuovo Database Layer.

Questo script dimostra come utilizzare i nuovi componenti:
- BaseRepository per operazioni CRUD sicure
- DocumentRepository per gestione documenti
- UserRepository per autenticazione sicura
- DatabaseConfig per configurazione centralizzata
- ExecutionContext per gestione stato applicazione
- ContextManager per operazioni monitorate
"""

import os
import sys
import logging
from pathlib import Path

# Aggiungi path per import
sys.path.append(str(Path(__file__).parent))

from dal.base_repository import BaseRepository
from dal.document_repository import DocumentRepository
from dal.user_repository import UserRepository
from config_layer.database_config import DatabaseConfig
from config_layer.project_config import ProjectConfig
from context.execution_context import ExecutionContext
from context.context_manager import ContextManager

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def esempio_configurazione_database():
    """Esempio configurazione database centralizzata"""
    print("🔧 ESEMPIO: Configurazione Database")
    print("=" * 50)

    # Crea configurazione globale
    global_config = DatabaseConfig()
    print(f"Database globale: {global_config.get_database_path()}")

    # Crea configurazione progetto specifico
    project_config = DatabaseConfig(project_id="progetto_accademico")
    print(f"Database progetto: {project_config.get_database_path()}")

    # Crea configurazione ambiente test
    test_config = DatabaseConfig(environment="testing")
    print(f"Database test: {test_config.get_database_path()}")

    # Validazione configurazione
    validation = global_config.validate_configuration()
    print(f"Configurazione valida: {validation['valid']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings']}")

    print()

def esempio_repository_pattern():
    """Esempio utilizzo repository pattern"""
    print("📋 ESEMPIO: Repository Pattern")
    print("=" * 50)

    # Crea configurazione database
    db_config = DatabaseConfig()

    # Crea repository documenti
    doc_repo = DocumentRepository(db_config.get_database_path())

    try:
        # Esempio operazioni documenti
        print("Operazioni documenti:")

        # Crea documento test
        test_doc = {
            'file_name': 'test_documento.txt',
            'title': 'Documento di Test',
            'authors': 'Autore Test',
            'publication_year': 2024,
            'category_id': 'TEST/CAT01',
            'category_name': 'Categoria Test'
        }

        # Nota: In ambiente reale creeremmo prima le tabelle
        print(f"Documento test: {test_doc}")

        # Esempio ricerca (se tabella esistesse)
        print("Ricerca documenti per categoria:")
        print(f"Query: SELECT * FROM papers WHERE category_id = ?")

        # Esempio operazioni sicure
        print("Operazioni con gestione errori:")
        print("- Validazione input automatica")
        print("- Logging strutturato operazioni")
        print("- Context manager per connessioni sicure")

    except Exception as e:
        print(f"Errore esempio repository: {e}")

    finally:
        doc_repo.close_connection()

    print()

def esempio_user_management():
    """Esempio gestione utenti sicura"""
    print("👤 ESEMPIO: Gestione Utenti Sicura")
    print("=" * 50)

    # Crea repository utenti
    db_config = DatabaseConfig()
    user_repo = UserRepository(db_config.get_database_path())

    try:
        print("Operazioni utenti:")

        # Esempio creazione utente sicuro
        print("Creazione utente con password hashing:")
        print("- Username validazione (min 3 caratteri)")
        print("- Password hashing automatico (bcrypt)")
        print("- Controllo unicità username")

        # Esempio autenticazione
        print("Autenticazione sicura:")
        print("- Verifica password con hash")
        print("- Logging tentativi accesso")
        print("- Gestione errori sicurezza")

        # Esempio operazioni avanzate
        print("Operazioni avanzate:")
        print("- Cambio password sicuro")
        print("- Marcatura utente non-nuovo")
        print("- Statistiche utente")

    except Exception as e:
        print(f"Errore esempio utenti: {e}")

    finally:
        user_repo.close_connection()

    print()

def esempio_context_manager():
    """Esempio utilizzo context manager"""
    print("⚡ ESEMPIO: Context Manager")
    print("=" * 50)

    # Crea context manager
    ctx_manager = ContextManager()

    # Esempio operazione semplice
    def operazione_test():
        return "Risultato operazione test"

    # Esegui operazione con monitoring
    result = ctx_manager.execute_with_context(
        "operazione_test",
        operazione_test
    )

    print(f"Operazione completata: {result.success}")
    print(f"Durata: {result.duration:.3f}s")
    print(f"Timestamp: {result.timestamp}")

    # Statistiche operazioni
    stats = ctx_manager.get_operation_stats()
    print(f"\\nStatistiche operazioni:")
    print(f"- Totali: {stats['total_operations']}")
    print(f"- Success rate: {stats['success_rate']}%")
    print(f"- Durata media: {stats['avg_duration']:.3f}s")

    print()

def esempio_execution_context():
    """Esempio utilizzo execution context"""
    print("🎯 ESEMPIO: Execution Context")
    print("=" * 50)

    # Crea contesto esecuzione
    context = ExecutionContext(project_id="demo_project", user_id=123)

    try:
        # Inizializza contesto
        if context.initialize():
            print("Contesto inizializzato con successo")

            # Mostra informazioni contesto
            info = context.get_context_info()
            print(f"\\nInformazioni contesto:")
            print(f"- Servizi: {info['services_count']}")
            print(f"- Repository: {info['repositories_count']}")
            print(f"- Stato applicazione: {info['application_state']['initialized']}")

            # Esempio operazione nel contesto
            def operazione_contesto():
                return f"Operazione eseguita per progetto {context.project_id}"

            result = context.execute_in_context(
                "demo_operation",
                operazione_contesto
            )

            print(f"\\nRisultato operazione: {result}")

            # Statistiche contesto
            app_state = context.app_state
            print(f"\\nStatistiche applicazione:")
            print(f"- Richieste: {app_state.request_count}")
            print(f"- Errori: {app_state.error_count}")
            print(f"- Uptime: {app_state.to_dict()['uptime_seconds']:.1f}s")

        else:
            print("Errore inizializzazione contesto")

    except Exception as e:
        print(f"Errore esempio contesto: {e}")

    finally:
        context.cleanup()

    print()

def esempio_project_config():
    """Esempio configurazione progetto"""
    print("🏗️ ESEMPIO: Configurazione Progetto")
    print("=" * 50)

    # Crea configurazione progetto da template
    project_config = ProjectConfig.create_from_template("progetto_demo", "academic")

    print("Configurazione progetto accademico:")
    summary = project_config.get_config_summary()
    print(f"- Nome: {summary['project_name']}")
    print(f"- Features: {', '.join(summary['features_enabled'])}")
    print(f"- AI Provider: {summary['ai_provider']}")

    # Validazione configurazione
    validation = project_config.validate_config()
    print(f"\\nConfigurazione valida: {validation['valid']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings']}")

    # Esporta configurazione
    config_json = project_config.export_config()
    print(f"\\nDimensione configurazione: {len(config_json)} caratteri")

    print()

def esempio_completo_workflow():
    """Esempio workflow completo con tutti i componenti"""
    print("🔄 ESEMPIO: Workflow Completo")
    print("=" * 50)

    try:
        # 1. Crea configurazione progetto
        project_config = ProjectConfig("workflow_demo")
        db_config = project_config.get_database_config()

        # 2. Crea contesto esecuzione
        context = ExecutionContext(project_id="workflow_demo")
        context.initialize()

        # 3. Crea context manager per monitoring
        ctx_manager = ContextManager()

        # 4. Crea repository con contesto
        doc_repo = DocumentRepository(db_config.get_database_path())

        print("Workflow componenti creato con successo!")
        print(f"- Progetto: {project_config.project_id}")
        print(f"- Database: {db_config.get_database_path()}")
        print(f"- Contesto: {context.app_state.initialized}")
        print(f"- Repository: {doc_repo._get_table_name()}")

        # 5. Esempio operazione complessa
        def operazione_workflow():
            # Simula operazione complessa
            return {
                'documenti_processati': 5,
                'utenti_creati': 2,
                'progetto_attivo': context.project_id
            }

        # Esegui operazione con monitoring completo
        result = ctx_manager.execute_with_context(
            "workflow_completo",
            operazione_workflow,
            context=context
        )

        if result.success:
            print(f"\\nWorkflow completato: {result.data}")
            print(f"Durata: {result.duration:.3f}s")

        # 6. Mostra report finale
        print("\\n📊 Report Finale:")
        stats = ctx_manager.get_operation_stats()
        print(f"- Operazioni totali: {stats['total_operations']}")
        print(f"- Success rate: {stats['success_rate']}%")

        # Cleanup
        doc_repo.close_connection()
        context.cleanup()

    except Exception as e:
        print(f"Errore workflow completo: {e}")

    print()

def main():
    """Funzione principale esempi"""
    print("🚀 DATABASE LAYER - ESEMPI UTILIZZO")
    print("=" * 60)
    print("Dimostrazione componenti Fase 0 per preparazione multi-progetto")
    print()

    # Verifica se directory logs esiste
    os.makedirs('database_layer/logs', exist_ok=True)

    # Esegui esempi
    esempio_configurazione_database()
    esempio_repository_pattern()
    esempio_user_management()
    esempio_context_manager()
    esempio_execution_context()
    esempio_project_config()
    esempio_completo_workflow()

    print("✅ ESEMPI COMPLETATI")
    print("=" * 60)
    print("Il Database Layer è pronto per l'integrazione!")
    print()
    print("📋 Prossimi step:")
    print("- Integrare componenti esistenti con nuovo DAL")
    print("- Sviluppare suite test completa")
    print("- Pianificare migrazione multi-progetto")
    print("- Documentare API per sviluppatori")

if __name__ == "__main__":
    main()
