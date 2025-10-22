# Architettura Target - Archivista AI v2.5
## Documento di Progettazione Architetturale (Giorno 3-4)

### 🎯 Visione Architetturale

**Da:** Architettura monolitica con file di 1000-2700 righe
**A:** Architettura modulare con responsabilità chiare e confini definiti

### 🏗️ Architettura Target Proposta

```
src/
├── config/                 # ✅ Configuration Management
│   ├── __init__.py
│   ├── settings.py        # Configurazione principale
│   ├── database.py        # Configurazione database
│   ├── ai.py             # Configurazione AI/LLM
│   └── validation.py     # Validazione configurazione
│
├── database/              # ✅ Data Access Layer (DAL)
│   ├── __init__.py
│   ├── models/           # Modelli dati (Pydantic)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── course.py
│   │   └── base.py
│   ├── repositories/     # Repository Pattern
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── document_repository.py
│   │   ├── course_repository.py
│   │   └── base_repository.py
│   ├── migrations/       # Migrazioni database
│   │   ├── __init__.py
│   │   ├── migration_001.py
│   │   └── manager.py
│   └── connection.py     # Gestione connessioni
│
├── services/             # ✅ Business Logic Layer
│   ├── __init__.py
│   ├── archive/         # Servizio Archivio
│   │   ├── __init__.py
│   │   ├── archive_service.py
│   │   ├── document_processor.py
│   │   └── search_engine.py
│   ├── chat/           # Servizio Chat
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   └── conversation_manager.py
│   ├── editor/         # Servizio Editor
│   │   ├── __init__.py
│   │   ├── editor_service.py
│   │   └── content_manager.py
│   ├── auth/           # Servizio Autenticazione
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── session_manager.py
│   └── ai/             # Servizio AI Centralizzato
│       ├── __init__.py
│       ├── ai_service.py
│       ├── embeddings.py
│       └── knowledge_graph.py
│
├── core/                # ✅ Core System
│   ├── __init__.py
│   ├── errors/         # Gestione Errori Unificata
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   ├── error_types.py
│   │   └── error_responses.py
│   ├── events/         # Event System
│   │   ├── __init__.py
│   │   ├── event_bus.py
│   │   └── event_types.py
│   └── utils/          # Utilities Core
│       ├── __init__.py
│       ├── logging.py
│       └── validation.py
│
├── api/                # ✅ API Layer (Futuro)
│   ├── __init__.py
│   ├── routes/        # Endpoint API
│   └── middleware/    # Middleware API
│
└── ui/                 # ✅ UI Layer
    ├── __init__.py
    ├── components/     # Componenti riutilizzabili
    │   ├── __init__.py
    │   ├── navigation.py
    │   ├── forms.py
    │   └── cards.py
    ├── pages/         # Page implementations
    │   ├── __init__.py
    │   ├── chat_page.py
    │   ├── archive_page.py
    │   └── editor_page.py
    └── assets/        # CSS, JS, immagini
```

### 🔌 Interfacce dei Moduli Core

#### 1. Archive Service Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class DocumentResult:
    success: bool
    document_id: str
    message: str
    metadata: Dict[str, Any]

@dataclass
class SearchQuery:
    text: str
    filters: Dict[str, Any]
    limit: int = 10

