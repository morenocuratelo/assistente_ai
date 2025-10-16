# Documentazione Testing - Archivista AI v2.5

## 📋 Panoramica del Sistema di Testing

Questa documentazione descrive la strategia di testing completa per il progetto Archivista AI, inclusi i tipi di test, le convenzioni e le procedure.

## 🏗️ Strategia di Testing

### Tipi di Test

#### 1. Unit Tests
**Scopo**: Testare singole unità di codice in isolamento
**Copertura**: Funzioni, metodi, classi individuali
**Tools**: pytest, unittest.mock
**Marcatore**: `@pytest.mark.unit`

```python
@pytest.mark.unit
def test_single_function():
    """Test singola funzione con mock delle dipendenze."""
    pass
```

#### 2. Integration Tests
**Scopo**: Testare interazioni tra moduli
**Copertura**: Integrazione tra servizi, database operations
**Tools**: pytest, test database in-memory
**Marcatore**: `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_service_interaction(in_memory_db):
    """Test interazione tra servizi con database reale."""
    pass
```

#### 3. End-to-End Tests
**Scopo**: Testare flussi completi utente
**Copertura**: User journey complete
**Tools**: pytest, selenium/playwright (futuro)
**Marcatore**: `@pytest.mark.e2e`

#### 4. Performance Tests
**Scopo**: Validare performance requirements
**Copertura**: Tempi di risposta, throughput
**Tools**: pytest-benchmark, custom metrics
**Marcatore**: `@pytest.mark.performance`

### Livelli di Testing

```
┌─────────────────────────────────────────┐
│           End-to-End Tests              │ ← User journeys complete
├─────────────────────────────────────────┤
│         Integration Tests               │ ← Interazione moduli
├─────────────────────────────────────────┤
│            Unit Tests                   │ ← Singole unità codice
└─────────────────────────────────────────┘
```

## 🛠️ Configurazione Ambiente Testing

### Dipendenze Testing

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
    "database: Database related tests",
    "ai: AI/ML related tests",
    "ui: UI related tests",
]
```

### Environment Variables per Testing

```bash
export ENVIRONMENT=test
export DEBUG=true
export DATABASE_URL=sqlite:///:memory:
export AI_MODEL=test-model
export LOG_LEVEL=DEBUG
```

## 📁 Struttura Directory Test

```
tests/
├── conftest.py                    # Configuration globale pytest
├── test_unit_core.py             # Test unità core
├── test_unit_services/           # Test unità servizi
│   ├── test_archive_service.py
│   ├── test_chat_service.py
│   ├── test_auth_service.py
│   └── test_ai_service.py
├── test_integration/             # Test integrazione
│   ├── test_database_integration.py
│   ├── test_service_integration.py
│   └── test_api_integration.py
├── test_e2e/                    # Test end-to-end
│   ├── test_user_journeys.py
│   └── test_critical_paths.py
├── test_performance/             # Test performance
│   ├── test_benchmarks.py
│   └── test_load_tests.py
├── fixtures/                    # Fixture dati test
│   ├── sample_documents/
│   ├── test_users.json
│   └── mock_responses/
└── utils/                       # Utilities testing
    ├── test_helpers.py
    └── assertions.py
```

## 🧪 Pattern di Testing

### Arrange-Act-Assert (AAA)

```python
@pytest.mark.unit
def test_document_processing():
    """Test processamento documento usando pattern AAA."""

    # Arrange - Prepara dati e mock
    mock_config = Mock()
    mock_config.ai.model = "test-model"

    processor = DocumentProcessor(mock_config)
    test_file = "test.pdf"

    # Act - Esegui operazione da testare
    with patch.object(processor, '_extract_text') as mock_extract:
        mock_extract.return_value = "Extracted text"

        result = processor.process_document(test_file)

    # Assert - Verifica risultati
    assert result.success is True
    assert result.document_id is not None
    mock_extract.assert_called_once_with(test_file)
```

### Given-When-Then (BDD Style)

```python
@pytest.mark.integration
def test_user_authentication_flow():
    """Test flusso autenticazione utente."""

    # Given - Setup contesto
    user_data = {"username": "testuser", "password": "password123"}
    auth_service = AuthenticationService(test_db)

    # When - Esegui azione
    result = auth_service.authenticate(user_data["username"], user_data["password"])

    # Then - Verifica outcome
    assert result.success is True
    assert result.user.username == user_data["username"]
    assert result.token is not None
