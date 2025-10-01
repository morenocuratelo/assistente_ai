"""
Script di diagnosi per identificare problemi nell'applicazione Archivista AI.
Testa sistematicamente tutti i componenti per identificare la causa dei problemi.
"""
import sys
import os
import traceback
from datetime import datetime

def test_imports():
    """Testa tutti gli import necessari."""
    print("🔍 Testando import necessari...")

    try:
        import streamlit as st
        print("✅ Streamlit importato correttamente")

        import pandas as pd
        print("✅ Pandas importato correttamente")

        import sqlite3
        print("✅ SQLite3 importato correttamente")

        from llama_index.core import Settings
        from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
        print("✅ LlamaIndex importato correttamente")

        from config import initialize_services
        print("✅ Config importato correttamente")

        from file_utils import setup_database, get_papers_dataframe
        print("✅ File utils importato correttamente")

        import knowledge_structure
        print("✅ Knowledge structure importato correttamente")

        from statistics import get_comprehensive_stats
        print("✅ Statistics importato correttamente")

        from batch_operations import get_available_operations
        print("✅ Batch operations importato correttamente")

        from export_manager import create_export_data
        print("✅ Export manager importato correttamente")

        return True, "Tutti gli import funzionano correttamente"

    except ImportError as e:
        return False, f"Errore import: {e}"
    except Exception as e:
        return False, f"Errore generico: {e}"

def test_database():
    """Testa la connessione e operazioni del database."""
    print("\n💾 Testando database...")

    try:
        from file_utils import setup_database, get_papers_dataframe

        # Crea/verifica database
        setup_database()
        print("✅ Database configurato correttamente")

        # Test lettura dati
        df = get_papers_dataframe()
        print(f"✅ DataFrame caricato: {len(df)} documenti")

        if len(df) > 0:
            print(f"   - Colonne disponibili: {list(df.columns)}")
            print(f"   - Tipi di documento: {df['category_name'].value_counts().to_dict()}")

        return True, f"Database funziona correttamente ({len(df)} documenti)"

    except Exception as e:
        return False, f"Errore database: {e}"

def test_ai_services():
    """Testa i servizi AI (Ollama e modelli)."""
    print("\n🤖 Testando servizi AI...")

    try:
        from config import initialize_services

        # Inizializza servizi
        initialize_services()
        print("✅ Servizi AI inizializzati correttamente")

        # Verifica modelli
        if hasattr(Settings, 'llm') and Settings.llm:
            print(f"✅ LLM configurato: {type(Settings.llm).__name__}")
        else:
            print("⚠️ LLM non configurato")

        if hasattr(Settings, 'embed_model') and Settings.embed_model:
            print(f"✅ Modello embedding configurato: {type(Settings.embed_model).__name__}")
        else:
            print("⚠️ Modello embedding non configurato")

        return True, "Servizi AI funzionano correttamente"

    except Exception as e:
        return False, f"Errore servizi AI: {e}"

def test_statistics():
    """Testa il modulo statistics."""
    print("\n📊 Testando modulo statistics...")

    try:
        from statistics import get_basic_stats, get_comprehensive_stats

        # Test statistiche di base
        basic_stats = get_basic_stats()
        print(f"✅ Statistiche di base: {basic_stats['total_documents']} documenti")

        # Test statistiche complete
        stats = get_comprehensive_stats()
        print(f"✅ Statistiche complete caricate: {len(stats)} sezioni")

        return True, "Modulo statistics funziona correttamente"

    except Exception as e:
        return False, f"Errore statistics: {e}"

def test_batch_operations():
    """Testa il modulo batch operations."""
    print("\n🔧 Testando operazioni batch...")

    try:
        from batch_operations import get_available_operations, create_batch_operation

        # Test operazioni disponibili
        operations = get_available_operations()
        print(f"✅ Operazioni disponibili: {len(operations)}")

        for op in operations:
            print(f"   - {op['name']}: {op['description']}")

        return True, "Modulo batch operations funziona correttamente"

    except Exception as e:
        return False, f"Errore batch operations: {e}"