class IArchiveService(ABC):
    """Interfaccia per il servizio di archiviazione documenti"""

    @abstractmethod
    async def process_document(self, file_path: str) -> DocumentResult:
        """Processa un singolo documento con gestione completa degli errori"""
        pass

    @abstractmethod
    async def search_documents(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """Ricerca documenti con filtraggio avanzato"""
        pass

    @abstractmethod
    async def organize_documents(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Organizza i documenti secondo i criteri specificati"""
        pass

    @abstractmethod
    async def batch_operation(self, operation: str, document_ids: List[str]) -> Dict[str, Any]:
        """Esegue operazioni batch su documenti multipli"""
        pass
```

#### 2. Chat Service Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class ChatSession:
    session_id: str
    user_id: str
    title: str
    messages: List[ChatMessage]

class IChatService(ABC):
    """Interfaccia per il servizio chat"""

    @abstractmethod
    async def create_session(self, user_id: str, title: str) -> str:
        """Crea una nuova sessione chat"""
        pass

    @abstractmethod
    async def send_message(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Invia un messaggio e restituisce risposta in streaming"""
        pass

    @abstractmethod
    async def get_session_history(self, session_id: str) -> ChatSession:
        """Recupera la cronologia di una sessione"""
        pass

    @abstractmethod
    async def search_conversations(self, user_id: str, query: str) -> List[ChatSession]:
        """Cerca nelle conversazioni dell'utente"""
        pass
```

#### 3. Authentication Service Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class User:
    id: str
    username: str
    email: str
    preferences: Dict[str, Any]
    created_at: str

@dataclass
class AuthResult:
    success: bool
    user: Optional[User]
    token: Optional[str]
    message: str

class IAuthService(ABC):
    """Interfaccia per il servizio di autenticazione"""

    @abstractmethod
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Autentica un utente"""
        pass

    @abstractmethod
    async def create_user(self, username: str, email: str, password: str) -> AuthResult:
        """Crea un nuovo utente"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Recupera utente per ID"""
        pass

    @abstractmethod
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Aggiorna preferenze utente"""
        pass
```

#### 4. AI Service Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AIQuery:
    text: str
    context: List[str]
    model: str
    temperature: float = 0.7

@dataclass
class AIResponse:
    text: str
    confidence: float
    sources: List[str]
    metadata: Dict[str, Any]

class IAIService(ABC):
    """Interfaccia per il servizio AI centralizzato"""

    @abstractmethod
    async def query(self, ai_query: AIQuery) -> AIResponse:
        """Esegue una query AI generica"""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings per testi"""
        pass

    @abstractmethod
    async def update_knowledge_graph(self, documents: List[str]) -> bool:
        """Aggiorna il grafo della conoscenza"""
        pass

    @abstractmethod
    async def get_similar_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Trova documenti simili a una query"""
        pass
```

### 🗃️ Data Access Layer (DAL) Interfaces

#### Repository Pattern Interfaces

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar

T = TypeVar('T')

class IBaseRepository(Generic[T], ABC):
    """Interfaccia base per tutti i repository"""

    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Recupera entità per ID"""
        pass

    @abstractmethod
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Recupera tutte le entità con filtri opzionali"""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Crea nuova entità"""
        pass

    @abstractmethod
    async def update(self, id: Any, entity: T) -> bool:
        """Aggiorna entità esistente"""
        pass

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Elimina entità"""
        pass

class IDocumentRepository(IBaseRepository[Document]):
    """Repository specializzato per documenti"""

    @abstractmethod
    async def search_by_content(self, query: str) -> List[Document]:
        """Cerca documenti per contenuto"""
        pass

    @abstractmethod
    async def get_by_category(self, category: str) -> List[Document]:
        """Recupera documenti per categoria"""
        pass

    @abstractmethod
    async def get_recent(self, user_id: str, limit: int = 10) -> List[Document]:
        """Recupera documenti recenti per utente"""
        pass
```

### ⚙️ Configuration Management Strategy

#### Configurazione Centralizzata

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int
    timeout: int
    retry_attempts: int

@dataclass
class AIConfig:
    model_name: str
    temperature: float
    max_tokens: int
    api_key: str

@dataclass
class AppConfig:
    database: DatabaseConfig
    ai: AIConfig
    ui: Dict[str, Any]
    logging: Dict[str, Any]

class IConfigManager(ABC):
    """Interfaccia per gestione configurazione"""

    @abstractmethod
    def get_config(self) -> AppConfig:
        """Restituisce configurazione completa"""
        pass

    @abstractmethod
    def reload_config(self) -> bool:
        """Ricarica configurazione da fonti esterne"""
        pass

    @abstractmethod
    def validate_config(self) -> List[str]:
        """Valida configurazione e restituisce errori"""
        pass
```

### 🚨 Error Handling Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    VALIDATION = "validation"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    AI_SERVICE = "ai_service"
    AUTHENTICATION = "authentication"
    NETWORK = "network"

@dataclass
class ErrorContext:
    user_id: Optional[str]
    operation: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class ErrorResult:
    error_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    stack_trace: Optional[str]

class IErrorHandler(ABC):
    """Interfaccia per gestione errori unificata"""

    @abstractmethod
    async def handle_error(self, error: Exception, context: ErrorContext) -> ErrorResult:
        """Gestisce e classifica errori in modo coerente"""
        pass

    @abstractmethod
    async def create_error_response(self, error: ErrorResult) -> Dict[str, Any]:
        """Crea risposta di errore standardizzata"""
        pass

    @abstractmethod
    async def log_error(self, error: ErrorResult) -> None:
        """Logga errore con contesto e tracciamento appropriati"""
        pass

    @abstractmethod
    async def should_retry(self, error: ErrorResult) -> bool:
        """Determina se l'operazione dovrebbe essere ritentata"""
        pass
```

### 🔄 Dependency Injection Strategy

#### Container IoC (Inversion of Control)

```python
from typing import Dict, Any, Type, TypeVar
from abc import ABC, abstractmethod

T = TypeVar('T')

class IServiceContainer(ABC):
    """Container per Dependency Injection"""

    @abstractmethod
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Registra implementazione singleton"""
        pass

    @abstractmethod
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Registra implementazione transient"""
        pass

    @abstractmethod
    def get_service(self, interface: Type[T]) -> T:
        """Risolve servizio per interfaccia"""
        pass

# Esempio di utilizzo
class ServiceContainer(IServiceContainer):
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._transients: Dict[Type, Type] = {}

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        self._singletons[interface] = implementation()

    def get_service(self, interface: Type[T]) -> T:
        if interface in self._singletons:
            return self._singletons[interface]
        elif interface in self._transients:
            return self._transients[interface]()
        else:
            raise ValueError(f"Servizio non registrato: {interface}")
```

### 📡 Event-Driven Communication Pattern

#### Event Bus Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')

@dataclass
class Event:
    event_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    source: str

@dataclass
class EventHandler:
    handler_id: str
    event_type: str
    callback: Callable[[Event], None]

class IEventBus(ABC):
    """Interfaccia per bus eventi"""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Pubblica evento nel bus"""
        pass

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Sottoscrive handler per tipo evento"""
        pass

    @abstractmethod
    async def unsubscribe(self, handler_id: str) -> None:
        """Rimuove sottoscrizione handler"""
        pass
```

### 🗄️ Piano Consolidamento Schema Database

#### Schema Unificato Target

```sql
-- Users table (enhanced)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    preferences JSON,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Projects table (NEW - Central project management)
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    is_default BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User projects association (NEW - Multi-project access)
CREATE TABLE user_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    project_id TEXT REFERENCES projects(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, project_id)
);

-- Documents table (consolidated)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    file_name VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500),
    content_hash VARCHAR(64),
    file_size INTEGER,
    mime_type VARCHAR(100),
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Categories table (hierarchical)
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    category_type VARCHAR(50) DEFAULT 'standard',
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Document categories (many-to-many)
CREATE TABLE document_categories (
    document_id INTEGER REFERENCES documents(id),
    category_id INTEGER REFERENCES categories(id),
    confidence_score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, category_id)
);

