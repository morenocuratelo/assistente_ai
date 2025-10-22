"""
Test per DocumentService.

Verifica tutte le funzionalità del service documenti implementato nella Fase 2.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.document_service import DocumentService
from src.database.models.document import Document, DocumentCreate, DocumentUpdate

class TestDocumentService:
    """Test suite per DocumentService."""

    def test_service_initialization(self, document_service):
        """Test inizializzazione service."""
        assert document_service is not None
        assert hasattr(document_service, 'repository')
        assert hasattr(document_service, 'logger')

    def test_service_initialization_with_custom_repository(self, document_repository):
        """Test inizializzazione con repository custom."""
        service = DocumentService(document_repository)
        assert service.repository is document_repository

    @pytest.mark.unit
    def test_get_by_id_not_supported(self, document_service):
        """Test che get_by_id restituisca errore per documenti."""
        result = document_service.get_by_id(1)

        assert result['success'] is False
        assert 'non supportata' in result['message']
        assert result['error'] == 'ID-based lookup not supported for documents'

    @pytest.mark.unit
    def test_get_by_filename_success(self, document_service, sample_document_data):
        """Test recupero documento per filename con successo."""
        # Mock repository response
        mock_document = Mock()
        mock_document.dict.return_value = sample_document_data
        document_service.repository.get_by_filename.return_value = mock_document

        result = document_service.get_by_filename("test.pdf")

        assert result['success'] is True
        assert result['data'] == sample_document_data
        assert result['message'] == 'Documento recuperato'
        document_service.repository.get_by_filename.assert_called_once_with("test.pdf")

    @pytest.mark.unit
    def test_get_by_filename_not_found(self, document_service):
        """Test recupero documento non trovato."""
        document_service.repository.get_by_filename.return_value = None

        result = document_service.get_by_filename("nonexistent.pdf")

        assert result['success'] is False
        assert result['message'] == 'Documento non trovato'

    @pytest.mark.unit
    def test_get_by_filename_exception(self, document_service):
        """Test gestione eccezione nel recupero documento."""
        document_service.repository.get_by_filename.side_effect = Exception("DB Error")

        result = document_service.get_by_filename("test.pdf")

        assert result['success'] is False
        assert 'Errore durante recupero documento' in result['message']
        assert 'DB Error' in result['error']

    @pytest.mark.unit
    def test_get_all_success(self, document_service, sample_document_data):
        """Test recupero tutti i documenti con successo."""
        # Mock documenti
        mock_docs = []
        for i in range(3):
            mock_doc = Mock()
            data = sample_document_data.copy()
            data['file_name'] = f"test{i}.pdf"
            mock_doc.dict.return_value = data
            mock_docs.append(mock_doc)

        document_service.repository.get_all.return_value = mock_docs

        result = document_service.get_all()

        assert result['success'] is True
        assert len(result['data']) == 3
        assert 'Recuperati 3 documenti' in result['message']

    @pytest.mark.unit
    def test_get_all_with_filters(self, document_service, sample_document_data):
        """Test recupero documenti con filtri."""
        mock_docs = [Mock()]
        mock_docs[0].dict.return_value = sample_document_data

        document_service.repository.get_all.return_value = mock_docs

        filters = {"category_id": "TEST/001"}
        result = document_service.get_all(filters)

        assert result['success'] is True
        document_service.repository.get_all.assert_called_once_with(filters)

    @pytest.mark.unit
    def test_get_all_as_dataframe_success(self, document_service):
        """Test recupero documenti come DataFrame."""
        # Mock DataFrame
        df_data = {
            'file_name': ['test1.pdf', 'test2.pdf'],
            'title': ['Title 1', 'Title 2'],
            'category_id': ['CAT1', 'CAT2']
        }
        mock_df = pd.DataFrame(df_data)
        document_service.repository.get_all_documents.return_value = mock_df

        result = document_service.get_all_as_dataframe()

        assert result['success'] is True
        assert len(result['data']) == 2
        assert result['data'][0]['file_name'] == 'test1.pdf'

    @pytest.mark.unit
    def test_get_all_as_dataframe_empty(self, document_service):
        """Test recupero documenti come DataFrame vuoto."""
        empty_df = pd.DataFrame()
        document_service.repository.get_all_documents.return_value = empty_df

        result = document_service.get_all_as_dataframe()

        assert result['success'] is True
        assert result['data'] == []

    @pytest.mark.unit
    def test_create_document_success(self, document_service, sample_document_data):
        """Test creazione documento con successo."""
        # Mock documento creato
        mock_document = Mock()
        mock_document.dict.return_value = sample_document_data
        document_service.repository.create.return_value = mock_document

        result = document_service.create(sample_document_data)

        assert result['success'] is True
        assert result['data'] == sample_document_data
        assert result['message'] == 'Documento creato'

        # Verifica che DocumentCreate sia stato creato correttamente
        document_service.repository.create.assert_called_once()
        call_args = document_service.repository.create.call_args[0][0]
        assert hasattr(call_args, 'file_name')
        assert call_args.file_name == sample_document_data['file_name']

    @pytest.mark.unit
    def test_create_document_exception(self, document_service, sample_document_data):
        """Test gestione eccezione nella creazione documento."""
        document_service.repository.create.side_effect = Exception("Validation Error")

        result = document_service.create(sample_document_data)

        assert result['success'] is False
        assert 'Errore durante creazione documento' in result['message']
        assert 'Validation Error' in result['error']

    @pytest.mark.unit
    def test_update_document_success(self, document_service, sample_document_data):
        """Test aggiornamento documento con successo."""
        document_service.repository.update.return_value = True

        update_data = {"title": "Updated Title"}
        result = document_service.update("test.pdf", update_data)

        assert result['success'] is True
        assert result['message'] == 'Documento aggiornato'

        # Verifica chiamata repository
        document_service.repository.update.assert_called_once()
        args = document_service.repository.update.call_args[0]
        assert args[0] == "test.pdf"

        # Verifica DocumentUpdate
        call_args = document_service.repository.update.call_args[0]
        update_obj = call_args[1]
        assert hasattr(update_obj, 'title')
        assert update_obj.title == "Updated Title"

    @pytest.mark.unit
    def test_update_document_not_found(self, document_service):
        """Test aggiornamento documento non trovato."""
        document_service.repository.update.return_value = False

        result = document_service.update("nonexistent.pdf", {"title": "New Title"})

        assert result['success'] is False
        assert result['message'] == 'Documento non trovato'

    @pytest.mark.unit
    def test_delete_document_success(self, document_service):
        """Test eliminazione documento con successo."""
        document_service.repository.delete.return_value = True

        result = document_service.delete("test.pdf")

        assert result['success'] is True
        assert result['message'] == 'Documento eliminato'
        document_service.repository.delete.assert_called_once_with("test.pdf")

    @pytest.mark.unit
    def test_delete_document_not_found(self, document_service):
        """Test eliminazione documento non trovato."""
        document_service.repository.delete.return_value = False

        result = document_service.delete("nonexistent.pdf")

        assert result['success'] is False
        assert result['message'] == 'Documento non trovato'

    @pytest.mark.unit
    def test_search_documents_success(self, document_service, sample_document_data):
        """Test ricerca documenti con successo."""
        # Mock documenti trovati
        mock_docs = []
        for i in range(2):
            mock_doc = Mock()
            data = sample_document_data.copy()
            data['file_name'] = f"result{i}.pdf"
            mock_doc.dict.return_value = data
            mock_docs.append(mock_doc)

        document_service.repository.search_documents.return_value = mock_docs

        result = document_service.search_documents("test query")

        assert result['success'] is True
        assert len(result['data']) == 2
        assert 'Trovati 2 documenti' in result['message']

    @pytest.mark.unit
    def test_get_documents_by_category_success(self, document_service, sample_document_data):
        """Test recupero documenti per categoria."""
        mock_docs = [Mock()]
        mock_docs[0].dict.return_value = sample_document_data

        document_service.repository.get_documents_by_category.return_value = mock_docs

        result = document_service.get_documents_by_category("TEST/001")

        assert result['success'] is True
        assert len(result['data']) == 1
        assert 'categoria TEST/001' in result['message']

    @pytest.mark.unit
    def test_get_recent_documents_success(self, document_service, sample_document_data):
        """Test recupero documenti recenti."""
        mock_docs = []
        for i in range(3):
            mock_doc = Mock()
            data = sample_document_data.copy()
            data['file_name'] = f"recent{i}.pdf"
            mock_doc.dict.return_value = data
            mock_docs.append(mock_doc)

        document_service.repository.get_recent_documents.return_value = mock_docs

        result = document_service.get_recent_documents(5)

        assert result['success'] is True
        assert len(result['data']) == 3
        assert 'Recuperati 3 documenti recenti' in result['message']

    @pytest.mark.unit
    def test_get_document_stats_empty(self, document_service):
        """Test statistiche documenti - database vuoto."""
        empty_df = pd.DataFrame()
        document_service.repository.get_all_documents.return_value = empty_df

        result = document_service.get_document_stats()

        assert result['success'] is True
        assert result['data']['total_documents'] == 0
        assert result['data']['categories'] == {}
        assert result['data']['recent_uploads'] == 0

    @pytest.mark.unit
    def test_get_document_stats_with_data(self, document_service):
        """Test statistiche documenti con dati."""
        # Crea DataFrame con dati di test
        df_data = {
            'category_id': ['CAT1', 'CAT1', 'CAT2', 'CAT1'],
            'processed_at': ['2024-01-01', None, '2024-01-02', '2024-01-03']
        }
        test_df = pd.DataFrame(df_data)
        document_service.repository.get_all_documents.return_value = test_df

        result = document_service.get_document_stats()

        assert result['success'] is True
        assert result['data']['total_documents'] == 4
        assert result['data']['categories']['CAT1'] == 3
        assert result['data']['categories']['CAT2'] == 1
        assert result['data']['recent_uploads'] == 3

    @pytest.mark.unit
    def test_bulk_update_documents_success(self, document_service):
        """Test aggiornamento documenti in blocco."""
        updates = [
            {"file_name": "doc1.pdf", "title": "New Title 1"},
            {"file_name": "doc2.pdf", "title": "New Title 2"}
        ]

        # Mock successful updates
        document_service.repository.update.side_effect = [True, True]

        result = document_service.bulk_update_documents(updates)

        assert result['success'] is True
        assert result['data']['success_count'] == 2
        assert len(result['data']['errors']) == 0
        assert 'Aggiornati 2 documenti' in result['message']

    @pytest.mark.unit
    def test_bulk_update_documents_partial_failure(self, document_service):
        """Test aggiornamento documenti in blocco con errori parziali."""
        updates = [
            {"file_name": "doc1.pdf", "title": "New Title 1"},
            {"file_name": "doc2.pdf", "title": "New Title 2"}
        ]

        # Mock mixed results
        document_service.repository.update.side_effect = [True, False]

        result = document_service.bulk_update_documents(updates)

        assert result['success'] is True
        assert result['data']['success_count'] == 1
        assert len(result['data']['errors']) == 1
        assert 'Documento doc2.pdf non trovato' in result['data']['errors'][0]

    @pytest.mark.unit
    def test_bulk_update_documents_with_exception(self, document_service):
        """Test aggiornamento documenti in blocco con eccezione."""
        updates = [{"file_name": "doc1.pdf", "title": "New Title"}]

        document_service.repository.update.side_effect = Exception("DB Error")

        result = document_service.bulk_update_documents(updates)

        assert result['success'] is False
        assert 'Errore durante aggiornamento documenti in blocco' in result['message']

    @pytest.mark.unit
    def test_update_metadata_success(self, document_service):
        """Test aggiornamento metadati documento."""
        document_service.repository.update_document_metadata.return_value = True

        metadata = {"title": "New Title", "authors": "New Author"}
        result = document_service.update_metadata("test.pdf", metadata)

        assert result['success'] is True
        assert result['message'] == 'Metadati documento aggiornati'

    @pytest.mark.unit
    def test_update_metadata_not_found(self, document_service):
        """Test aggiornamento metadati documento non trovato."""
        document_service.repository.update_document_metadata.return_value = False

        result = document_service.update_metadata("nonexistent.pdf", {"title": "New"})

        assert result['success'] is False
        assert result['message'] == 'Documento non trovato'

    @pytest.mark.integration
    def test_document_service_integration(self, document_service, sample_document_data):
        """Test integrazione completa servizio documenti."""
        # Crea documento
        create_result = document_service.create(sample_document_data)
        assert create_result['success'] is True

        # Recupera documento
        filename = sample_document_data['file_name']
        get_result = document_service.get_by_filename(filename)
        assert get_result['success'] is True
        assert get_result['data']['file_name'] == filename

        # Aggiorna documento
        update_data = {"title": "Updated Title"}
        update_result = document_service.update(filename, update_data)
        assert update_result['success'] is True

        # Verifica aggiornamento
        get_result = document_service.get_by_filename(filename)
        assert get_result['data']['title'] == "Updated Title"

        # Elimina documento
        delete_result = document_service.delete(filename)
        assert delete_result['success'] is True

        # Verifica eliminazione
        get_result = document_service.get_by_filename(filename)
        assert get_result['success'] is False

    @pytest.mark.performance
    def test_document_service_performance(self, document_service):
        """Test performance servizio documenti."""
        import time

        # Test creazione multipla
        start_time = time.time()
        for i in range(10):
            data = {
                "file_name": f"perf_test_{i}.pdf",
                "title": f"Performance Test {i}",
                "authors": "Perf Author",
                "publication_year": 2024,
                "category_id": "PERF/TEST"
            }
            document_service.create(data)
        create_time = time.time() - start_time

        # Test ricerca
        start_time = time.time()
        result = document_service.search_documents("Performance")
        search_time = time.time() - start_time

        # Verifica tempi ragionevoli (sotto 1 secondo)
        assert create_time < 1.0, f"Creazione troppo lenta: {create_time}s"
        assert search_time < 1.0, f"Ricerca troppo lenta: {search_time}s"
        assert result['success'] is True

    @pytest.mark.integration
    def test_document_service_with_real_dataframe(self, document_service):
        """Test servizio con DataFrame reale."""
        # Test get_all_as_dataframe
        df_result = document_service.get_all_as_dataframe()
        assert df_result['success'] is True

        # Verifica struttura dati
        if df_result['data']:
            # Se ci sono dati, verifica che siano nel formato corretto
            first_doc = df_result['data'][0]
            assert 'file_name' in first_doc
            assert 'title' in first_doc

    def test_response_format_consistency(self, document_service):
        """Test consistenza formato risposte."""
        # Test risposta successo
        success_response = document_service._create_response(True, "Test message", {"key": "value"})
        assert success_response.success is True
        assert success_response.message == "Test message"
        assert success_response.data == {"key": "value"}
        assert success_response.error is None

        # Test risposta errore
        error_response = document_service._create_response(False, "Error message", error="Error details")
        assert error_response.success is False
        assert error_response.message == "Error message"
        assert error_response.error == "Error details"
        assert error_response.data is None

    def test_error_handling_consistency(self, document_service):
        """Test consistenza gestione errori."""
        test_error = Exception("Test error")

        error_response = document_service._handle_error(test_error, "test operation")

        assert error_response.success is False
        assert 'Errore durante test operation' in error_response.message
        assert 'Test error' in error_response.error

    @pytest.mark.unit
    def test_document_service_with_mock_repository(self, mock_document_service, sample_document_data):
        """Test servizio con repository mockato."""
        # Configura mock
        mock_document_service.repository.get_by_filename.return_value = Mock()

        result = mock_document_service.get_by_filename("test.pdf")

        # Verifica che il repository sia stato chiamato correttamente
        mock_document_service.repository.get_by_filename.assert_called_once_with("test.pdf")

        # Verifica formato risposta anche con mock
        assert 'success' in result
        assert 'message' in result

    def test_service_method_coverage(self, document_service):
        """Test copertura metodi servizio."""
        # Verifica tutti i metodi pubblici esistano
        required_methods = [
            'get_by_id', 'get_by_filename', 'get_all', 'get_all_as_dataframe',
            'create', 'update', 'update_metadata', 'delete', 'search_documents',
            'get_documents_by_category', 'get_recent_documents', 'get_document_stats',
            'bulk_update_documents'
        ]

        for method_name in required_methods:
            assert hasattr(document_service, method_name), f"Metodo {method_name} mancante"
            assert callable(getattr(document_service, method_name)), f"{method_name} non è callable"

    def test_document_service_edge_cases(self, document_service):
        """Test casi limite servizio documenti."""
        # Test ricerca con stringa vuota
        result = document_service.search_documents("")
        assert result['success'] is True

        # Test ricerca con None
        result = document_service.search_documents(None)
        assert result['success'] is True

        # Test filtri None
        result = document_service.get_all(None)
        assert result['success'] is True

        # Test limite documenti recenti 0
        result = document_service.get_recent_documents(0)
        assert result['success'] is True

        # Test limite documenti recenti negativo
        result = document_service.get_recent_documents(-1)
        assert result['success'] is True
