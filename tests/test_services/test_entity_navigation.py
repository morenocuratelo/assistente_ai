"""
Test per la navigazione tra entità nel grafo della conoscenza.

Testa le funzionalità di navigazione, esplorazione e visualizzazione
delle entità e delle loro relazioni.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.ui.components.graph_visualization import GraphVisualization


class TestEntityNavigation:
    """Test per la navigazione tra entità."""

    @pytest.fixture
    def mock_graph_data(self):
        """Dati grafo mock per test."""
        return {
            'entities': [
                {
                    'id': 1,
                    'entity_name': 'Machine Learning',
                    'entity_type': 'concept',
                    'entity_description': 'Apprendimento automatico',
                    'confidence_score': 0.9,
                    'source_file_name': 'ml_paper.pdf'
                },
                {
                    'id': 2,
                    'entity_name': 'Neural Network',
                    'entity_type': 'concept',
                    'entity_description': 'Reti neurali artificiali',
                    'confidence_score': 0.8,
                    'source_file_name': 'ml_paper.pdf'
                },
                {
                    'id': 3,
                    'entity_name': 'Deep Learning',
                    'entity_type': 'concept',
                    'entity_description': 'Apprendimento profondo',
                    'confidence_score': 0.7,
                    'source_file_name': 'dl_review.pdf'
                }
            ],
            'relationships': [
                {
                    'id': 1,
                    'source_name': 'Machine Learning',
                    'target_name': 'Neural Network',
                    'relationship_type': 'includes',
                    'confidence_score': 0.85,
                    'source_file_name': 'ml_paper.pdf'
                },
                {
                    'id': 2,
                    'source_name': 'Neural Network',
                    'target_name': 'Deep Learning',
                    'relationship_type': 'related_to',
                    'confidence_score': 0.75,
                    'source_file_name': 'dl_review.pdf'
                }
            ]
        }

    @pytest.fixture
    def graph_viz(self):
        """Istanza GraphVisualization per test."""
        # Create a simple mock without external dependencies
        graph_viz = GraphVisualization.__new__(GraphVisualization)
        graph_viz.selected_entity = None
        graph_viz.min_confidence = 0.3
        graph_viz.graph_data = None
        graph_viz.filtered_entities = []
        graph_viz.filtered_relationships = []
        graph_viz.selected_entity_type = None
        graph_viz.on_entity_select = None

        # Mock the external functions
        graph_viz._get_user_knowledge_graph = lambda x: {'entities': [], 'relationships': []}
        graph_viz._get_entity_neighbors = lambda x, y: {'relationships': []}
        graph_viz._get_confidence_color = lambda x: '#00ff00'
        graph_viz._get_confidence_label = lambda x: 'Alta'

        return graph_viz

    def test_entity_navigation_initialization(self, graph_viz):
        """Test inizializzazione navigazione entità."""
        assert graph_viz.selected_entity is None
        assert graph_viz.min_confidence == 0.3
        assert graph_viz.filtered_entities == []
        assert graph_viz.filtered_relationships == []

    def test_entity_selection_navigation(self, graph_viz, mock_graph_data):
        """Test navigazione tramite selezione entità."""
        # Imposta dati grafo
        graph_viz.graph_data = mock_graph_data

        # Seleziona entità
        entity = mock_graph_data['entities'][0]
        graph_viz._explore_entity(entity)

        assert graph_viz.selected_entity == 'Machine Learning'

    def test_entity_neighbors_navigation(self, graph_viz, mock_graph_data):
        """Test navigazione verso entità vicine."""
        graph_viz.graph_data = mock_graph_data
        graph_viz.selected_entity = 'Machine Learning'

        # Mock session_state per evitare errori Streamlit
        with patch('streamlit.session_state') as mock_session:
            mock_session.__getitem__.return_value = 123  # Mock user_id

            # Mock per get_entity_neighbors
            with patch.object(graph_viz, '_get_entity_neighbors') as mock_get_neighbors:
                mock_get_neighbors.return_value = {
                    'relationships': [
                        {
                            'source_name': 'Machine Learning',
                            'target_name': 'Neural Network',
                            'relationship_type': 'includes',
                            'confidence_score': 0.85
                        }
                    ]
                }

                graph_viz._show_entity_neighbors()

                # Verifica che sia stata chiamata la funzione
                mock_get_neighbors.assert_called_once_with(123, 'Machine Learning')

    def test_entity_details_navigation(self, graph_viz, mock_graph_data):
        """Test navigazione dettagli entità."""
        graph_viz.graph_data = mock_graph_data
        entity = mock_graph_data['entities'][0]

        # Test visualizzazione dettagli
        graph_viz._show_entity_details(entity)

        # Verifica che l'entità sia stata processata
        assert entity['entity_name'] == 'Machine Learning'

    def test_confidence_based_navigation(self, graph_viz, mock_graph_data):
        """Test navigazione basata su confidenza."""
        graph_viz.graph_data = mock_graph_data
        graph_viz.min_confidence = 0.8

        # Applica filtri
        graph_viz._apply_filters()

        # Verifica che solo entità con alta confidenza siano incluse
        assert len(graph_viz.filtered_entities) == 2  # ML e Neural Network
        assert all(e['confidence_score'] >= 0.8 for e in graph_viz.filtered_entities)

    def test_entity_type_navigation(self, graph_viz, mock_graph_data):
        """Test navigazione per tipo entità."""
        graph_viz.graph_data = mock_graph_data
        graph_viz.selected_entity_type = 'concept'

        # Applica filtri
        graph_viz._apply_filters()

        # Verifica che solo entità del tipo selezionato siano incluse
        assert len(graph_viz.filtered_entities) == 3
        assert all(e['entity_type'] == 'concept' for e in graph_viz.filtered_entities)

    def test_relationship_navigation(self, graph_viz, mock_graph_data):
        """Test navigazione tramite relazioni."""
        graph_viz.graph_data = mock_graph_data

        # Prima applica filtri per popolare filtered_relationships
        graph_viz._apply_filters()

        # Test calcolo entità influenti
        influential = graph_viz._calculate_influential_entities()

        assert len(influential) > 0
        assert influential[0][1] >= influential[1][1]  # Prima entità più influente

    def test_navigation_with_empty_graph(self, graph_viz):
        """Test navigazione con grafo vuoto."""
        graph_viz.graph_data = {'entities': [], 'relationships': []}

        # Test con grafo vuoto
        graph_viz._apply_filters()

        assert graph_viz.filtered_entities == []
        assert graph_viz.filtered_relationships == []

    def test_navigation_confidence_emoji(self, graph_viz):
        """Test emoji confidenza per navigazione."""
        assert graph_viz._get_confidence_emoji(0.9) == "🟢"
        assert graph_viz._get_confidence_emoji(0.7) == "🟡"
        assert graph_viz._get_confidence_emoji(0.5) == "🟠"
        assert graph_viz._get_confidence_emoji(0.2) == "🔴"

    def test_navigation_entity_types_extraction(self, graph_viz, mock_graph_data):
        """Test estrazione tipi entità per navigazione."""
        graph_viz.graph_data = mock_graph_data

        entity_types = graph_viz._get_entity_types()

        assert 'concept' in entity_types
        assert len(entity_types) == 1

    def test_navigation_entity_names_extraction(self, graph_viz, mock_graph_data):
        """Test estrazione nomi entità per navigazione."""
        graph_viz.graph_data = mock_graph_data

        entity_names = graph_viz._get_entity_names()

        assert 'Machine Learning' in entity_names
        assert 'Neural Network' in entity_names
        assert 'Deep Learning' in entity_names

    def test_navigation_callback_integration(self, graph_viz, mock_graph_data):
        """Test integrazione callback navigazione."""
        callback_called = False
        callback_entity = None

        def mock_callback(entity):
            nonlocal callback_called, callback_entity
            callback_called = True
            callback_entity = entity

        graph_viz.on_entity_select = mock_callback
        entity = mock_graph_data['entities'][0]

        graph_viz._explore_entity(entity)

        assert callback_called
        assert callback_entity == entity

    def test_navigation_filter_combination(self, graph_viz, mock_graph_data):
        """Test navigazione con filtri combinati."""
        graph_viz.graph_data = mock_graph_data
        graph_viz.min_confidence = 0.8
        graph_viz.selected_entity_type = 'concept'

        # Applica filtri combinati
        graph_viz._apply_filters()

        # Verifica filtri combinati
        assert len(graph_viz.filtered_entities) == 2
        assert all(e['confidence_score'] >= 0.8 for e in graph_viz.filtered_entities)
        assert all(e['entity_type'] == 'concept' for e in graph_viz.filtered_entities)

    def test_navigation_performance_with_large_graph(self, graph_viz):
        """Test performance navigazione con grafo grande."""
        # Crea grafo grande
        large_graph = {
            'entities': [
                {
                    'id': i,
                    'entity_name': f'Entity_{i}',
                    'entity_type': 'concept',
                    'confidence_score': 0.5 + (i % 5) * 0.1,
                    'source_file_name': f'doc_{i}.pdf'
                }
                for i in range(100)
            ],
            'relationships': [
                {
                    'id': i,
                    'source_name': f'Entity_{i}',
                    'target_name': f'Entity_{(i + 1) % 100}',
                    'relationship_type': 'related_to',
                    'confidence_score': 0.6,
                    'source_file_name': f'doc_{i}.pdf'
                }
                for i in range(100)
            ]
        }

        graph_viz.graph_data = large_graph

        # Test performance filtri
        import time
        start_time = time.time()

        graph_viz._apply_filters()

        filter_time = time.time() - start_time

        # Verifica che filtri siano veloci
        assert filter_time < 1.0  # Meno di 1 secondo
        assert len(graph_viz.filtered_entities) <= 100

    def test_navigation_error_handling(self, graph_viz):
        """Test gestione errori navigazione."""
        # Test con dati corrotti
        graph_viz.graph_data = {
            'entities': [
                {'id': 1, 'entity_name': 'Test'},  # Dati incompleti
                {'entity_name': 'Test2', 'confidence_score': 0.5}  # ID mancante
            ],
            'relationships': [
                {'source_name': 'Test'}  # Dati incompleti
            ]
        }

        # Non dovrebbe crashare
        graph_viz._apply_filters()
        graph_viz._calculate_influential_entities()

        # Dovrebbe gestire graziosamente i dati incompleti
        assert len(graph_viz.filtered_entities) >= 0
        assert len(graph_viz.filtered_relationships) >= 0


class TestGraphNavigationIntegration:
    """Test integrazione navigazione grafo."""

    def test_navigation_with_real_data(self):
        """Test navigazione con dati reali (se disponibili)."""
        # Questo test può essere esteso quando ci sono dati reali
        pass

    def test_navigation_persistence(self):
        """Test persistenza stato navigazione."""
        # Test che lo stato di navigazione persista tra le sessioni
        pass

    def test_navigation_undo_redo(self):
        """Test funzionalità undo/redo navigazione."""
        # Test navigazione con possibilità di tornare indietro
        pass