-- Courses table (enhanced)
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    course_name VARCHAR(255) NOT NULL,
    course_code VARCHAR(50),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Lectures table (enhanced)
CREATE TABLE lectures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER REFERENCES courses(id),
    lecture_title VARCHAR(255) NOT NULL,
    lecture_date DATE,
    description TEXT,
    keywords JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Materials table (enhanced)
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER REFERENCES lectures(id),
    course_id INTEGER REFERENCES courses(id),
    document_id INTEGER REFERENCES documents(id),
    material_type VARCHAR(50),
    description TEXT,
    processed_at DATETIME
);

-- Tasks table (enhanced)
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    course_id INTEGER REFERENCES courses(id),
    lecture_id INTEGER REFERENCES lectures(id),
    task_title VARCHAR(255) NOT NULL,
    task_description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    task_type VARCHAR(50) DEFAULT 'general',
    due_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table (enhanced)
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    session_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table (enhanced)
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES chat_sessions(id),
    message_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Concept entities table (enhanced)
CREATE TABLE concept_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    entity_description TEXT,
    source_file_name VARCHAR(255),
    confidence_score FLOAT DEFAULT 0.5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Concept relationships table (enhanced)
CREATE TABLE concept_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    source_entity_id INTEGER REFERENCES concept_entities(id),
    target_entity_id INTEGER REFERENCES concept_entities(id),
    relationship_type VARCHAR(100) NOT NULL,
    relationship_description TEXT,
    confidence_score FLOAT DEFAULT 0.5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User XP table (enhanced)
