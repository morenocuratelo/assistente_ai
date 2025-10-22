"""
Test per ProjectService e ProjectSelector.

Verifica funzionalità di project switching e gestione progetti.
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.project_service import ProjectService
from src.database.repositories.project_repository import ProjectRepository
from src.ui.components.project_selector import ProjectSelector


@pytest.fixture
def in_memory_db():
    """Crea database in memoria per test."""
    return sqlite3.connect(":memory:")


@pytest.fixture
def project_repository(in_memory_db):
    """Crea ProjectRepository per test."""
    return ProjectRepository(in_memory_db)


@pytest.fixture
def project_service(project_repository):
    """Crea ProjectService per test."""
    return ProjectService(project_repository)


@pytest.fixture
def sample_projects():
    """Dati di test per progetti."""
    return [
        {
            'name': 'Tesi Laurea',
            'type': 'Studio',
            'description': 'Tesi di laurea in informatica',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'user_id': 1
        },
        {
            'name': 'Ricerca AI',
            'type': 'Ricerca',
            'description': 'Ricerca su intelligenza artificiale',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'user_id': 1
        },
        {
            'name': 'Progetto Personale',
            'type': 'Personale',
            'description': 'Progetto hobby',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'user_id': 2
        }
    ]


class TestProjectService:
    """Test per ProjectService."""

    @pytest.mark.unit
    def test_project_service_initialization(self, project_service):
        """Test inizializzazione ProjectService."""
        assert project_service is not None
        assert hasattr(project_service, 'repository')
        assert hasattr(project_service, 'logger')

    @pytest.mark.unit
    def test_create_project_validation(self, project_service, sample_projects):
        """Test validazione creazione progetto."""
        # Test progetto valido
        valid_project = sample_projects[0]
        result = project_service.create_project(valid_project)

        assert result.success is True
        assert result.data is not None
        assert result.data['name'] == valid_project['name']

        # Test progetto senza nome
        invalid_project = {'type': 'Studio', 'description': 'Test'}
        result = project_service.create_project(invalid_project)

        assert result.success is False
        assert "Nome progetto obbligatorio" in result.message

        # Test progetto con nome troppo lungo
        long_name_project = {'name': 'A' * 101, 'type': 'Studio'}
        result = project_service.create_project(long_name_project)

        assert result.success is False
        assert "Nome progetto troppo lungo" in result.message

    @pytest.mark.unit
    def test_get_all_projects(self, project_service, sample_projects):
        """Test recupero tutti i progetti."""
        # Crea alcuni progetti
        for project in sample_projects:
            result = project_service.create_project(project)
            assert result.success

        # Recupera tutti i progetti
        result = project_service.get_all_projects()

        assert result.success is True
        assert len(result.data) >= len(sample_projects)

        # Verifica che i progetti creati siano presenti
        project_names = [p['name'] for p in result.data]
        assert 'Tesi Laurea' in project_names
        assert 'Ricerca AI' in project_names

    @pytest.mark.unit
    def test_project_crud_operations(self, project_service, sample_projects):
        """Test operazioni CRUD complete."""
        project_data = sample_projects[0]

        # CREATE
        create_result = project_service.create_project(project_data)
        assert create_result.success
        project_id = create_result.data['id']

        # READ
        read_result = project_service.get_by_id(project_id)
        assert read_result.success
        assert read_result.data['name'] == project_data['name']

        # UPDATE
        update_data = {'name': 'Tesi Laurea - Aggiornata', 'type': 'Ricerca'}
        update_result = project_service.update(project_id, update_data)
        assert update_result.success

        # Verifica update
        updated_result = project_service.get_by_id(project_id)
        assert updated_result.data['name'] == update_data['name']
        assert updated_result.data['type'] == update_data['type']

        # DELETE
        delete_result = project_service.delete(project_id)
        assert delete_result.success

        # Verifica eliminazione
        deleted_result = project_service.get_by_id(project_id)
        assert not deleted_result.success

    @pytest.mark.unit
    def test_project_search(self, project_service, sample_projects):
        """Test ricerca progetti."""
        # Crea progetti
        for project in sample_projects:
            project_service.create_project(project)

        # Test ricerca per nome
        search_result = project_service.search_projects('Tesi')
        assert search_result.success
        assert len(search_result.data) > 0

        # Test ricerca per descrizione
        search_result = project_service.search_projects('intelligenza')
        assert search_result.success
        assert len(search_result.data) > 0

        # Test ricerca senza risultati
        search_result = project_service.search_projects('nonexistent')
        assert search_result.success
        assert len(search_result.data) == 0

    @pytest.mark.unit
    def test_project_filtering(self, project_service, sample_projects):
        """Test filtri progetti."""
        # Crea progetti
        for project in sample_projects:
            project_service.create_project(project)

        # Test filtro per tipo
        studio_result = project_service.get_projects_by_type('Studio')
        assert studio_result.success
        assert len(studio_result.data) > 0

        # Verifica che tutti i risultati siano del tipo corretto
        for project in studio_result.data:
            assert project['type'] == 'Studio'


class TestProjectSelector:
    """Test per ProjectSelector component."""

    @pytest.mark.unit
    def test_project_selector_initialization(self):
        """Test inizializzazione ProjectSelector."""
        selector = ProjectSelector()
        assert selector is not None
        assert hasattr(selector, 'on_project_change')
        assert hasattr(selector, 'selected_project')
        assert hasattr(selector, 'projects_cache')

    @pytest.mark.unit
    def test_project_creation_through_selector(self, project_service):
        """Test creazione progetto tramite selector."""
        selector = ProjectSelector()
        selector.project_service = project_service

        # Crea progetto
        success = selector._create_project('Test Project', 'Studio', 'Test description')

        assert success is True

        # Verifica progetto creato
        projects_result = project_service.get_all_projects()
        assert projects_result.success
        assert len(projects_result.data) > 0

        # Trova progetto creato
        created_project = next(
            (p for p in projects_result.data if p['name'] == 'Test Project'),
            None
        )
        assert created_project is not None
        assert created_project['type'] == 'Studio'
        assert created_project['description'] == 'Test description'

    @pytest.mark.unit
    def test_project_selection(self, project_service, sample_projects):
        """Test selezione progetto."""
        selector = ProjectSelector()
        selector.project_service = project_service

        # Crea progetti
        for project in sample_projects:
            selector._create_project(project['name'], project['type'], project['description'])

        # Test selezione progetto
        projects_list = selector._get_projects_list()
        assert len(projects_list) >= len(sample_projects)

        # Seleziona primo progetto
        first_project = projects_list[0]
        selector._set_active_project(first_project)

        # Verifica progetto attivo
        assert selector.selected_project == first_project
        assert selector.get_active_project() == first_project

    @pytest.mark.unit
    def test_project_deletion(self, project_service, sample_projects):
        """Test eliminazione progetto."""
        selector = ProjectSelector()
        selector.project_service = project_service

        # Crea progetto
        project_data = sample_projects[0]
        create_result = project_service.create_project(project_data)
        assert create_result.success
        project_id = create_result.data['id']

        # Elimina progetto
        success = selector._delete_project(project_id)
        assert success is True

        # Verifica eliminazione
        deleted_result = project_service.get_by_id(project_id)
        assert not deleted_result.success

    @pytest.mark.unit
    def test_project_validation(self):
        """Test validazione dati progetto."""
        selector = ProjectSelector()

        # Test validazione nome vuoto
        validation = selector.project_service._validate_project_data({'type': 'Studio'})
        assert validation['valid'] is False
        assert 'Nome progetto obbligatorio' in validation['errors']

        # Test validazione nome troppo lungo
        validation = selector.project_service._validate_project_data({'name': 'A' * 101, 'type': 'Studio'})
        assert validation['valid'] is False
        assert 'Nome progetto troppo lungo (max 100 caratteri)' in validation['errors']

        # Test validazione tipo non valido
        validation = selector.project_service._validate_project_data({'name': 'Test', 'type': 'InvalidType'})
        assert validation['valid'] is False
        assert 'Tipo progetto non valido. Usa: Ricerca, Studio, Personale, Lavoro' in validation['errors']

        # Test validazione progetto valido
        validation = selector.project_service._validate_project_data({
            'name': 'Test Project',
            'type': 'Studio',
            'description': 'Valid project'
        })
        assert validation['valid'] is True
        assert len(validation['errors']) == 0

    @pytest.mark.unit
    def test_project_switching_callback(self, project_service, sample_projects):
        """Test callback cambio progetto."""
        callback_called = False
        callback_project = None

        def mock_callback(project):
            nonlocal callback_called, callback_project
            callback_called = True
            callback_project = project

        selector = ProjectSelector(on_project_change=mock_callback)
        selector.project_service = project_service

        # Crea progetto
        project_data = sample_projects[0]
        create_result = project_service.create_project(project_data)
        assert create_result.success

        # Seleziona progetto
        projects_list = selector._get_projects_list()
        first_project = projects_list[0]

        selector._set_active_project(first_project)

        # Verifica callback chiamato
        assert callback_called is True
        assert callback_project == first_project

    @pytest.mark.unit
    def test_cache_management(self, project_service, sample_projects):
        """Test gestione cache progetti."""
        selector = ProjectSelector()
        selector.project_service = project_service

        # Cache inizialmente vuota
        assert len(selector.projects_cache) == 0

        # Crea progetto
        project_data = sample_projects[0]
        selector._create_project(project_data['name'], project_data['type'], project_data['description'])

        # Cache dovrebbe essere aggiornata
        projects_list = selector._get_projects_list()
        assert len(selector.projects_cache) > 0

        # Test refresh cache
        selector.refresh_projects()
        assert len(selector.projects_cache) == 0


class TestProjectIntegration:
    """Test integrazione ProjectService e ProjectSelector."""

    @pytest.mark.integration
    def test_full_project_workflow(self, project_service, sample_projects):
        """Test workflow completo gestione progetti."""
        # 1. Crea progetto
        project_data = sample_projects[0]
        create_result = project_service.create_project(project_data)
        assert create_result.success
        project_id = create_result.data['id']

        # 2. Recupera progetto
        read_result = project_service.get_by_id(project_id)
        assert read_result.success
        assert read_result.data['name'] == project_data['name']

        # 3. Aggiorna progetto
        update_data = {'description': 'Descrizione aggiornata'}
        update_result = project_service.update(project_id, update_data)
        assert update_result.success

        # 4. Verifica update
        updated_result = project_service.get_by_id(project_id)
        assert updated_result.data['description'] == update_data['description']

        # 5. Elimina progetto
        delete_result = project_service.delete(project_id)
        assert delete_result.success

        # 6. Verifica eliminazione
        deleted_result = project_service.get_by_id(project_id)
        assert not deleted_result.success

    @pytest.mark.integration
    def test_project_selector_integration(self, project_service, sample_projects):
        """Test integrazione ProjectSelector con ProjectService."""
        selector = ProjectSelector()
        selector.project_service = project_service

        # Test creazione tramite selector
        success = selector._create_project('Integration Test', 'Studio', 'Test integration')
        assert success is True

        # Test selezione progetto
        projects = selector._get_projects_list()
        assert len(projects) > 0

        # Seleziona progetto
        test_project = next(p for p in projects if p['name'] == 'Integration Test')
        selector._set_active_project(test_project)

        # Verifica progetto attivo
        active = selector.get_active_project()
        assert active is not None
        assert active['name'] == 'Integration Test'

        # Test eliminazione
        success = selector._delete_project(test_project['id'])
        assert success is True

        # Verifica rimozione da cache
        assert test_project not in selector.projects_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
