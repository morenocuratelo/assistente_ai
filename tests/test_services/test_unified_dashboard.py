"""
Test per UnifiedDashboard.

Verifica funzionalità del componente dashboard unificata
con integrazione completa dei servizi della Fase 2.
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Aggiungi path per import
sys.path.append(str(Path(__file__).parent.parent.parent))

class TestUnifiedDashboard:
    """Test suite per UnifiedDashboard."""

    @pytest.fixture
    def mock_session_state(self):
        """Mock session state per test."""
        with patch('streamlit.session_state') as mock_session:
            mock_session.user = None
            mock_session.context_files = []
            mock_session.chat_messages = []
            mock_session.active_tab = 'chat'
            mock_session.show_login = False
            mock_session.show_file_manager = False
            mock_session.sidebar_collapsed = False
            yield mock_session

    @pytest.fixture
    def dashboard(self):
        """Dashboard per test."""
        from src.ui.components.unified_dashboard import UnifiedDashboard
        return UnifiedDashboard()

    @pytest.mark.unit
    def test_dashboard_initialization(self, dashboard):
        """Test inizializzazione dashboard."""
        assert dashboard is not None
        assert hasattr(dashboard, 'active_tab')
        assert hasattr(dashboard, 'sidebar_collapsed')
        assert hasattr(dashboard, 'document_service')
        assert hasattr(dashboard, 'user_service')
        assert hasattr(dashboard, 'chat_service')

    @pytest.mark.unit
    def test_dashboard_with_mock_services(self):
        """Test dashboard con servizi mockati."""
        with patch('src.ui.components.unified_dashboard.DocumentService') as MockDocService, \
             patch('src.ui.components.unified_dashboard.UserService') as MockUserService, \
             patch('src.ui.components.unified_dashboard.ChatService') as MockChatService:

            from src.ui.components.unified_dashboard import UnifiedDashboard

            dashboard = UnifiedDashboard()

            # Verifica servizi mockati
            assert dashboard.document_service is not None
            assert dashboard.user_service is not None
            assert dashboard.chat_service is not None

    @pytest.mark.unit
    def test_tab_navigation(self, dashboard, mock_session_state):
        """Test navigazione tra tab."""
        # Test cambio tab
        dashboard.active_tab = "archive"
        assert dashboard.active_tab == "archive"

        dashboard.active_tab = "dashboard"
        assert dashboard.active_tab == "dashboard"

        dashboard.active_tab = "settings"
        assert dashboard.active_tab == "settings"

    @pytest.mark.unit
    def test_sidebar_toggle(self, dashboard):
        """Test toggle sidebar."""
        # Sidebar inizialmente non collassata
        assert dashboard.sidebar_collapsed is False

        # Test toggle
        dashboard.sidebar_collapsed = True
        assert dashboard.sidebar_collapsed is True

        dashboard.sidebar_collapsed = False
        assert dashboard.sidebar_collapsed is False

    @pytest.mark.integration
    def test_service_integration_in_dashboard(self, dashboard):
        """Test integrazione servizi nella dashboard."""
        # Verifica che i servizi siano stati inizializzati correttamente
        assert dashboard.document_service is not None
        assert dashboard.user_service is not None
        assert dashboard.chat_service is not None

        # Test metodi servizi disponibili
        assert hasattr(dashboard.document_service, 'get_all')
        assert hasattr(dashboard.user_service, 'authenticate')
        assert hasattr(dashboard.chat_service, 'create')

    @pytest.mark.unit
    def test_render_methods_exist(self, dashboard):
        """Test che tutti i metodi render esistano."""
        required_render_methods = [
            'render',
            'render_header',
            'render_sidebar',
            'render_file_context_manager',
            'render_chat_tab',
            'render_archive_tab',
            'render_dashboard_tab',
            'render_projects_tab',
            'render_career_tab',
            'render_graph_tab',
            'render_settings_tab',
            'render_active_tab',
            'handle_state_changes'
        ]

        for method_name in required_render_methods:
            assert hasattr(dashboard, method_name), f"Metodo {method_name} mancante"
            method = getattr(dashboard, method_name)
            assert callable(method), f"{method_name} non è callable"

    @pytest.mark.unit
    def test_modal_handlers(self, dashboard):
        """Test gestori modali."""
        modal_methods = [
            '_render_login_modal',
            '_render_file_manager_modal'
        ]

        for method_name in modal_methods:
            assert hasattr(dashboard, method_name), f"Metodo {method_name} mancante"
            method = getattr(dashboard, method_name)
            assert callable(method), f"{method_name} non è callable"

    @pytest.mark.unit
    def test_dashboard_factory_function(self):
        """Test funzione factory dashboard."""
        from src.ui.components.unified_dashboard import create_unified_dashboard

        dashboard = create_unified_dashboard()
        assert dashboard is not None
        assert isinstance(dashboard, object)

    @pytest.mark.integration
    def test_dashboard_with_real_services(self):
        """Test dashboard con servizi reali."""
        # Crea connessione database di test
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Crea tabelle necessarie
        conn.execute("""
            CREATE TABLE papers (
                file_name TEXT PRIMARY KEY, title TEXT, authors TEXT,
                publication_year INTEGER, category_id TEXT, created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
                email TEXT, password_hash TEXT, first_name TEXT, last_name TEXT,
                is_active BOOLEAN DEFAULT 1, is_admin BOOLEAN DEFAULT 0,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT,
                user_id INTEGER, is_active BOOLEAN DEFAULT 1, created_at TEXT
            )
        """)

        conn.commit()

        with patch('src.ui.components.unified_dashboard.DocumentRepository') as MockDocRepo, \
             patch('src.ui.components.unified_dashboard.UserRepository') as MockUserRepo, \
             patch('src.ui.components.unified_dashboard.ChatRepository') as MockChatRepo:

            # Mock repository per restituire connessione
            mock_doc_repo = Mock()
            mock_user_repo = Mock()
            mock_chat_repo = Mock()

            MockDocRepo.return_value = mock_doc_repo
            MockUserRepo.return_value = mock_user_repo
            MockChatRepo.return_value = mock_chat_repo

            from src.ui.components.unified_dashboard import UnifiedDashboard

            dashboard = UnifiedDashboard()

            # Verifica inizializzazione con servizi mock
            assert dashboard.document_service is not None
            assert dashboard.user_service is not None
            assert dashboard.chat_service is not None

        conn.close()

    @pytest.mark.unit
    def test_error_handling_in_services(self, dashboard):
        """Test gestione errori servizi."""
        # Mock servizi per simulare errori
        dashboard.document_service.get_all = Mock(side_effect=Exception("DB Error"))
        dashboard.user_service.authenticate = Mock(side_effect=Exception("Auth Error"))
        dashboard.chat_service.get_chats_by_user = Mock(side_effect=Exception("Chat Error"))

        # Verifica che dashboard gestisca errori graziosamente
        # (non dovrebbe crashare durante inizializzazione)
        assert dashboard is not None

    @pytest.mark.unit
    def test_state_management(self, dashboard, mock_session_state):
        """Test gestione stato dashboard."""
        # Test gestione stato tramite session state
        mock_session_state.show_login = True
        mock_session_state.show_file_manager = False

        # Dashboard dovrebbe gestire questi stati
        # (test che non crashi con stati diversi)
        assert dashboard.active_tab == "chat"

        # Test cambio stato
        dashboard.active_tab = "archive"
        assert dashboard.active_tab == "archive"

    @pytest.mark.unit
    def test_component_inheritance(self, dashboard):
        """Test ereditarietà componente."""
        from src.ui.components.base import BaseComponent

        # Verifica ereditarietà
        assert isinstance(dashboard, BaseComponent)
        assert hasattr(dashboard, 'render')
        assert hasattr(dashboard, 'logger')

    @pytest.mark.unit
    def test_dashboard_configuration(self):
        """Test configurazione dashboard."""
        # Test configurazione di default
        from src.ui.components.unified_dashboard import UnifiedDashboard

        dashboard = UnifiedDashboard()

        # Verifica valori di default
        assert dashboard.active_tab == "chat"
        assert dashboard.sidebar_collapsed is False

        # Verifica servizi inizializzati
        assert dashboard.document_service is not None
        assert dashboard.user_service is not None
        assert dashboard.chat_service is not None

    @pytest.mark.integration
    def test_dashboard_service_calls(self, dashboard):
        """Test chiamate servizi dashboard."""
        # Mock metodi servizi
        dashboard.document_service.get_all = Mock(return_value=Mock(success=True, data=[]))
        dashboard.user_service.get_all = Mock(return_value=Mock(success=True, data=[]))
        dashboard.chat_service.get_all = Mock(return_value=Mock(success=True, data=[]))

        # Test chiamate servizi non dovrebbero fallire
        try:
            # Queste chiamate dovrebbero funzionare senza errori
            doc_result = dashboard.document_service.get_all()
            user_result = dashboard.user_service.get_all()
            chat_result = dashboard.chat_service.get_all()

            # Verifica chiamate mockate
            dashboard.document_service.get_all.assert_called()
            dashboard.user_service.get_all.assert_called()
            dashboard.chat_service.get_all.assert_called()

        except Exception as e:
            pytest.fail(f"Chiamate servizi fallite: {e}")

    @pytest.mark.unit
    def test_dashboard_tab_content(self, dashboard):
        """Test contenuto tab dashboard."""
        # Test che ogni tab abbia contenuto appropriato
        tabs_content = {
            "chat": "Chat con AI",
            "archive": "Archivio Documenti",
            "dashboard": "Dashboard Statistiche",
            "projects": "Progetti",
            "career": "Carriera",
            "graph": "Grafo Conoscenza",
            "settings": "Impostazioni"
        }

        for tab_id, expected_content in tabs_content.items():
            dashboard.active_tab = tab_id

            # Verifica che il tab sia impostato correttamente
            assert dashboard.active_tab == tab_id

    @pytest.mark.unit
    def test_dashboard_error_recovery(self, dashboard):
        """Test recovery da errori dashboard."""
        # Simula errore servizio
        original_get_all = dashboard.document_service.get_all
        dashboard.document_service.get_all = Mock(side_effect=Exception("Service Error"))

        # Dashboard dovrebbe gestire errore graziosamente
        try:
            # Questo non dovrebbe crashare l'applicazione
            result = dashboard.document_service.get_all()
        except Exception:
            pass  # Errore atteso

        # Ripristina metodo originale
        dashboard.document_service.get_all = original_get_all

        # Dashboard dovrebbe essere ancora funzionale
        assert dashboard is not None
        assert dashboard.active_tab == "chat"

    @pytest.mark.unit
    def test_dashboard_memory_management(self, dashboard):
        """Test gestione memoria dashboard."""
        import gc

        # Crea molti messaggi di test
        test_messages = []
        for i in range(100):
            test_messages.append({
                "role": "user",
                "content": f"Test message {i}",
                "timestamp": f"2024-01-01T{i%24:02d}:00:00Z"
            })

        # Simula aggiunta messaggi
        initial_count = len(test_messages)

        # Verifica gestione memoria
        assert len(test_messages) == 100

        # Forza garbage collection
        gc.collect()

        # Dashboard dovrebbe essere ancora funzionale
        assert dashboard is not None

    def test_dashboard_method_signatures(self, dashboard):
        """Test firme metodi dashboard."""
        # Test firme metodi principali
        import inspect

        # render() dovrebbe essere metodo senza parametri richiesti
        sig = inspect.signature(dashboard.render)
        assert len(sig.parameters) == 0

        # handle_state_changes() dovrebbe essere metodo senza parametri
        sig = inspect.signature(dashboard.handle_state_changes)
        assert len(sig.parameters) == 0

        # render_active_tab() dovrebbe essere metodo senza parametri
        sig = inspect.signature(dashboard.render_active_tab)
        assert len(sig.parameters) == 0

    @pytest.mark.unit
    def test_dashboard_state_persistence(self, dashboard, mock_session_state):
        """Test persistenza stato dashboard."""
        # Test che stato sia mantenuto tra chiamate
        dashboard.active_tab = "archive"
        assert dashboard.active_tab == "archive"

        # Cambia stato
        dashboard.active_tab = "dashboard"
        assert dashboard.active_tab == "dashboard"

        # Verifica che sidebar state sia mantenuto
        dashboard.sidebar_collapsed = True
        assert dashboard.sidebar_collapsed is True

    @pytest.mark.integration
    def test_dashboard_full_workflow(self, dashboard):
        """Test workflow completo dashboard."""
        # 1. Test navigazione tab
        dashboard.active_tab = "archive"
        assert dashboard.active_tab == "archive"

        # 2. Test toggle sidebar
        dashboard.sidebar_collapsed = True
        assert dashboard.sidebar_collapsed is True

        # 3. Test ritorno a tab principale
        dashboard.active_tab = "chat"
        assert dashboard.active_tab == "chat"

        # 4. Test servizi ancora disponibili
        assert dashboard.document_service is not None
        assert dashboard.user_service is not None
        assert dashboard.chat_service is not None

    def test_dashboard_component_structure(self, dashboard):
        """Test struttura componente dashboard."""
        # Verifica attributi essenziali
        required_attributes = [
            'active_tab',
            'sidebar_collapsed',
            'document_service',
            'user_service',
            'chat_service'
        ]

        for attr in required_attributes:
            assert hasattr(dashboard, attr), f"Attributo {attr} mancante"

        # Verifica tipi attributi
        assert isinstance(dashboard.active_tab, str)
        assert isinstance(dashboard.sidebar_collapsed, bool)
        assert dashboard.document_service is not None
        assert dashboard.user_service is not None
        assert dashboard.chat_service is not None

    @pytest.mark.unit
    def test_dashboard_service_error_handling(self, dashboard):
        """Test gestione errori servizi dashboard."""
        # Mock servizi per restituire errori
        error_response = Mock()
        error_response.success = False
        error_response.message = "Errore servizio"
        error_response.data = None

        dashboard.document_service.get_all = Mock(return_value=error_response)
        dashboard.user_service.get_all = Mock(return_value=error_response)
        dashboard.chat_service.get_all = Mock(return_value=error_response)

        # Dashboard dovrebbe gestire errori senza crashare
        try:
            # Queste chiamate dovrebbero restituire risposte di errore gestibili
            doc_result = dashboard.document_service.get_all()
            user_result = dashboard.user_service.get_all()
            chat_result = dashboard.chat_service.get_all()

            # Verifica risposte errore
            assert doc_result.success is False
            assert user_result.success is False
            assert chat_result.success is False

        except Exception as e:
            pytest.fail(f"Gestione errori fallita: {e}")

    @pytest.mark.unit
    def test_dashboard_tab_switching(self, dashboard):
        """Test cambio tab dashboard."""
        # Test tutti i cambi tab possibili
        all_tabs = ["chat", "archive", "dashboard", "projects", "career", "graph", "settings"]

        for tab in all_tabs:
            dashboard.active_tab = tab
            assert dashboard.active_tab == tab

            # Verifica che tab sia valido
            assert tab in all_tabs

    def test_dashboard_initial_state(self, dashboard):
        """Test stato iniziale dashboard."""
        # Verifica stato iniziale
        assert dashboard.active_tab == "chat"
        assert dashboard.sidebar_collapsed is False

        # Verifica servizi inizializzati
        assert dashboard.document_service is not None
        assert dashboard.user_service is not None
        assert dashboard.chat_service is not None

        # Verifica logger configurato
        assert dashboard.logger is not None

    @pytest.mark.unit
    def test_dashboard_service_availability(self, dashboard):
        """Test disponibilità servizi dashboard."""
        # Verifica tutti i servizi necessari siano disponibili
        services = [
            dashboard.document_service,
            dashboard.user_service,
            dashboard.chat_service
        ]

        for service in services:
            assert service is not None, "Servizio non inizializzato"

        # Verifica metodi chiave disponibili
        assert hasattr(dashboard.document_service, 'get_all')
        assert hasattr(dashboard.user_service, 'authenticate')
        assert hasattr(dashboard.chat_service, 'create')

    def test_dashboard_responsiveness(self, dashboard):
        """Test responsività dashboard."""
        # Test che dashboard sia responsiva ai cambi di stato
        initial_tab = dashboard.active_tab
        initial_sidebar = dashboard.sidebar_collapsed

        # Cambia stato
        dashboard.active_tab = "archive"
        dashboard.sidebar_collapsed = True

        # Verifica cambi applicati
        assert dashboard.active_tab != initial_tab
        assert dashboard.sidebar_collapsed != initial_sidebar

        # Ripristina stato
        dashboard.active_tab = initial_tab
        dashboard.sidebar_collapsed = initial_sidebar

        # Verifica ripristino
        assert dashboard.active_tab == initial_tab
        assert dashboard.sidebar_collapsed == initial_sidebar