CREATE TABLE user_xp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    xp_amount INTEGER NOT NULL,
    xp_source VARCHAR(100) NOT NULL,
    xp_description TEXT,
    source_id VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User achievements table (enhanced)
CREATE TABLE user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    achievement_type VARCHAR(100) NOT NULL,
    achievement_title VARCHAR(255) NOT NULL,
    achievement_description TEXT,
    earned_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Study sessions table (enhanced)
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    session_start DATETIME NOT NULL,
    session_end DATETIME,
    course_id INTEGER REFERENCES courses(id),
    duration_minutes INTEGER,
    topics_covered JSON,
    notes TEXT,
    productivity_rating INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User activity table (enhanced)
CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    action_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(100),
    target_id VARCHAR(100),
    metadata JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100)
);

-- Document processing status table (enhanced)
CREATE TABLE document_processing_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    file_name VARCHAR(255) NOT NULL,
    processing_state VARCHAR(50) DEFAULT 'pending',
    processing_stage VARCHAR(100),
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_name)
);

-- Processing error log table (enhanced)
CREATE TABLE processing_error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    file_name VARCHAR(255),
    error_category VARCHAR(100),
    error_type VARCHAR(100),
    error_message TEXT NOT NULL,
    error_details JSON,
    severity VARCHAR(20) DEFAULT 'medium',
    resolved BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Processing metrics table (enhanced)
CREATE TABLE processing_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Quarantine files table (enhanced)
CREATE TABLE quarantine_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    file_name VARCHAR(255) NOT NULL,
    original_path VARCHAR(500),
    quarantine_reason TEXT NOT NULL,
    error_details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);

-- Bayesian evidence table (enhanced)
CREATE TABLE bayesian_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    entity_id INTEGER REFERENCES concept_entities(id),
    evidence_type VARCHAR(100) NOT NULL,
    evidence_data JSON NOT NULL,
    confidence_weight FLOAT DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 📊 Strategia di Migrazione

#### Fasi di Migrazione

1. **Fase 1: Backup e Setup**
   - Creare backup completo database esistente
   - Creare nuova tabella `projects` con progetto default
   - Aggiungere colonna `project_id` a tutte le tabelle esistenti

2. **Fase 2: Migrazione Dati**
   - Associare utenti esistenti al progetto default
   - Migrare relazioni esistenti preservando integrità
   - Validare consistenza dati dopo migrazione

3. **Fase 3: Ottimizzazioni**
   - Creare indici per performance
   - Rimuovere colonne obsolete
   - Implementare pulizia automatica log

#### Script di Migrazione

```python
class MigrationManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations = []

    async def migrate_database(self) -> bool:
        """Esegue migrazione completa"""
        try:
            # 1. Backup
            await self.create_backup()

            # 2. Crea progetto default
            await self.create_default_project()

            # 3. Migrazione strutturale
            await self.migrate_schema()

            # 4. Migrazione dati
            await self.migrate_data()

            # 5. Validazione
            await self.validate_migration()

            return True
        except Exception as e:
            await self.rollback_migration()
            raise
```

### 🎯 Benefici Architetturali

#### Miglioramenti Attesi

1. **Manutenibilità** 🔧
   - File di massimo 300-400 righe
   - Responsabilità chiaramente separate
   - Testing unitario facilitato

2. **Scalabilità** 📈
   - Moduli indipendenti
   - Facile aggiunta nuove funzionalità
   - Performance ottimizzate

3. **Affidabilità** 🛡️
   - Error handling centralizzato
   - Logging strutturato
   - Recovery automatico

4. **Testabilità** ✅
   - Dependency injection per mock facili
   - Interfacce chiare per testing
   - Separazione logica/UI

5. **Evolutività** 🚀
   - Architettura plugin-based
   - API-first design
   - Event-driven communication

### 📋 Prossimi Passi Implementativi

#### Giorno 5-7: Setup Ambiente Sviluppo
1. **Configurazione Tooling**
   - Black per formattazione codice
   - Flake8 + mypy per linting
   - Pre-commit hooks
   - Documentazione progetto

2. **Framework Testing**
   - Pytest configurazione
   - Fixture e utility test
   - Pattern testing per moduli
   - Pipeline CI/CD

3. **Documentazione Standard**
   - Standard codifica definiti
   - Template documentazione
   - Guide sviluppo

---

*Documento di Architettura Target - Generated $(date)*
*Basato su analisi stato attuale e requisiti progetto*
