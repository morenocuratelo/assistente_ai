# Analisi Dipendenze Database - Fase 0

## 📊 Analisi dello Stato Attuale

Questa analisi documenta tutte le interazioni dirette con il database SQLite per preparare la creazione del Data Access Layer centralizzato.

### 🔍 **File Analizzati**

#### 1. **file_utils.py** (81KB, 2000+ righe)
**Operazioni Database Identificate:**

**Tabella `papers`:**
- `get_papers_dataframe()` - SELECT * completo
- `delete_paper(file_name)` - DELETE con JOIN complessa
- `update_paper_metadata()` - UPDATE dinamico
- `cleanup_missing_files()` - DELETE pulizia riferimenti
- `get_archive_tree()` - SELECT complessa con JOIN

**Tabella `users`:**
- `create_user()` - INSERT con hash password
- `authenticate_user()` - SELECT con verifica password
- `get_user_by_id()` - SELECT singolo utente
- `check_first_time_user()` - SELECT stato nuovo utente
- `mark_user_not_new()` - UPDATE stato utente

**Tabella `chat_sessions` & `chat_messages`:**
- `create_chat_session()` - INSERT sessione
- `get_user_chat_sessions()` - SELECT sessioni utente
- `save_chat_message()` - INSERT messaggio + UPDATE sessione
- `get_chat_messages()` - SELECT messaggi sessione
- `get_user_memory_summary()` - Query complessa memoria conversazionale

**Tabelle Accademiche (`courses`, `lectures`, `materials`, `tasks`):**
- `create_course()`, `get_user_courses()`, `update_course()`, `delete_course()`
- `create_lecture()`, `get_course_lectures()`, `update_lecture()`
- `create_material()`, `get_materials_for_lecture()`
- `create_task()`, `get_user_tasks()`, `update_task()`, `delete_task()`

**Tabelle Knowledge Graph (`concept_entities`, `concept_relationships`):**
- `create_concept_entity()`, `create_concept_relationship()`
- `get_user_knowledge_graph()`, `get_entity_neighbors()`

**Tabelle Gamification (`user_xp`, `user_achievements`, `study_sessions`):**
- `award_xp()`, `get_user_total_xp()`, `get_user_xp_history()`
- `check_and_award_achievements()`, `get_user_achievements()`
- `start_study_session()`, `end_study_session()`, `get_user_study_sessions()`

**Tabelle Activity Tracking (`user_activity`):**
- `record_user_activity()`, `get_recent_documents()`, `get_recent_uploads()`
- `get_user_activity_summary()`, `get_most_accessed_documents()`

**Funzioni Planning (`study_sessions`):**
- `create_planned_study_session()`, `get_today_planned_sessions()`
- `generate_study_schedule()`, `implement_generated_schedule()`

#### 2. **main.py** (40KB, 1500+ righe)
**Operazioni Database Identificate:**

**Accesso tramite file_utils:**
- `get_papers_dataframe()` - Caricamento documenti
- `get_user_courses()`, `get_course_lectures()` - Dati accademici
- `get_user_tasks()` - Attività utente
- `get_recent_documents()`, `get_recent_uploads()` - Contenuto recente
- `get_user_activity_summary()` - Statistiche attività
- `check_first_time_user()`, `mark_user_not_new()` - Stato utente

**Query dirette:**
- Utilizzo funzioni da file_utils per operazioni complesse

#### 3. **pages/1_Chat.py** (17KB, 500+ righe)
**Operazioni Database Identificate:**

**Chat persistence:**
- `get_user_chat_sessions()` - Caricamento sessioni esistenti
- `create_chat_session()` - Creazione nuova sessione
- `get_chat_messages()` - Caricamento messaggi sessione
- `save_chat_message()` - Salvataggio messaggi
- `get_user_memory_summary()` - Memoria conversazionale

#### 4. **pages/2_Archivio.py** (15KB, 400+ righe)
**Operazioni Database Identificate:**

**Document management:**
- `get_papers_dataframe()` - Caricamento documenti
- `get_archive_tree()` - Struttura archivio
- Utilizzo funzioni batch da batch_operations.py

#### 5. **pages/3_Editor.py** (8KB, 200+ righe)
**Operazioni Database Identificate:**

**Editor functionality:**
- `get_papers_dataframe()` - Caricamento documenti
- `update_paper_metadata()` - Salvataggio modifiche anteprima

#### 6. **pages/5_Carriera.py** (15KB, 400+ righe)
**Operazioni Database Identificate:**