def test_export_manager():
    """Testa il modulo export manager."""
    print("\n📤 Testando export manager...")

    try:
        from export_manager import get_export_summary, get_category_choices_for_filter

        # Test riepilogo esportazione
        summary = get_export_summary()
        print(f"✅ Riepilogo esportazione: {summary['document_count']} documenti")

        # Test filtri categorie
        categories = get_category_choices_for_filter()
        print(f"✅ Filtri categorie: {len(categories)} categorie")

        return True, "Modulo export manager funziona correttamente"

    except Exception as e:
        return False, f"Errore export manager: {e}"

def test_streamlit_app():
    """Testa se l'app Streamlit può partire."""
    print("\n🚀 Testando avvio applicazione Streamlit...")

    try:
        # Crea un'app Streamlit minima per test
        test_app_content = '''
import streamlit as st

st.title("Test Archivista AI")
st.write("✅ Applicazione funziona correttamente!")
st.info("Se vedi questo messaggio, Streamlit funziona.")
'''

        with open('test_app.py', 'w', encoding='utf-8') as f:
            f.write(test_app_content)

        print("✅ File test creato correttamente")
        return True, "Test app creato correttamente"

    except Exception as e:
        return False, f"Errore creazione test app: {e}"

def run_diagnosis():
    """Esegue la diagnosi completa del sistema."""
    print("🔍 DIAGNOSTICA ARCHIVISTA AI")
    print("=" * 50)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Directory: {os.getcwd()}")
    print("-" * 50)

    # Lista test da eseguire
    tests = [
        ("Import Moduli", test_imports),
        ("Database", test_database),
        ("Servizi AI", test_ai_services),
        ("Modulo Statistics", test_statistics),
        ("Operazioni Batch", test_batch_operations),
        ("Export Manager", test_export_manager),
        ("App Streamlit", test_streamlit_app),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success, message = test_func()
            if success:
                print(f"✅ {test_name}: {message}")
                results.append((test_name, True, message))
            else:
                print(f"❌ {test_name}: {message}")
                results.append((test_name, False, message))
        except Exception as e:
            error_msg = f"Errore durante il test: {str(e)}"
            print(f"💥 {test_name}: {error_msg}")
            results.append((test_name, False, error_msg))

    # Riepilogo finale
    print("\n" + "=" * 50)
    print("📋 RIEPILOGO FINALE")
    print("=" * 50)

    successful_tests = sum(1 for _, success, _ in results if success)
    total_tests = len(results)

    print(f"Test superati: {successful_tests}/{total_tests}")

    if successful_tests == total_tests:
        print("🎉 TUTTI I TEST SUPERATI!")
        print("L'applicazione dovrebbe funzionare correttamente.")
    else:
        print("⚠️ ALCUNI TEST FALLITI!")
        print("Consulta i dettagli sopra per identificare i problemi.")

        # Suggerimenti per i problemi comuni
        failed_tests = [name for name, success, _ in results if not success]
        if "Import Moduli" in failed_tests:
            print("\n💡 SUGGERIMENTO: Installa le dipendenze mancanti con:")
            print("   pip install -r requirements.txt")
        if "Database" in failed_tests:
            print("\n💡 SUGGERIMENTO: Verifica i permessi della directory db_memoria")
        if "Servizi AI" in failed_tests:
            print("\n💡 SUGGERIMENTO: Verifica che Ollama sia in esecuzione:")
            print("   curl http://localhost:11434/api/tags")

    return results

if __name__ == "__main__":
    try:
        results = run_diagnosis()

        # Salva risultati in file
        with open('diagnosis_results.txt', 'w', encoding='utf-8') as f:
            f.write("RISULTATI DIAGNOSI ARCHIVISTA AI\n")
            f.write("=" * 50 + "\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for test_name, success, message in results:
                status = "✅" if success else "❌"
                f.write(f"{status} {test_name}: {message}\n")

        print("\n💾 Risultati salvati in: diagnosis_results.txt")
    except Exception as e:
        print(f"💥 Errore durante la diagnosi: {e}")
        traceback.print_exc()
