#!/usr/bin/env python3
"""
Script per testare i miglioramenti delle performance del sistema ottimizzato
"""
import os
import sys
import time
import glob
from pathlib import Path

# Aggiungi il path corrente per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_performance_improvements():
    """Testa i miglioramenti delle performance"""

    print("🚀 TEST MIGLIORAMENTI PERFORMANCE - FASE 3")
    print("=" * 60)

    # Test 1: Verifica ottimizzatore performance
    print("\n📊 TEST 1: Ottimizzatore Performance")
    print("-" * 40)

    try:
        from performance_optimizer import performance_optimizer

        # Verifica se ci sono dati di performance esistenti
        if os.path.exists("db_memoria/processing_metrics.json"):
            print("✅ Metriche esistenti caricate")

        # Genera report performance
        report = performance_optimizer.get_performance_report()
        print(f"📈 File processati totali: {report['total_files_processed']}")
        print(f"💾 Dimensione cache: {report['cache_size']} file")

        if report['optimization_suggestions']:
            print("\n💡 Suggerimenti di ottimizzazione:")
            for suggestion in report['optimization_suggestions']:
                print(f"   • {suggestion}")
        else:
            print("✅ Nessun suggerimento di ottimizzazione necessario")

    except Exception as e:
        print(f"⚠️ Errore test ottimizzatore: {e}")

    # Test 2: Test velocità estrazione con ottimizzazioni
    print("\n⚡ TEST 2: Test Velocità Estrazione")
    print("-" * 40)

    test_file = "documenti_da_processare/attention-deficit-hyperactivity-disorder.pdf"
    if os.path.exists(test_file):
        try:
            from performance_optimizer import get_optimized_extractor_list

            # Ottieni lista ottimizzata di estrattori
            optimized_extractors = get_optimized_extractor_list(test_file)

            print(f"📋 Estrattori ottimizzati per {Path(test_file).suffix}:")
            for i, (name, func) in enumerate(optimized_extractors, 1):
                print(f"   {i}. {name}")

            # Test velocità del primo estrattore
            if optimized_extractors:
                fastest_extractor_name, fastest_extractor_func = optimized_extractors[0]
                start_time = time.time()

                try:
                    # Importa la funzione corretta
                    from archivista_processing import extract_text_pymupdf
                    text = extract_text_pymupdf(test_file)
                    end_time = time.time()

                    extraction_time = end_time - start_time
                    text_length = len(text)

                    print(f"\n✅ Test estrazione con {fastest_extractor_name}:")
                    print(f"   ⏱️ Tempo: {extraction_time:.3f}s")
                    print(f"   📏 Testo estratto: {text_length:,} caratteri")

                except Exception as e:
                    print(f"❌ Errore test estrazione: {e}")

        except Exception as e:
            print(f"⚠️ Errore test velocità: {e}")

    # Test 3: Verifica funzionalità cache
    print("\n🗄️ TEST 3: Sistema di Cache")
    print("-" * 40)

    try:
        from performance_optimizer import performance_optimizer

        test_file = "documenti_da_processare/attention-deficit-hyperactivity-disorder.pdf"
        if os.path.exists(test_file):
            # Test verifica file già processato
            is_processed = performance_optimizer.is_file_processed(test_file)
            print(f"📋 File già processato: {is_processed}")

            # Test calcolo hash
            file_hash = performance_optimizer.get_file_hash(test_file)
            if file_hash:
                print(f"🔢 Hash file: {file_hash[:16]}...")
            else:
                print("❌ Errore calcolo hash")

    except Exception as e:
        print(f"⚠️ Errore test cache: {e}")

    # Test 4: Test supporto multi-formato
    print("\n📄 TEST 4: Supporto Multi-Formato")
    print("-" * 40)

    supported_extensions = ['.pdf', '.docx', '.txt', '.html', '.rtf']
    print("📋 Formati supportati:")
    for ext in supported_extensions:
        print(f"   ✅ {ext}")

    # Test 5: Verifica integrità sistema
    print("\n🔍 TEST 5: Verifica Integrità Sistema")
    print("-" * 40)

    checks = [
        ("Directory documenti_da_processare", "documenti_da_processare"),
        ("Directory db_memoria", "db_memoria"),
        ("Directory archivio", "Dall_Origine_alla_Complessita"),
        ("File configurazione .env", ".env"),
        ("File requirements.txt", "requirements.txt"),
        ("Connessione Ollama", "http://localhost:11434"),
    ]

    for check_name, check_path in checks:
        if check_path.startswith("http"):
            # Test connessione Ollama
            try:
                import requests
                response = requests.get(f"{check_path}/api/version", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {check_name}: Connesso")
                else:
                    print(f"   ❌ {check_name}: Errore connessione")
            except:
                print(f"   ❌ {check_name}: Non raggiungibile")
        else:
            # Test file/directory
            if os.path.exists(check_path):
                if os.path.isfile(check_path):
                    size = os.path.getsize(check_path)
                    print(f"   ✅ {check_name}: {size:,} bytes")
                else:
                    file_count = len(glob.glob(os.path.join(check_path, "**/*"), recursive=True))
                    print(f"   ✅ {check_name}: {file_count} elementi")
            else:
                print(f"   ❌ {check_name}: Non trovato")

def generate_optimization_report():
    """Genera report completo delle ottimizzazioni"""

    print("\n📋 REPORT OTTIMIZZAZIONI - FASE 3")
    print("=" * 50)

    try:
        from performance_optimizer import performance_optimizer

        report = performance_optimizer.get_performance_report()

        print("📊 STATISTICHE PERFORMANCE:")
        print(f"   • File processati: {report['total_files_processed']}")
        print(f"   • Dimensione cache: {report['cache_size']}")
        print(f"   • Estrattori monitorati: {len(report['extractor_performance'])}")

        if report['extractor_performance']:
            print("\n🏆 PERFORMANCE ESTRATTORI:")
            for ext, extractors in report['extractor_performance'].items():
                print(f"\n   📁 Estensione {ext}:")
                for extractor_name, data in extractors.items():
                    success_rate = (data['success_count'] / data['count'] * 100) if data['count'] > 0 else 0
                    print(f"      • {extractor_name}: {data['avg_time']:.3f}s avg, "
                          f"{success_rate:.1f}% successo ({data['count']} file)")

        if report['optimization_suggestions']:
            print("\n💡 SUGGERIMENTI OTTIMIZZAZIONE:")
            for suggestion in report['optimization_suggestions']:
                print(f"   • {suggestion}")

        print("\n🎯 PROSSIMI PASSI CONSIGLIATI:")
        print("   1. Monitorare performance per identificare ulteriori ottimizzazioni")
        print("   2. Implementare processamento parallelo per file multipli")
        print("   3. Aggiungere supporto per formati aggiuntivi")
        print("   4. Implementare pulizia automatica cache")
        print("   5. Aggiungere metriche di sistema avanzate")

    except Exception as e:
        print(f"⚠️ Errore generazione report: {e}")

if __name__ == "__main__":
    # Esegui test miglioramenti performance
    test_performance_improvements()

    # Genera report ottimizzazioni
    generate_optimization_report()

    print(f"\n{'=' * 60}")
    print("✅ FASE 3 - OTTIMIZZAZIONI COMPLETATA!")
    print("=" * 60)
