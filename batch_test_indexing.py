#!/usr/bin/env python3
"""
Script per testare il processamento batch di tutti i file PDF
"""
import os
import sys
import time
import glob
from datetime import datetime

# Aggiungi il path corrente per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def batch_process_pdfs():
    """Processa tutti i PDF nella directory documenti_da_processare"""

    input_dir = "documenti_da_processare"
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))

    if not pdf_files:
        print(f"❌ Nessun file PDF trovato in: {input_dir}")
        return False

    print("🚀 BATCH PROCESSING - Test con tutti i file PDF")
    print("=" * 60)
    print(f"📋 Trovati {len(pdf_files)} file PDF da processare:")
    for pdf_file in pdf_files:
        print(f"  - {os.path.basename(pdf_file)}")

    results = {
        'success': [],
        'failed': [],
        'total_time': 0
    }

    start_time = time.time()

    for i, pdf_file in enumerate(pdf_files, 1):
        file_name = os.path.basename(pdf_file)
        print(f"\n🔄 [{i}/{len(pdf_files)}] Processamento: {file_name}")
        print("-" * 50)

        try:
            # Importa e esegui il processamento
            from archivista_processing import process_document_task

            file_start_time = time.time()
            result = process_document_task(pdf_file)
            file_end_time = time.time()

            file_time = file_end_time - file_start_time
            print(f"✅ SUCCESSO: {file_name} - Tempo: {file_time:.2f}s")

            # Verifica dove è stato archiviato
            categorized_dirs = ["Dall_Origine_alla_Complessita"]
            file_found = False
            for cat_dir in categorized_dirs:
                for root, dirs, files in os.walk(cat_dir):
                    if file_name in files:
                        print(f"   📁 Archiviato in: {os.path.relpath(os.path.join(root, file_name))}")
                        file_found = True
                        break
                if file_found:
                    break

            results['success'].append({
                'file': file_name,
                'time': file_time,
                'result': result
            })

        except Exception as e:
            file_end_time = time.time()
            file_time = file_end_time - file_start_time
            print(f"❌ FALLITO: {file_name} - Tempo: {file_time:.2f}s")
            print(f"   Errore: {e}")

            results['failed'].append({
                'file': file_name,
                'time': file_time,
                'error': str(e)
            })

    end_time = time.time()
    results['total_time'] = end_time - start_time

    # Report finale
    print(f"\n{'=' * 60}")
    print("📊 REPORT FINALE BATCH PROCESSING")
    print(f"{'=' * 60}")
    print(f"⏱️ Tempo totale: {results['total_time']:.2f} secondi")
    print(f"📈 Media per file: {results['total_time']/len(pdf_files):.2f} secondi")
    print(f"✅ Processati con successo: {len(results['success'])}/{len(pdf_files)}")
    print(f"❌ Falliti: {len(results['failed'])}/{len(pdf_files)}")

    if results['success']:
        print("\n📁 File processati con successo:")
        for success in results['success']:
            print(f"   ✅ {success['file']} ({success['time']:.2f}s) - Categoria: {success['result'].get('category', 'N/A')}")

    if results['failed']:
        print("\n❌ File falliti:")
        for failed in results['failed']:
            print(f"   ❌ {failed['file']} ({failed['time']:.2f}s) - Errore: {failed['error']}")

    # Calcola statistiche di performance
    if results['success']:
        avg_time = sum(s['time'] for s in results['success']) / len(results['success'])
        print(f"\n📈 PERFORMANCE:")
        print(f"   Tempo medio per file riuscito: {avg_time:.2f} secondi")
        print(f"   Throughput: {len(results['success'])/results['total_time']:.2f} file/secondo")

    return len(results['failed']) == 0

def cleanup_error_files():
    """Pulisce i file dalla directory errori se esistono"""

    error_dir = "documenti_da_processare/_error"
    if os.path.exists(error_dir):
        error_files = glob.glob(os.path.join(error_dir, "*"))
        if error_files:
            print(f"🧹 Pulizia directory errori: {len(error_files)} file")
            for file_path in error_files:
                try:
                    os.remove(file_path)
                    print(f"   Rimossa: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"   Errore rimozione {os.path.basename(file_path)}: {e}")

if __name__ == "__main__":
    print("🚀 AVVIO BATCH TEST INDICIZZAZIONE")
    print("=" * 60)

    # Pulisce eventuali file dalla directory errori
    cleanup_error_files()

    # Esegue il batch processing
    success = batch_process_pdfs()

    print(f"\n{'=' * 60}")
    if success:
        print("🎉 BATCH PROCESSING COMPLETATO CON SUCCESSO!")
        print("   Tutti i file sono stati processati correttamente.")
    else:
        print("⚠️ BATCH PROCESSING COMPLETATO CON ALCUNI ERRORI")
        print("   Verifica i log sopra per i dettagli.")

    print("=" * 60)