**Academic management:**
- `get_user_courses()`, `create_course()`, `update_course()`, `delete_course()`
- `get_course_lectures()`, `create_lecture()`, `update_lecture()`
- `get_user_tasks()`, `create_task()`, `update_task()`, `delete_task()`
- `get_materials_for_lecture()` - Materiali per lezione

### 📈 **Statistiche Operazioni Database**

| Categoria | Funzioni | Query Dirette | Tabelle Coinvolte |
|-----------|----------|---------------|-------------------|
| **Documenti** | 15+ | 20+ | papers, materials |
| **Utenti** | 8+ | 10+ | users, user_activity |
| **Chat** | 10+ | 15+ | chat_sessions, chat_messages, user_chat_history |
| **Accademico** | 20+ | 25+ | courses, lectures, tasks, study_sessions |
| **Knowledge Graph** | 6+ | 8+ | concept_entities, concept_relationships |
| **Gamification** | 8+ | 12+ | user_xp, user_achievements |
| **Totale** | **67+** | **90+** | **11 tabelle** |

### 🔗 **Pattern di Accesso Identificati**

#### 1. **Pattern CRUD Ricorrente**
```python
# Pattern standard in file_utils.py
def get_user_courses(user_id: int) -> list:
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE user_id = ?", (user_id,))
        return [dict(course) for course in cursor.fetchall()]
```

#### 2. **Pattern Complesso con JOIN**
```python
# Pattern complesso in get_recent_documents
cursor.execute("""
    SELECT DISTINCT p.*, ua.timestamp as last_accessed
    FROM papers p
    JOIN user_activity ua ON (ua.target_type = 'document' AND ua.target_id = p.file_name)
    WHERE ua.user_id = ?
""", (user_id,))
```

#### 3. **Pattern Aggregazione**
```python
# Pattern aggregazione in get_user_total_xp
cursor.execute("SELECT COALESCE(SUM(xp_amount), 0) as total FROM user_xp WHERE user_id = ?", (user_id,))
```

### ⚠️ **Problemi Identificati**

#### 1. **Accesso Diretto Sparso**
- 67+ funzioni accedono direttamente a `db_connect()`
- Pattern simili ripetuti in più moduli
- Nessuna gestione centralizzata errori
- Logging inconsistente

#### 2. **Configurazione Hardcoded**
```python
# In file_utils.py
DB_STORAGE_DIR = "db_memoria"
METADATA_DB_FILE = os.path.join(DB_STORAGE_DIR, "metadata.sqlite")

# In main.py
DB_STORAGE_DIR = "db_memoria"
```

#### 3. **Nessun Contesto Progetto**
- Tutte le operazioni sono globali
- Nessun supporto per `project_id`
- Impossibile isolare dati per progetto

#### 4. **Error Handling Inconsistente**
- Alcuni metodi hanno try/catch, altri no
- Messaggi errore non strutturati
- Nessun rollback automatico

### 🎯 **Piano Rifactoring**

#### **Fase 1: Repository Pattern**
```python
class DocumentRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_by_user(self, user_id, project_id=None):
        # Query con filtro progetto
        pass

    def save_with_context(self, document_data, context):
        # Salvataggio con contesto progetto
        pass
```

#### **Fase 2: Dependency Injection**
```python
class ChatService:
    def __init__(self, chat_repository: ChatRepository, context: ExecutionContext):
        self.chat_repo = chat_repository
        self.context = context
```

#### **Fase 3: Configurazione Unificata**
```python
class DatabaseConfig:
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.db_path = self._get_db_path()

    def _get_db_path(self) -> str:
        if self.project_id:
            return f"db_memoria/project_{self.project_id}.sqlite"
        return "db_memoria/metadata.sqlite"
```

### 📋 **Prossimi Step**

1. ✅ **Analisi completata** - Documentate tutte le dipendenze
2. 🔄 **Implementare Base Repository** - Classe base operazioni comuni
3. 🔄 **Creare Repository specifici** - Per ogni entità principale
4. 🔄 **Introdurre ExecutionContext** - Gestione stato applicazione
5. 🔄 **Sviluppare test** - Validazione modifiche

### 🚨 **Rischi Identificati**

- **Alto numero operazioni** (90+ query) richiede refactoring graduale
- **Interdipendenze complesse** tra moduli accademici e documenti
- **Performance** potrebbe essere influenzata da layer aggiuntivo
- **Testing** critico per evitare regressioni

### 💡 **Raccomandazioni**

1. **Refactoring incrementale** - Non modificare tutto insieme
2. **Test dopo ogni repository** - Validare funzionalità
3. **Logging strutturato** - Tracciare operazioni DB
4. **Fallback mechanism** - Mantenere compatibilità durante transizione
