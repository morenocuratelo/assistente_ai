# Esempio Utilizzo Sistema Progetti - Post Fase 1
"""
Esempio pratico utilizzo sistema multi-progetto dopo migrazione.

Questo script dimostra:
1. Creazione progetti separati
2. Switch contesto progetto
3. Operazioni progetto-aware
4. Gestione permessi progetto
5. Export/import progetti
"""

import os
import sys
import logging
from pathlib import Path

# Aggiungi path per import
sys.path.append(str(Path(__file__).parent))

from dal.project_service import ProjectService
from dal.project_repository import ProjectRepository
from dal.document_repository import DocumentRepository
from config_layer.project_config import ProjectConfig
from context.execution_context import ExecutionContext

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def esempio_creazione_progetti():
    """Esempio creazione progetti separati"""
    print("🏗️ ESEMPIO: Creazione Progetti")
    print("=" * 50)

    # Crea service progetti
    project_service = ProjectService()

    # Crea progetto università
    print("📚 Creazione progetto Università...")
    university_result = project_service.create_project_with_validation(
        project_id="universita",
        user_id=1,
        name="Università",
        description="Documenti e materiali accademici"
    )

    if university_result['success']:
        print(f"✅ Progetto Università creato: {university_result['project_id']}")
        print(f"   Database: {university_result['database_created']}")
        print(f"   Config: {university_result['config_created']}")
    else:
        print(f"❌ Errore creazione progetto Università: {university_result.get('message')}")

    # Crea progetto lavoro
    print("\\n💼 Creazione progetto Lavoro...")
    work_result = project_service.create_project_with_validation(
        project_id="lavoro",
        user_id=1,
        name="Lavoro",
        description="Documenti professionali e progetti lavorativi"
    )

    if work_result['success']:
        print(f"✅ Progetto Lavoro creato: {work_result['project_id']}")
    else:
        print(f"❌ Errore creazione progetto Lavoro: {work_result.get('message')}")

    print()

def esempio_switch_progetto():
    """Esempio cambio contesto progetto"""
    print("🔄 ESEMPIO: Switch Progetto")
    print("=" * 50)

    project_service = ProjectService()

    # Mostra progetti disponibili
    projects = project_service.get_user_projects_with_stats(1)
    print(f"📋 Progetti disponibili: {len(projects)}")

    for project in projects:
        print(f"   • {project['name']} ({project['id']}) - {project['stats']['total_items']} elementi")

    # Switch a progetto università
    print("\\n🔄 Cambio a progetto Università...")
    switch_result = project_service.switch_user_project(1, "universita")

    if switch_result['success']:
        print(f"✅ Progetto attivo cambiato: {switch_result['new_project_id']}")
    else:
        print(f"❌ Errore cambio progetto: {switch_result.get('message')}")

    print()

def esempio_operazioni_progetto_aware():
    """Esempio operazioni progetto-aware"""
    print("🎯 ESEMPIO: Operazioni Progetto-Aware")
    print("=" * 50)

    # Crea contesto progetto specifico
    context = ExecutionContext(project_id="universita", user_id=1)

    if context.initialize():
        print("✅ Contesto progetto inizializzato")

        # Ottieni repository con contesto progetto
        doc_repo = context.get_repository('document')

        if doc_repo:
            print("✅ Repository documenti progetto-aware disponibile")

            # Esempio operazioni documenti nel contesto progetto
            print("\\n📄 Operazioni documenti progetto Università:")

            # Trova documenti progetto specifico
            try:
                # Nota: Questo funzionerebbe dopo migrazione completa
                project_docs = doc_repo.find_by_criteria({'project_id': 'universita'})
                print(f"   Documenti progetto: {len(project_docs)}")

            except Exception as e:
                print(f"   Nota: {e} (atteso prima migrazione)")

        # Cleanup contesto
        context.cleanup()
    else:
        print("❌ Errore inizializzazione contesto progetto")

    print()

def esempio_gestione_permessi():
    """Esempio gestione permessi progetto"""
    print("🔐 ESEMPIO: Gestione Permessi Progetto")
    print("=" * 50)

    repo = ProjectRepository()

    # Verifica permessi utente in progetto
    permissions = repo.get_user_permissions_in_project(1, "universita")

    print(f"Permessi utente 1 in progetto universita:")
    print(f"   Accesso: {permissions['has_access']}")
    print(f"   Ruolo: {permissions['role']}")

    if permissions['permissions']:
        print("   Permessi dettagliati:")
        for perm, value in permissions['permissions'].items():
            status = "✅" if value else "❌"
            print(f"     {status} {perm}")

    print()

def esempio_configurazione_progetto():
    """Esempio configurazione progetto"""
    print("⚙️ ESEMPIO: Configurazione Progetto")
    print("=" * 50)

    # Carica configurazione progetto accademico
    project_config = ProjectConfig("universita")

    # Mostra configurazione corrente
    summary = project_config.get_config_summary()
    print("Configurazione progetto Università:")
    print(f"   Nome: {summary['project_name']}")
    print(f"   Features: {', '.join(summary['features_enabled'])}")
    print(f"   AI Provider: {summary['ai_provider']}")
    print(f"   Database: {summary['database_enabled']}")

    # Validazione configurazione
    validation = project_config.validate_config()
    print(f"\\nConfigurazione valida: {validation['valid']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings']}")

    print()

