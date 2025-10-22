#!/usr/bin/env python3
"""
Test script per verificare il funzionamento della nuova architettura unificata.
"""

import sys
import os

def test_imports():
    """Test importazione componenti."""
    print("🔍 Test importazione componenti...")

    try:
        # Test componenti base
        from src.ui.components.base import BaseComponent, CollapsibleSidebar
        print("✅ Componenti base importati con successo")

        # Test servizi
        from src.services import ServiceManager, initialize_services
        print("✅ Servizi importati con successo")

        # Test configurazione
        from src.config.settings import ConfigurationManager
        print("✅ Configurazione importata con successo")

        return True

    except ImportError as e:
        print(f"❌ Errore importazione: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

def test_componenti():
    """Test creazione componenti."""
    print("\n🏗️ Test creazione componenti...")

    try:
        from src.ui.components import (
            create_collapsible_sidebar,
            create_modal_login,
            create_minimal_chat
        )

        # Crea componenti
        sidebar = create_collapsible_sidebar()
        login_modal = create_modal_login()
        chat = create_minimal_chat()

        print("✅ Tutti i componenti creati con successo")
        print(f"   - Sidebar: {type(sidebar).__name__}")
        print(f"   - Login Modal: {type(login_modal).__name__}")
        print(f"   - Chat: {type(chat).__name__}")

        return True

    except Exception as e:
        print(f"❌ Errore creazione componenti: {e}")
        return False

def test_servizi():
    """Test inizializzazione servizi."""
    print("\n⚙️ Test servizi...")

    try:
        from src.services import initialize_services, get_service_status

        if initialize_services():
            status = get_service_status()
            print("✅ Servizi inizializzati con successo")
            print(f"   - Stato: {status}")
            return True
        else:
            print("❌ Fallita inizializzazione servizi")
            return False

    except Exception as e:
        print(f"❌ Errore servizi: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Test Architettura Unificata - Archivista AI")
    print("=" * 50)

    # Test imports
    if not test_imports():
        print("\n❌ Test fallito - problemi di importazione")
        return False

    # Test componenti
    if not test_componenti():
        print("\n❌ Test fallito - problemi componenti")
        return False

    # Test servizi
    if not test_servizi():
        print("\n❌ Test fallito - problemi servizi")
        return False

    print("\n🎉 TUTTI I TEST SUPERATI!")
    print("\n📋 Prossimo passo: eseguire 'streamlit run unified_main.py'")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