```

### Table-Driven Tests

```python
@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid-email", False),
    ("@domain.com", False),
    ("user@", False),
    ("user.name+tag@domain.co.uk", True),
])
def test_email_validation(input, expected):
    """Test validazione email con dati tabellari."""
    result = validate_email(input)
    assert result == expected
```

## 🎯 Fixture e Test Data

### Fixture Scope

```python
# Session scope - Setup una volta per tutta la sessione
@pytest.fixture(scope="session")
def test_database():
    """Database di test per tutta la sessione."""
    # Setup
    yield db
    # Teardown

# Module scope - Setup una volta per modulo
@pytest.fixture(scope="module")
def sample_data():
    """Dati di esempio per modulo test."""
    # Setup
    yield data
    # Teardown

# Function scope - Setup per ogni funzione test
@pytest.fixture
def mock_service():
    """Mock service per singolo test."""
    return Mock()
```

### Test Data Factory

```python
class TestDataFactory:
    """Factory per generazione dati test."""

    @staticmethod
    def create_user(overrides=None):
        """Crea dati utente test."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "preferences": {"theme": "light"}
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_document(overrides=None):
        """Crea dati documento test."""
        data = {
            "file_name": "test.pdf",
            "title": "Test Document",
            "content": "Sample content"
        }
        if overrides:
            data.update(overrides)
        return data
```

## 🚨 Mock e Stubbing

### Mock Esterni

```python
@pytest.mark.unit
def test_external_api_call():
    """Test chiamata API esterna con mock."""

    with patch('requests.post') as mock_post:
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        # Esegui codice che chiama API esterna
        result = call_external_api()

        # Verifica
        assert result["success"] is True
        mock_post.assert_called_once()
```

### Mock Database

```python
@pytest.mark.unit
def test_repository_with_mock_db():
    """Test repository con database mockato."""

    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}

    with patch('sqlite3.connect', return_value=mock_db):
        repo = DocumentRepository("test.db")
        result = repo.get_by_id(1)

        assert result["id"] == 1
        assert result["name"] == "test"
```

## 📊 Coverage e Quality Metrics

### Coverage Configuration

```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

### Quality Gates

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pytest pytest-cov

      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v1
        with:
          file: ./coverage.xml

      - name: Check coverage thresholds
        run: |
          coverage report --fail-under=80
```

## 🔧 Test Utilities

### Custom Assertions

```python
# tests/utils/assertions.py

def assert_document_valid(document):
    """Custom assertion per documenti."""
    assert document.id is not None
    assert document.file_name.endswith('.pdf')
    assert len(document.title) > 0
    assert document.created_at is not None

def assert_user_has_permissions(user, permissions):
    """Custom assertion per permessi utente."""
    for permission in permissions:
        assert permission in user.permissions
```

### Test Helpers

```python
# tests/utils/test_helpers.py

def create_test_file(content: str, filename: str) -> Path:
    """Crea file test con contenuto specificato."""
    path = Path(filename)
    path.write_text(content)
    return path

def wait_for_condition(condition_func, timeout=5):
    """Attende condizione per massimo timeout secondi."""
    import time
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(0.1)
    return False
```

## 🚀 Performance Testing

### Benchmark Tests

```python
@pytest.mark.performance
def test_document_processing_benchmark(benchmark, sample_document):
    """Benchmark processamento documenti."""

    def process_doc():
        return document_processor.process(sample_document)

    # Esegui benchmark
    result = benchmark(process_doc)

    # Verifica performance
    assert result < 2.0  # Deve completare entro 2 secondi

@pytest.mark.performance
def test_database_query_performance(benchmark, in_memory_db):
    """Benchmark query database."""

    def query_db():
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        return cursor.fetchone()

    result = benchmark(query_db)
    assert result < 0.1  # Query deve essere veloce
```

### Load Testing

```python
@pytest.mark.slow
@pytest.mark.performance
def test_high_load_processing():
    """Test processamento sotto carico elevato."""

    # Crea molti documenti test
    documents = [create_large_document(i) for i in range(100)]

    start_time = time.time()

    # Processa tutti i documenti
    results = []
    for doc in documents:
        result = document_processor.process(doc)
        results.append(result)

    end_time = time.time()

    # Verifica performance
    total_time = end_time - start_time
    avg_time_per_doc = total_time / len(documents)

    assert avg_time_per_doc < 1.0  # Max 1 secondo per documento
    assert all(r.success for r in results)  # Tutti devono avere successo
```

## 🗄️ Database Testing

### In-Memory Database

```python
@pytest.fixture
def test_db():
    """Database in-memory per test veloci."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Crea schema test
    create_tables(conn)
    populate_test_data(conn)

    yield conn
    conn.close()