def esempio_dashboard_progetto():
    """Esempio dashboard progetto specifico"""
    print("📊 ESEMPIO: Dashboard Progetto")
    print("=" * 50)

    project_service = ProjectService()

    try:
        # Ottieni dati dashboard progetto università
        dashboard_data = project_service.get_project_dashboard_data("universita", 1)

        if dashboard_data:
            print("Dashboard Progetto Università:")
            print(f"   Progetto: {dashboard_data['project_info']['name']}")
            print(f"   Documenti: {dashboard_data['stats']['documents_count']}")
            print(f"   Corsi: {dashboard_data['stats']['courses_count']}")
            print(f"   Attività: {dashboard_data['stats']['tasks_count']}")

            # Documenti recenti
            recent_docs = dashboard_data['recent_documents']
            print(f"\\n   Documenti recenti: {len(recent_docs)}")

            # Permessi utente
            permissions = dashboard_data['user_permissions']
            print(f"\\n   Permessi utente: {permissions['role']}")

        else:
            print("❌ Errore caricamento dati dashboard")

    except Exception as e:
        print(f"❌ Errore dashboard progetto: {e}")

    print()

def esempio_export_import_progetto():
    """Esempio export/import progetto"""
    print("📤📥 ESEMPIO: Export/Import Progetto")
    print("=" * 50)

    project_service = ProjectService()

    try:
        # Prepara dati per export
        export_data = project_service.get_project_export_data("universita", 1)

        if export_data:
            print("Dati progetto preparati per export:")
            print(f"   Progetto: {export_data['project_info']['name']}")
            print(f"   Documenti: {export_data['metadata']['total_documents']}")
            print(f"   Corsi: {export_data['metadata']['total_courses']}")
            print(f"   Data export: {export_data['export_date']}")

            # Qui potresti salvare su file JSON
            print("\\n💾 Dati pronti per salvataggio su file")

        else:
            print("❌ Errore preparazione export")

    except Exception as e:
        print(f"❌ Errore export progetto: {e}")

    print()

def esempio_workflow_completo():
    """Esempio workflow completo multi-progetto"""
    print("🔄 ESEMPIO: Workflow Completo Multi-Progetto")
    print("=" * 50)

    project_service = ProjectService()

    try:
        print("1️⃣ Creazione progetti...")

        # Crea progetto personale
        personal_result = project_service.create_project_with_validation(
            "personale", 1, "Archivio Personale",
            "Documenti personali e privati"
        )

        if personal_result['success']:
            print(f"   ✅ Progetto Personale creato: {personal_result['project_id']}")

        print("\\n2️⃣ Switch tra progetti...")

        # Switch progetti
        projects = ["wiki_globale", "universita", "lavoro", "personale"]

        for project_id in projects:
            try:
                switch_result = project_service.switch_user_project(1, project_id)
                if switch_result['success']:
                    print(f"   🔄 Switch a: {project_id}")
                else:
                    print(f"   ❌ Errore switch a: {project_id}")
            except:
                print(f"   ⚠️ Progetto non disponibile: {project_id}")

        print("\\n3️⃣ Operazioni progetto-aware...")

        # Crea contesto per progetto specifico
        context = ExecutionContext(project_id="universita", user_id=1)
        context.initialize()

        print("   ✅ Contesto progetto Università attivo")
        print(f"   📊 Servizi disponibili: {len(context._services)}")
        print(f"   🗂️ Repository disponibili: {len(context._repositories)}")

        # Cleanup
        context.cleanup()

        print("\\n4️⃣ Statistiche finali...")

        # Mostra tutti i progetti con stats
        all_projects = project_service.get_user_projects_with_stats(1)
        print(f"   📋 Totale progetti: {len(all_projects)}")

        for project in all_projects:
            stats = project.get('stats', {})
            print(f"   • {project['name']}: {stats.get('total_items', 0)} elementi")

    except Exception as e:
        print(f"❌ Errore workflow completo: {e}")

    print()

def main():
    """Funzione principale esempi post-migrazione"""
    print("🚀 SISTEMA PROGETTI - ESEMPI UTILIZZO POST-MIGRAZIONE")
    print("=" * 70)
    print("Dimostrazione utilizzo sistema multi-progetto dopo migrazione 001")
    print()

    # Crea directory logs se necessario
    os.makedirs('database_layer/logs', exist_ok=True)

    # Esegui esempi
    esempio_creazione_progetti()
    esempio_switch_progetto()
    esempio_operazioni_progetto_aware()
    esempio_gestione_permessi()
    esempio_configurazione_progetto()
    esempio_dashboard_progetto()
    esempio_export_import_progetto()
    esempio_workflow_completo()

    print("✅ ESEMPI POST-MIGRAZIONE COMPLETATI")
    print("=" * 70)
    print()
    print("🎯 Sistema Progetti Pronto!")
    print()
    print("📋 Prossimi step operativi:")
    print("1. Eseguire migrazione 001 su database produzione")
    print("2. Testare UI gestione progetti (pages/0_Projects.py)")
    print("3. Integrare project switcher nelle pagine esistenti")
    print("4. Validare operazioni progetto-aware")
    print("5. Ottimizzare performance multi-progetto")

if __name__ == "__main__":
    main()
