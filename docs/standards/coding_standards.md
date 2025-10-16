# Standard di Codifica - Archivista AI v2.5

## 📋 Sommario

Questo documento definisce gli standard di codifica per il progetto Archivista AI, garantendo consistenza, manutenibilità e qualità del codice.

## 🏗️ Principi Generali

### Filosofia del Codice

- **Leggibilità prima di tutto**: Il codice deve essere auto-documentante
- **DRY (Don't Repeat Yourself)**: Evitare duplicazioni inutili
- **KISS (Keep It Simple, Stupid)**: Preferire soluzioni semplici
- **YAGNI (You Aren't Gonna Need It)**: Implementare solo ciò che serve
- **SOLID Principles**: Applicare i principi SOLID quando appropriato

### Convenzioni di Nomenclatura

#### Python Files
```python
# ✅ Buono
user_service.py
document_repository.py
ai_config.py

# ❌ Evitare
UserService.py          # PascalCase
document-repo.py        # kebab-case
Document_Repository.py  # snake_case con maiuscole
```

#### Classes
```python
# ✅ Buono
class ArchiveService:
class DocumentRepository:
class AIConfig:

# ❌ Evitare
class archive_service:      # snake_case
class Archive_Service:      # snake_case con underscore
class ARCHIVE_SERVICE:      # UPPER_CASE
```

#### Functions e Methods
```python
# ✅ Buono
def get_user_by_id(user_id: str) -> Optional[User]:
def process_document(file_path: str) -> DocumentResult:
def calculate_confidence_score(text: str) -> float:

# ❌ Evitare
def GetUserById(user_id):           # PascalCase
def processDocument(file_path):     # camelCase
def calculate_confidence_Score():   # snake_case con maiuscole
```

#### Variables e Constants
```python
# ✅ Buono
MAX_RETRY_ATTEMPTS = 3
database_config = DatabaseConfig()
user_id = "user_123"

# ❌ Evitare
maxRetryAttempts = 3        # camelCase
DATABASE_CONFIG = {}        # UPPER_CASE per non costanti
UserId = "user_123"         # PascalCase
```

## 📝 Struttura del Codice

### Organizzazione dei File

```
src/
├── modulename/
│   ├── __init__.py           # Exports pubblici del modulo
│   ├── core.py              # Logica principale
│   ├── models.py            # Data models (Pydantic)
│   ├── repository.py        # Data access layer
│   ├── service.py           # Business logic layer
│   ├── exceptions.py        # Custom exceptions
│   └── tests/               # Test del modulo
│       ├── __init__.py
│       ├── test_core.py
│       └── fixtures.py
```

### Import Organization

```python
# 1. Standard library imports
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

# 2. Third-party imports (in ordine alfabetico)
import streamlit as st
from llama_index.core import VectorStoreIndex

# 3. Local imports (in ordine alfabetico)
from .models import Document, User
from .repository import DocumentRepository
from ..config.settings import AppConfig
```

### Funzione e Classe Structure

```python
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class DocumentResult:
    """Risultato dell'elaborazione di un documento."""
    success: bool
    document_id: str
    message: str
    metadata: Dict[str, str]

class DocumentProcessor:
    """Servizio per l'elaborazione dei documenti."""

    def __init__(self, config: AppConfig) -> None:
        """Inizializza il processore documenti.

        Args:
            config: Configurazione dell'applicazione
        """
        self.config = config
        self._setup_dependencies()

    def process_document(self, file_path: str) -> DocumentResult:
        """Processa un documento.

        Args:
            file_path: Percorso del file da processare

        Returns:
            Risultato dell'elaborazione

        Raises:
            DocumentProcessingError: Se il processamento fallisce
        """
        # Implementation here
        pass

    def _setup_dependencies(self) -> None:
        """Setup interno delle dipendenze."""
        # Private method implementation
        pass
```

## 🔧 Configurazione Sviluppo

### Ambiente Virtuale

```bash
# Creazione ambiente virtuale
python -m venv .venv

# Attivazione (Linux/Mac)
source .venv/bin/activate

# Attivazione (Windows)
.venv\Scripts\activate

# Installazione dipendenze sviluppo
pip install -e ".[dev]"
```

### Pre-commit Hooks

```bash
# Installazione pre-commit
pre-commit install

# Esecuzione manuale
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## 🧪 Testing Standards

### Struttura Test

```python
import pytest
from unittest.mock import Mock, patch

class TestDocumentProcessor:
    """Test suite per DocumentProcessor."""

    def setup_method(self) -> None:
        """Setup eseguito prima di ogni test method."""
        self.config = Mock()
        self.processor = DocumentProcessor(self.config)

    def teardown_method(self) -> None:
        """Cleanup eseguito dopo ogni test method."""
        pass

    @pytest.mark.unit
    def test_process_document_success(self) -> None:
        """Test processamento documento con successo."""
        # Arrange
        file_path = "test_document.pdf"

        # Act
        result = self.processor.process_document(file_path)

        # Assert
        assert result.success is True
        assert result.document_id is not None

    @pytest.mark.integration
    @pytest.mark.slow
    def test_process_document_with_real_file(self) -> None:
        """Test processamento con file reale (lento)."""
        # Test implementation
        pass

    @pytest.mark.database
    def test_process_document_database_error(self) -> None:
        """Test gestione errori database."""
        # Test implementation
        pass
```

### Fixture Pattern

```python
import pytest
from typing import Generator

@pytest.fixture
def sample_document() -> Document:
    """Fixture per documento di test."""
    return Document(
        id="doc_1",
        title="Test Document",
        content="Sample content"
    )

@pytest.fixture
def database_connection() -> Generator[sqlite3.Connection, None, None]:
    """Fixture per connessione database di test."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def setup_and_teardown() -> Generator[None, None]:
    """Fixture automatico per setup/teardown globale."""
    # Setup
    yield
    # Teardown
```

## 🚨 Error Handling

### Custom Exceptions

```python
class ArchivistaError(Exception):
    """Eccezione base per errori Archivista."""

    def __init__(self, message: str, error_code: str, context: Dict[str, Any] = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}

class DocumentProcessingError(ArchivistaError):
    """Errore durante processamento documento."""

    def __init__(self, message: str, file_path: str) -> None:
        super().__init__(
            message,
            error_code="DOCUMENT_PROCESSING_FAILED",
            context={"file_path": file_path}
        )

class DatabaseError(ArchivistaError):
    """Errore operazioni database."""

    def __init__(self, message: str, operation: str) -> None:
        super().__init__(
            message,
            error_code="DATABASE_ERROR",
            context={"operation": operation}
        )
```

### Error Handling Pattern

```python
from typing import Optional
from .exceptions import DocumentProcessingError

def process_document_safe(file_path: str) -> Optional[DocumentResult]:
    """Processa documento con gestione errori completa."""
    try:
        # Operazione principale
        result = process_document_unsafe(file_path)

        # Logging successo
        logger.info(f"Documento processato: {file_path}")

        return result

    except DocumentProcessingError:
        # Rilogging errore specifico
        logger.error(f"Errore processamento documento: {file_path}")
        raise

    except sqlite3.Error as e:
        # Conversione errore database
        logger.error(f"Errore database: {e}")
        raise DatabaseError(f"Database error: {e}", "document_processing")

    except Exception as e:
        # Catch-all con contesto
        logger.error(f"Errore inaspettato: {e}", extra={"file_path": file_path})
        raise DocumentProcessingError(
            f"Errore inaspettato durante processamento: {e}",
            file_path
        )
```

## 📚 Documentazione

### Docstring Format

```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
) -> Dict[str, Any]:
    """Breve descrizione funzione (imperativo).

    Descrizione più dettagliata se necessario.
    Spiega il perché e il come, non il cosa (ovvio dal codice).

    Args:
        param1: Descrizione parametro 1
        param2: Descrizione parametro 2

    Returns:
        Descrizione del valore restituito

    Raises:
        ValueError: Quando parametro non valido
        DatabaseError: Quando errore database

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        'success'
    """
    pass
```

### Type Hints

```python
from typing import Dict, List, Optional, Union, Any
from typing import Protocol

# ✅ Buono
def get_user(user_id: str) -> Optional[User]:
def process_documents(documents: List[Document]) -> List[DocumentResult]:
def configure_ai(settings: Dict[str, Any]) -> None:

# ✅ Buono - Generic types
def find_by_id(items: List[T], id: str) -> Optional[T]:
def merge_dicts(base: Dict[K, V], updates: Dict[K, V]) -> Dict[K, V]:

# ✅ Buono - Protocol per duck typing
class DocumentProcessor(Protocol):
    def process(self, document: Document) -> DocumentResult: ...
```

## 🔒 Security Standards

### Input Validation

```python
from pydantic import BaseModel, validator
import re

class DocumentUploadRequest(BaseModel):
    """Schema validazione upload documento."""
    file_name: str
    file_size: int
    mime_type: str

    @validator('file_name')
    def validate_file_name(cls, v: str) -> str:
        # Controlli sicurezza
        if not v:
            raise ValueError("Nome file obbligatorio")

        if len(v) > 255:
            raise ValueError("Nome file troppo lungo")

        # Pattern pericolosi
        dangerous_patterns = ['../', '..\\', '<script', 'javascript:']
        for pattern in dangerous_patterns:
            if pattern in v.lower():
                raise ValueError("Nome file non valido")

        return v

    @validator('file_size')
    def validate_file_size(cls, v: int) -> int:
        MAX_SIZE = 100 * 1024 * 1024  # 100MB
        if v > MAX_SIZE:
            raise ValueError("File troppo grande")
        return v
```

### Database Security

```python
# ✅ Buono - Parameterized queries
def get_user_by_id(user_id: str) -> Optional[User]:
    query = "SELECT * FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))  # Parametrized
    return cursor.fetchone()

# ❌ Evitare - SQL injection vulnerable
def get_user_unsafe(user_id: str) -> Optional[User]:
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # Vulnerabile!
    cursor.execute(query)
    return cursor.fetchone()
```

## 🚀 Performance Standards

### Database Optimization

```python
# ✅ Buono - Prepared statements
PREPARED_QUERIES = {
    'get_user': 'SELECT * FROM users WHERE id = ?',
    'get_documents': 'SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC',
}

def get_user_optimized(user_id: str) -> Optional[User]:
    cursor = self.connection.cursor()
    cursor.execute(PREPARED_QUERIES['get_user'], (user_id,))
    return cursor.fetchone()

# ✅ Buono - Connection pooling
class DatabaseManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None
        self._init_pool()

    def _init_pool(self) -> None:
        # Inizializza connection pool
        pass

    def get_connection(self) -> sqlite3.Connection:
        return self._pool.get_connection()
```

### Async/Await Pattern

```python
import asyncio
from typing import AsyncGenerator

class AsyncDocumentProcessor:
    """Processore documenti asincrono."""

    async def process_documents_async(
        self,
        file_paths: List[str]
    ) -> AsyncGenerator[DocumentResult, None]:
        """Processa documenti in modo asincrono."""

        # Crea tasks per processamento parallelo
        tasks = [
            self._process_single_document(file_path)
            for file_path in file_paths
        ]

        # Esegui processamento parallelo
        for task in asyncio.as_completed(tasks):
            result = await task
            yield result

    async def _process_single_document(self, file_path: str) -> DocumentResult:
        """Processa singolo documento."""
        # Implementatione asincrona
        pass
```

## 🔍 Code Quality Metrics

### Target Metrics

| Metrica | Target | Descrizione |
|---------|--------|-------------|
| Cyclomatic Complexity | < 10 | Complessità ciclomatica per funzione |
| Line Length | ≤ 88 | Lunghezza massima riga |
| Test Coverage | ≥ 80% | Copertura test minima |
| Docstring Coverage | ≥ 90% | Copertura documentazione |
| Technical Debt Ratio | < 10% | Rapporto debito tecnico |

### Code Smells da Evitare

1. **Long Method** (> 20 righe senza ragione)
2. **Large Class** (> 300 righe)
3. **Long Parameter List** (> 7 parametri)
4. **Duplicate Code** (estratto con funzione/metodo)
5. **Complex Conditional** (deeply nested if/else)
6. **Dead Code** (codice non utilizzato)
7. **Magic Numbers** (costanti senza nome)
8. **Global State** (variabili globali)

## 📋 Checklist Code Review

### Prima di Submit

- [ ] **Funzionalità**: Il codice implementa ciò che dovrebbe?
- [ ] **Errori**: Gestione errori completa e appropriata?
- [ ] **Test**: Test adeguati presenti e passanti?
- [ ] **Documentazione**: Docstring complete e accurate?
- [ ] **Type Hints**: Type hints presenti e corretti?
- [ ] **Performance**: Nessun collo di bottiglia evidente?
- [ ] **Security**: Input validato e sicuro?
- [ ] **Standards**: Codice conforme agli standard?

### Durante Review

- [ ] **Leggibilità**: Codice facile da leggere e capire?
- [ ] **Manutenibilità**: Facile da modificare e estendere?
- [ ] **Consistenza**: Stile coerente con resto codebase?
- [ ] **Design**: Design pattern appropriati utilizzati?
- [ ] **Testing**: Test sufficienti per coprire edge cases?

## 🛠️ Tool Configuration

### Black Configuration

```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310']
include = '\.pyi?$'
exclude = '''
/(
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### MyPy Configuration

```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true
```

---

*Documento Standard Codifica - Versione 2.5 - $(date)*
*Mantenuto dal team di sviluppo Archivista AI*