def test_database_operations(test_db):
    """Test operazioni database."""

    # Test operazioni CRUD
    user = create_user(test_db, "testuser")
    assert user["id"] is not None

    retrieved = get_user(test_db, user["id"])
    assert retrieved["username"] == "testuser"
```

### Transaction Testing

```python
@pytest.mark.database
def test_transaction_rollback():
    """Test rollback transazioni."""

    with database.transaction() as tx:
        # Operazioni che potrebbero fallire
        user_id = create_user(tx.connection, "testuser")

        # Simula errore
        if some_condition:
            raise Exception("Test error")

    # Dopo rollback, dati non dovrebbero esistere
    user = get_user(tx.connection, user_id)
    assert user is None
```

## 🤖 AI/ML Testing

### LLM Testing

```python
@pytest.mark.ai
def test_llm_response_quality(mock_llm):
    """Test qualità risposte LLM."""

    # Setup mock LLM
    mock_llm.complete.return_value = "Questa è una risposta di qualità"

    # Test generazione risposta
    response = ai_service.generate_response("Domanda test")

    assert len(response.text) > 10
    assert response.confidence > 0.5

@pytest.mark.ai
def test_embedding_generation(mock_llm):
    """Test generazione embeddings."""

    texts = ["Test document 1", "Test document 2"]

    with patch.object(ai_service, 'generate_embeddings') as mock_embed:
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

        embeddings = ai_service.generate_embeddings(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) > 0
```

### Knowledge Graph Testing

```python
@pytest.mark.ai
def test_knowledge_graph_update():
    """Test aggiornamento grafo conoscenza."""

    # Crea documenti test
    documents = [
        {"content": "Python è un linguaggio di programmazione"},
        {"content": "Machine learning usa algoritmi"}
    ]

    # Test aggiornamento grafo
    success = knowledge_service.update_graph(documents)

    assert success is True

    # Verifica entità estratte
    entities = knowledge_service.get_entities()
    assert len(entities) > 0
```

## 🖥️ UI Testing (Futuro)

### Streamlit Testing

```python
# tests/test_ui_pages.py
import pytest
from streamlit.testing.v1 import AppTest

@pytest.mark.ui
def test_chat_page_rendering():
    """Test rendering pagina chat."""

    # Nota: Richiede streamlit-testing
    at = AppTest("pages/1_Chat.py")

    # Test componenti UI
    assert at.title[0].value == "Chat"
    assert at.button[0].label == "Invia"

@pytest.mark.ui
def test_user_interactions():
    """Test interazioni utente."""

    at = AppTest("pages/2_Archivio.py")

    # Simula input utente
    at.text_input[0].input("test query").run()

    # Verifica risultati
    assert len(at.dataframe) > 0
```

## 📈 Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10']

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics

    - name: Type check with mypy
      run: |
        mypy src

    - name: Test with pytest
      run: |
        pip install pytest pytest-cov
        pytest --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### Quality Checks

```yaml
# .github/workflows/quality.yml
name: Quality Checks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install black isort flake8 mypy bandit interrogate

    - name: Check formatting (black)
      run: black --check src tests

    - name: Check import sorting (isort)
      run: isort --check-only src tests

    - name: Lint with flake8
      run: flake8 src tests

    - name: Type check with mypy
      run: mypy src

    - name: Security check with bandit
      run: bandit -r src -c pyproject.toml

    - name: Docstring coverage with interrogate
      run: interrogate -c pyproject.toml src
```

## 🐛 Debugging Test

### Debug Mode

```python
# pytest.ini
[tool:pytest]
addopts = -ra -q --strict-markers --strict-config
# Aggiungi per debug
# addopts = -ra -q -s --pdb

# Per debug singolo test
pytest tests/test_core.py::TestClass::test_method -s --pdb
```

### Verbose Output

```bash
# Output dettagliato
pytest -v -s

# Mostra fixtures utilizzate
pytest --fixtures

# Mostra markers disponibili
pytest --markers

