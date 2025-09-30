#!/usr/bin/env python3
"""
Script per testare direttamente il processo di indicizzazione
senza dover utilizzare Celery worker
"""
import os
import sys
import shutil
from pathlib import Path

# Aggiungi il path corrente per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_single_file_indexing():
    """Test diretto del processo di indicizzazione su un singolo file"""

    # File di test
    test_file = "documenti_da_processare/attention-deficit-hyperactivity-disorder.pdf"

    if not os.path.exists(test_file):
        print(f"❌ File di test non trovato: {test_file}")
        return False

    print("🔬 TEST DIRETTO DEL PROCESSO DI INDICIZZAZIONE")
    print("=" * 60)
    print(f"📁 File di test: {test_file}")

    try:
        # Importa la funzione di processamento
        from archivista_processing import process_document_task

        print("🔧 Avvio processamento diretto...")

        # Esegui il processamento direttamente (senza Celery)
        result = process_document_task(test_file)

        print("✅ PROCESSAMENTO COMPLETATO CON SUCCESSO!")
        print(f"📊 Risultato: {result}")

        # Verifica se il file è stato spostato nella directory categorizzata
        file_name = os.path.basename(test_file)
        categorized_dirs = ["Dall_Origine_alla_Complessita"]

        file_found = False
        for cat_dir in categorized_dirs:
            for root, dirs, files in os.walk(cat_dir):
                if file_name in files:
                    print(f"✅ File trovato in: {os.path.join(root, file_name)}")
                    file_found = True
                    break
            if file_found:
                break

        if not file_found:
            print("⚠️ File non trovato nelle directory categorizzate")

        return True

    except Exception as e:
        print(f"❌ ERRORE DURANTE IL PROCESSAMENTO: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def test_error_handling():
    """Test della gestione errori"""

    print("\n🛡️ TEST GESTIONE ERRORI")
    print("=" * 40)

    # Crea un file di test vuoto per simulare un errore
    error_test_file = "documenti_da_processare/empty_test.txt"

    try:
        # Crea file vuoto
        with open(error_test_file, 'w') as f:
            f.write("")

        print(f"📝 Creato file di test vuoto: {error_test_file}")

        from archivista_processing import process_document_task

        try:
            result = process_document_task(error_test_file)
            print("⚠️ Il processamento del file vuoto non ha generato errore come previsto")
        except Exception as e:
            print(f"✅ Gestione errori funzionante: {e}")

        # Verifica se il file è stato spostato in _error
        error_file = f"documenti_da_processare/_error/{os.path.basename(error_test_file)}"
        if os.path.exists(error_file):
            print(f"✅ File vuoto correttamente spostato in: {error_file}")
            # Pulisci
            os.remove(error_file)
            print("🧹 File di test rimosso")
        else:
            print("⚠️ File vuoto non trovato nella directory errori")

    except Exception as e:
        print(f"❌ Errore nel test di gestione errori: {e}")

if __name__ == "__main__":
    print("🚀 AVVIO TEST DEL PROCESSO DI INDICIZZAZIONE")
    print("=" * 60)

    # Test 1: Processamento normale
    success = test_single_file_indexing()

    # Test 2: Gestione errori
    test_error_handling()

    print("\n" + "=" * 60)
    if success:
        print("✅ TEST COMPLETATO - Il processo di indicizzazione funziona correttamente!")
    else:
        print("❌ TEST FALLITO - Ci sono ancora problemi da risolvere")

    print("=" * 60)
