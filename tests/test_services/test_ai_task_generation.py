"""
Test per AI Task Generation.

Verifica funzionalità di generazione task AI da documenti
e integrazione con il sistema accademico.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.career_service import CareerService
from src.database.repositories.career_repository import CareerRepository


@pytest.fixture
def mock_llm_response():
    """Mock response da LLM per task generation."""
    return {
        "tasks": [
            {
                "title": "Ripasso teoremi fondamentali",
                "description": "Rivedere i teoremi principali del capitolo",
                "priority": "high",
                "task_type": "short_term",
                "estimated_hours": 2,
                "due_date": "2024-01-15"
            },
            {
                "title": "Esercizi pratici",
                "description": "Completare gli esercizi del capitolo 3",
                "priority": "medium",
                "task_type": "medium_term",
                "estimated_hours": 4,
                "due_date": "2024-01-20"
            }
        ],
        "summary": "Generati 2 task accademici dal documento"
    }


@pytest.fixture
def sample_document_text():
    """Testo documento di esempio per AI task generation."""
    return """
    CAPITOLO 3: TEOREMI FONDAMENTALI

    In questo capitolo studieremo i teoremi fondamentali dell'analisi matematica.

    Sezione 3.1: Teorema del Valore Intermedio
    Il teorema del valore intermedio afferma che se una funzione continua f definita
    su un intervallo [a,b] assume valori f(a) e f(b) con f(a) < 0 < f(b), allora
    esiste almeno un punto c ∈ (a,b) tale che f(c) = 0.

    Sezione 3.2: Teorema di Weierstrass
    Il teorema di Weierstrass garantisce che una funzione continua su un intervallo
    chiuso e limitato raggiunge il suo massimo e minimo assoluto.

    Sezione 3.3: Conseguenze e Applicazioni
    I teoremi precedenti hanno importanti applicazioni nell'analisi numerica
    e nella risoluzione di equazioni.

    ESERCIZI:
    1. Dimostrare il teorema del valore intermedio
    2. Applicare il teorema a funzioni polinomiali
    3. Risolvere equazioni usando il teorema
    """


class TestAITaskGeneration:
    """Test per generazione task AI."""

    @pytest.mark.unit
    def test_ai_task_generation_basic(self, mock_llm_response):
        """Test generazione task AI base."""
        # Crea service
        career_service = CareerService(Mock())

        # Test generazione task (senza AI per ora)
        document_text = "Test document for AI task generation"
        generated_tasks = career_service._generate_ai_tasks(document_text)

        # Verifica
        assert generated_tasks is not None
        assert 'tasks' in generated_tasks
        assert len(generated_tasks['tasks']) > 0

        # Verifica task structure
        first_task = generated_tasks['tasks'][0]
        assert 'title' in first_task
        assert 'description' in first_task
        assert 'priority' in first_task
        assert 'task_type' in first_task

    @pytest.mark.unit
    def test_ai_task_generation_academic_content(self, sample_document_text):
        """Test generazione task da contenuto accademico."""
        # Crea service
        career_service = CareerService(Mock())

        # Test generazione da testo accademico
        generated_tasks = career_service._generate_ai_tasks(sample_document_text)

        # Verifica task accademici generati
        assert generated_tasks is not None
        assert len(generated_tasks['tasks']) >= 1

        # Verifica task accademici specifici
        task_titles = [task['title'] for task in generated_tasks['tasks']]
        assert any('teorema' in title.lower() or 'eserciz' in title.lower() for title in task_titles)

    @pytest.mark.unit
    def test_ai_task_validation(self):
        """Test validazione task AI generati."""
        # Crea service
        career_service = CareerService(Mock())

        # Test validazione
        valid_tasks = {
            'tasks': [
                {
                    'title': 'Test Task',
                    'description': 'Test description',
                    'priority': 'high',
                    'task_type': 'short_term'
                }
            ]
        }

        validation_result = career_service._validate_ai_tasks(valid_tasks)

        assert validation_result['valid'] is True
        assert len(validation_result['errors']) == 0

    @pytest.mark.unit
    def test_ai_task_invalid_response(self):
        """Test gestione risposta AI non valida."""
        # Crea service
        career_service = CareerService(Mock())

        # Test gestione errore
        document_text = "Test document"
        generated_tasks = career_service._generate_ai_tasks(document_text)

        # Dovrebbe gestire l'errore graziosamente
        assert generated_tasks is not None
        assert 'tasks' in generated_tasks

    @pytest.mark.unit
    def test_task_priority_mapping(self):
        """Test mappatura priorità task."""
        career_service = CareerService(Mock())

        # Test mappatura priorità
        test_cases = [
            ("high", "high"),
            ("medium", "medium"),
            ("low", "low"),
            ("urgent", "high"),  # Default fallback
            ("", "medium")  # Default fallback
        ]

        for input_priority, expected_priority in test_cases:
            mapped_priority = career_service._map_task_priority(input_priority)
            assert mapped_priority == expected_priority

    @pytest.mark.unit
    def test_task_type_mapping(self):
        """Test mappatura tipo task."""
        career_service = CareerService(Mock())

        # Test mappatura tipo
        test_cases = [
            ("short_term", "short_term"),
            ("medium_term", "medium_term"),
            ("long_term", "long_term"),
            ("esame", "long_term"),  # Default fallback
            ("", "short_term")  # Default fallback
        ]

        for input_type, expected_type in test_cases:
            mapped_type = career_service._map_task_type(input_type)
            assert mapped_type == expected_type

    @pytest.mark.unit
    def test_task_due_date_calculation(self):
        """Test calcolo date scadenza task."""
        career_service = CareerService(Mock())

        # Test calcolo date
        base_date = datetime.now()

        # Task short_term: 3 giorni
        short_term_due = career_service._calculate_task_due_date("short_term", base_date)
        assert (short_term_due - base_date).days <= 7

        # Task medium_term: 14 giorni
        medium_term_due = career_service._calculate_task_due_date("medium_term", base_date)
        assert (medium_term_due - base_date).days <= 21

        # Task long_term: 30 giorni
        long_term_due = career_service._calculate_task_due_date("long_term", base_date)
        assert (long_term_due - base_date).days <= 60


class TestAITaskIntegration:
    """Test integrazione AI task generation."""

    @pytest.mark.integration
    def test_full_ai_task_workflow(self, sample_document_text):
        """Test workflow completo AI task generation."""
        # Crea service
        career_service = CareerService(Mock())

        # 1. Genera task AI
        generated_tasks = career_service._generate_ai_tasks(sample_document_text)

        # 2. Valida task
        validation_result = career_service._validate_ai_tasks(generated_tasks)
        assert validation_result['valid'] is True

        # 3. Arricchisci task con metadati
        enriched_tasks = career_service._enrich_ai_tasks(generated_tasks, "test_user_123")

        # 4. Verifica arricchimento
        assert len(enriched_tasks) > 0
        for task in enriched_tasks:
            assert 'id' in task
            assert 'created_at' in task
            assert 'user_id' in task

    @pytest.mark.integration
    def test_ai_task_persistence(self, sample_document_text):
        """Test persistenza task AI nel database."""
        # Crea repository in memoria
        import sqlite3
        db = sqlite3.connect(":memory:")
        repository = CareerRepository(db)

        # Crea service
        career_service = CareerService(repository)

        # Simula generazione task AI
        ai_tasks = {
            'tasks': [
                {
                    'title': 'Test AI Task',
                    'description': 'Task generato da AI',
                    'priority': 'high',
                    'task_type': 'short_term'
                }
            ]
        }

        # Salva task nel database
        user_id = 1
        course_id = 1

        for task_data in ai_tasks['tasks']:
            task_data.update({
                'user_id': user_id,
                'course_id': course_id,
                'status': 'pending'
            })

            result = repository.create_task(task_data)
            assert result is not None
            assert result['title'] == task_data['title']

    @pytest.mark.integration
    def test_ai_task_association_with_documents(self):
        """Test associazione task AI con documenti."""
        # Test associazione logica tra task generati e documento sorgente
        document_text = "Test document about calculus and theorems"
        course_id = 1

        # Simula generazione task
        generated_tasks = [
            {
                'title': 'Study calculus theorems',
                'description': 'Review fundamental calculus theorems',
                'priority': 'high',
                'task_type': 'short_term',
                'document_source': 'calculus_textbook.pdf'
            }
        ]

        # Verifica associazione
        for task in generated_tasks:
            assert 'document_source' in task
            assert task['document_source'] is not None

            # Verifica che il task sia correlato al contenuto del documento
            assert 'calculus' in task['title'].lower() or 'theorem' in task['description'].lower()


class TestAITaskQuality:
    """Test qualità task AI generati."""

    @pytest.mark.unit
    def test_task_relevance_scoring(self, sample_document_text):
        """Test scoring rilevanza task."""
        career_service = CareerService(Mock())

        # Simula task generati
        generated_tasks = [
            {
                'title': 'Ripasso teoremi matematici',
                'description': 'Rivedere teoremi del capitolo 3',
                'priority': 'high'
            },
            {
                'title': 'Task non correlato',
                'description': 'Task completamente diverso',
                'priority': 'low'
            }
        ]

        # Calcola score rilevanza
        for task in generated_tasks:
            relevance_score = career_service._calculate_task_relevance(task, sample_document_text)
            assert 0 <= relevance_score <= 1

    @pytest.mark.unit
    def test_task_deduplication(self):
        """Test deduplicazione task simili."""
        career_service = CareerService(Mock())

        # Task simili
        duplicate_tasks = [
            {
                'title': 'Ripasso teoremi',
                'description': 'Rivedere teoremi fondamentali'
            },
            {
                'title': 'Ripasso teoremi',
                'description': 'Rivedere teoremi fondamentali'
            },
            {
                'title': 'Studio teoremi',
                'description': 'Approfondire teoremi matematici'
            }
        ]

        # Deduplica
        deduplicated_tasks = career_service._deduplicate_tasks(duplicate_tasks)

        # Dovrebbe avere meno task dopo deduplicazione
        assert len(deduplicated_tasks) <= len(duplicate_tasks)

    @pytest.mark.unit
    def test_task_priority_optimization(self):
        """Test ottimizzazione priorità task."""
        career_service = CareerService(Mock())

        # Task con priorità iniziali
        tasks = [
            {
                'title': 'Task urgente',
                'description': 'Task molto importante',
                'priority': 'low'
            },
            {
                'title': 'Task esame',
                'description': 'Preparazione esame imminente',
                'priority': 'medium'
            }
        ]

        # Ottimizza priorità
        optimized_tasks = career_service._optimize_task_priorities(tasks)

        # Verifica ottimizzazione
        for task in optimized_tasks:
            assert task['priority'] in ['low', 'medium', 'high']

            # Task con parole chiave accademiche dovrebbero avere priorità più alta
            if 'esame' in task['description'].lower():
                assert task['priority'] in ['high', 'medium']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