# Debug mode con output completo
pytest -vv --tb=short
```

## 📋 Checklist Test

### Prima di Committare

- [ ] **Unit test**: Ogni nuova funzione ha test unitario?
- [ ] **Integration test**: Flussi principali hanno test integrazione?
- [ ] **Edge cases**: Casi limite coperti?
- [ ] **Error handling**: Errori gestiti correttamente?
- [ ] **Performance**: Test performance per operazioni critiche?
- [ ] **Coverage**: Coverage > 80% per nuovo codice?
- [ ] **Documentation**: Test documentati?

### Code Review Testing

- [ ] **Test esistenti**: Tutti i test esistenti passano?
- [ ] **Nuovi test**: Test comprensibili e mantenibili?
- [ ] **Mock appropriati**: Mock utilizzati correttamente?
- [ ] **Fixture efficienti**: Fixture non rallentano test?
- [ ] **Nomi descrittivi**: Nomi test auto-esplicativi?

## 🔧 Best Practices

### Test Naming

```python
# ✅ Buono
def test_user_creation_success():
def test_document_processing_with_invalid_file():
def test_authentication_with_wrong_password():

# ❌ Evitare
def test_user():
def test_process():
def test_auth():
```

### Test Organization

```python
class TestUserService:
    """Gruppo di test per UserService."""

    def test_create_user(self):
        """Test creazione utente."""
        pass

    def test_authenticate_user(self):
        """Test autenticazione utente."""
        pass

    def test_update_user_preferences(self):
        """Test aggiornamento preferenze."""
        pass
```

### Test Independence

```python
# ✅ Buono - Test indipendenti
def test_create_user():
    user = create_user("testuser")
    assert user.username == "testuser"

def test_delete_user():
    user = create_user("testuser2")  # Crea nuovo utente
    delete_user(user.id)
    assert get_user(user.id) is None

# ❌ Evitare - Test dipendenti
def test_global_user():
    global test_user
    if not test_user:
        test_user = create_user("global")
    # Usa utente globale
```

## 📊 Metriche e Report

### Coverage Report

```bash
# Genera report copertura
pytest --cov=src --cov-report=html

# Report console
pytest --cov=src --cov-report=term-missing

# Report XML per CI
pytest --cov=src --cov-report=xml
```

### Performance Report

```bash
# Benchmark report
pytest tests/test_performance/ -v --benchmark-only

# Benchmark comparison
pytest-benchmark compare 0001.json 0002.json
```

## 🚨 Error Handling nei Test

### Expected Failures

```python
@pytest.mark.unit
def test_expected_failure():
    """Test che verifica gestione errori."""

    with pytest.raises(DocumentProcessingError) as exc_info:
        processor.process_document("invalid_file.pdf")

    assert "File not found" in str(exc_info.value)
    assert exc_info.value.error_code == "FILE_NOT_FOUND"
```

### Custom Exception Testing

```python
@pytest.mark.unit
def test_custom_exception_context():
    """Test contesto eccezioni custom."""

    try:
        raise DocumentProcessingError(
            "Processing failed",
            "test.pdf",
            context={"user_id": "123", "operation": "test"}
        )
    except DocumentProcessingError as e:
        assert e.error_code == "DOCUMENT_PROCESSING_FAILED"
        assert e.context["user_id"] == "123"
        assert e.file_path == "test.pdf"
```

## 🔄 Test Maintenance

### Refactoring Test

```python
# Prima del refactoring
def test_old_function():
    # Test vecchio codice
    pass

# Dopo il refactoring
@pytest.mark.unit
def test_refactored_function():
    """Test funzione refactored."""
    # Test nuovo codice
    pass

# Mantieni test vecchio fino a completamento migrazione
@pytest.mark.unit
@ pytest.mark.skip(reason="Legacy test - to be removed after migration")
def test_old_function():
    # Test vecchio codice (da rimuovere)
    pass
```

### Test Data Maintenance

```python
# Usa factory per dati consistenti
def test_with_factory_data():
    user_data = TestDataFactory.create_user({"active": True})
    document_data = TestDataFactory.create_document({"public": True})

    # Test logic
    assert user_data["active"] is True
    assert document_data["public"] is True
```

## 📚 Risorse Aggiuntive

### Documentazione Esterna

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Black Code Style](https://black.readthedocs.io/)

### Libri Consigliati

- "Test-Driven Development with Python" by Harry Percival
- "Python Testing with pytest" by Brian Okken
- "Effective Python Testing" by Brett Slatkin

---

*Documento Testing - Versione 2.5 - $(date)*
*Mantenuto dal team QA Archivista AI*
