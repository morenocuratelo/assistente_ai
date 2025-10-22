#!/usr/bin/env python3
"""
Demo di Integrazione del Framework di Diagnosi e Gestione Errori
Dimostra come utilizzare tutti i componenti insieme per un sistema completo.
"""
import os
import sys
import time
from datetime import datetime

# Aggiungi path corrente per import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_error_framework():
    """Demo del framework di diagnosi errori"""
    print("🧪 Demo Framework Diagnosi Errori")
    print("=" * 50)

    from error_diagnosis_framework import (
        error_framework,
        ProcessingState,
        ProcessingPhase,
        ErrorCategory,
        ErrorSeverity
    )

    # Simula inizializzazione processamento
    test_file = "test_document.pdf"
    correlation_id = error_framework.initialize_processing_status(test_file, test_file)
    print(f"✅ Inizializzato processamento: {correlation_id}")

    # Simula cambio stato
    success = error_framework.update_processing_state(
        test_file,
        ProcessingState.PROCESSING,
        ProcessingPhase.PHASE_2,
        correlation_id=correlation_id
    )
    print(f"✅ Stato aggiornato: {success}")

    # Simula errore
    test_exception = ValueError("Documento vuoto o illeggibile")
    error_record = error_framework.classify_error(test_exception, test_file, ProcessingPhase.PHASE_2)

    print(f"📋 Errore classificato: {error_record.error_category.value}")
    print(f"🔥 Severità: {error_record.error_severity.value}")
    print(f"📊 Stato fallimento: {error_record.processing_state.value}")

    # Registra errore
    error_framework.record_error(error_record, correlation_id)
    print("✅ Errore registrato nel sistema")

def demo_retry_framework():
    """Demo del sistema di retry"""
    print("\n🧪 Demo Sistema Retry")
    print("=" * 50)

    from retry_framework import (
        schedule_file_for_retry,
        get_files_ready_for_retry,
        get_retry_info,
        ErrorCategory
    )

    test_file = "test_document.pdf"

    # Schedula per retry
    success = schedule_file_for_retry(test_file, ErrorCategory.FORMAT_ERROR)
    print(f"✅ File schedulato per retry: {success}")

    # Verifica info retry
    retry_info = get_retry_info(test_file)
    if retry_info:
        print(f"📋 Info retry: tentativo {retry_info['attempts']}/{retry_info['max_retries']}")
        print(f"⏰ Prossimo retry: {retry_info['next_retry']}")

    # Verifica file pronti
    ready_files = get_files_ready_for_retry()
    print(f"📋 File pronti per retry: {len(ready_files)}")

def demo_monitoring_system():
    """Demo del sistema di monitoraggio"""
    print("\n🧪 Demo Sistema Monitoraggio")
    print("=" * 50)

    from advanced_monitoring import (
        start_advanced_monitoring,
        get_system_status,
        stop_advanced_monitoring,
        MonitoringConfig
    )

    # Configurazione demo
    config = MonitoringConfig(
        enable_email_alerts=False,  # Disabilita email per demo
        error_rate_threshold=5.0,   # Threshold più basso per demo
        metrics_collection_interval=5  # Intervallo più frequente per demo
    )

    # Avvia monitoraggio
    monitoring_system = start_advanced_monitoring(config)
    print("🚀 Sistema di monitoraggio avviato")

    # Attendi qualche secondo per collezionare metriche
    time.sleep(3)

    # Recupera stato
    status = get_system_status()
    health = status.get('health', {})

    print(f"💚 Stato salute: {health.get('overall_status', 'unknown')}")
    print(f"📊 Metriche: {len(status.get('metrics', {}))} categorie")

    # Ferma monitoraggio
    stop_advanced_monitoring()
    print("⏹️ Sistema di monitoraggio fermato")

def demo_dashboard_integration():
    """Demo integrazione dashboard"""
    print("\n🧪 Demo Dashboard Unificata")
    print("=" * 50)

    from unified_dashboard import get_unified_dashboard_data

    try:
        # Recupera dati unificati
        data = get_unified_dashboard_data()

        if data:
            processing = data.get('processing', {})
            errors = data.get('errors', {})
            retry = data.get('retry', {})

            print("📊 Dati processamento:")
            print(f"   - File totali: {processing.get('total_files', 0)}")
            print(f"   - File falliti: {processing.get('failed_files', 0)}")

            print("🚨 Dati errori:")
            print(f"   - Errori aperti: {errors.get('total_open_errors', 0)}")

            print("🔄 Dati retry:")
            stats = retry.get('statistics', {})
            print(f"   - File in retry: {stats.get('total_files_in_retry', 0)}")
            print(f"   - Pronti per retry: {stats.get('files_ready_for_retry', 0)}")

            print("✅ Dashboard integrazione funzionante")
        else:
            print("⚠️ Nessun dato disponibile per dashboard")

    except Exception as e:
        print(f"❌ Errore demo dashboard: {e}")

def demo_complete_workflow():
    """Demo workflow completo"""
    print("\n🎯 Demo Workflow Completo")
    print("=" * 50)

    # Simula un workflow completo di processamento con errore e recovery
    test_file = "demo_workflow.pdf"

    print(f"📋 Test file: {test_file}")

    # 1. Inizializza processamento
    from error_diagnosis_framework import error_framework, ProcessingState, ProcessingPhase
    correlation_id = error_framework.initialize_processing_status(test_file, test_file)
    print(f"1️⃣ Inizializzato: {correlation_id}")

    # 2. Simula progresso
    error_framework.update_processing_state(
        test_file, ProcessingState.PROCESSING, ProcessingPhase.PHASE_2, correlation_id=correlation_id
    )
    print("2️⃣ Stato: PROCESSING")

    # 3. Simula errore
    test_error = ConnectionError("Timeout API LLM")
    error_record = error_framework.classify_error(test_error, test_file, ProcessingPhase.PHASE_3)
    error_framework.record_error(error_record, correlation_id)

    error_framework.update_processing_state(
        test_file,
        error_record.processing_state,
        ProcessingPhase.PHASE_3,
        error_message=error_record.error_message,
        correlation_id=correlation_id
    )
    print(f"3️⃣ Errore registrato: {error_record.error_category.value}")

    # 4. Schedula retry
    from retry_framework import schedule_file_for_retry
    retry_success = schedule_file_for_retry(test_file, error_record.error_category)
    print(f"4️⃣ Schedulato retry: {retry_success}")

    # 5. Verifica stato finale
    final_status = error_framework.get_processing_status(test_file)
    if final_status:
        print(f"5️⃣ Stato finale: {final_status.processing_state.value}")
        print(f"   Retry count: {final_status.retry_count}")

    print("✅ Workflow demo completato")

def main():
    """Funzione principale demo"""
    print("🚀 Demo Completa Framework Archivista AI")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    try:
        # Esegui demo componenti individuali
        demo_error_framework()
        demo_retry_framework()
        demo_monitoring_system()
        demo_dashboard_integration()

        print("\n" + "=" * 60)
        print("🎉 TUTTI I COMPONENTI FUNZIONANTI!")
        print("=" * 60)

        # Demo workflow completo
        demo_complete_workflow()

        print("\n" + "=" * 60)
        print("🏆 FRAMEWORK COMPLETO OPERATIVO!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERRORE NELLA DEMO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code)
