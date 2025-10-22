# 🔌 API DOCUMENTATION - ASSISTENTE AI

**Data:** 22/10/2025
**Versione:** 1.0.0
**Stato:** Production Ready
**Autore:** Cline (AI Assistant)
**Modalità:** ACT MODE

---

## 🎯 **PANORAMICA API**

L'API dell'Assistente AI fornisce endpoints REST per l'integrazione programmatica con tutte le funzionalità del sistema. L'API è progettata per essere semplice, sicura e scalabile.

---

## 🔐 **AUTENTICAZIONE**

### **JWT Authentication**
Tutte le API richiedono autenticazione JWT:

```bash
Authorization: Bearer <your_jwt_token>
```

### **Ottenere Token**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user"
  }
}
```

---

## 📄 **DOCUMENT API**

### **Lista Documenti**
```bash
GET /api/documents
```

**Query Parameters:**
- `page` (int): Pagina (default: 1)
- `per_page` (int): Elementi per pagina (default: 20)
- `search` (string): Termine ricerca
- `category` (string): Filtro categoria
- `user_id` (int): Filtro utente
- `project_id` (int): Filtro progetto

**Response:**
```json
{
  "documents": [
    {
      "id": 1,
      "title": "Sample Document",
      "content": "Document content...",
      "file_path": "/uploads/document.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "metadata": {"author": "John Doe"},
      "created_at": "2025-10-22T20:00:00Z",
      "user_id": 1,
      "project_id": 1,
      "category": "research",
      "tags": ["important", "review"]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

### **Crea Documento**
```bash
POST /api/documents
Content-Type: application/json

{
  "title": "New Document",
  "content": "Document content",
  "category": "research",
  "tags": ["tag1", "tag2"],
  "project_id": 1
}
```

**Response:** `201 Created` con documento creato

### **Dettagli Documento**
```bash
GET /api/documents/{id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Sample Document",
  "content": "Full document content...",
  "file_path": "/uploads/document.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "metadata": {"author": "John Doe"},
  "created_at": "2025-10-22T20:00:00Z",
  "updated_at": "2025-10-22T20:30:00Z",
  "user_id": 1,
  "project_id": 1,
  "category": "research",
  "tags": ["important", "review"]
}
```

### **Aggiorna Documento**
```bash
PUT /api/documents/{id}
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content",
  "category": "analysis",
  "tags": ["updated", "important"]
}
```

### **Elimina Documento**
```bash
DELETE /api/documents/{id}
```

**Response:** `204 No Content`

### **Cerca Documenti**
```bash
POST /api/documents/search
Content-Type: application/json

{
  "query": "machine learning",
  "filters": {
    "category": "research",
    "date_from": "2025-01-01",
    "date_to": "2025-12-31"
  },
  "sort": {
    "field": "created_at",
    "order": "desc"
  }
}
```

---

## 💬 **CHAT API**

### **Invia Messaggio**
```bash
POST /api/chat/messages
Content-Type: application/json

{
  "message": "What is machine learning?",
  "context": {
    "document_ids": [1, 2, 3],
    "project_id": 1
  },
  "model": "gpt-4",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "msg_123",
  "message": "Machine learning is...",
  "timestamp": "2025-10-22T20:00:00Z",
  "model": "gpt-4",
  "tokens_used": 150,
  "context": {
    "document_ids": [1, 2, 3],
    "project_id": 1
  }
}
```

### **History Conversazioni**
```bash
GET /api/chat/history
```

**Query Parameters:**
- `limit` (int): Numero messaggi (default: 50)
- `before` (string): ID messaggio prima del quale iniziare

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "message": "User message",
      "response": "AI response",
      "timestamp": "2025-10-22T20:00:00Z",
      "model": "gpt-4",
      "tokens_used": 150
    }
  ]
}
```

### **Aggiorna Contesto**
```bash
POST /api/chat/context
Content-Type: application/json

{
  "document_ids": [1, 2, 3],
  "project_id": 1,
  "instructions": "Focus on technical aspects"
}
```

### **Elimina Sessione**
```bash
DELETE /api/chat/sessions/{session_id}
```

---

## 📚 **PROJECT API**

### **Lista Progetti**
```bash
GET /api/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "AI Research Project",
      "description": "Research on machine learning",
      "project_type": "research",
      "status": "active",
      "created_at": "2025-10-22T20:00:00Z",
      "user_id": 1,
      "member_count": 3,
      "document_count": 15
    }
  ]
}
```

### **Crea Progetto**
```bash
POST /api/projects
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description",
  "project_type": "development",
  "members": ["user1@example.com", "user2@example.com"]
}
```

### **Dettagli Progetto**
```bash
GET /api/projects/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "AI Research Project",
  "description": "Research on machine learning",
  "project_type": "research",
  "status": "active",
  "created_at": "2025-10-22T20:00:00Z",
  "updated_at": "2025-10-22T20:30:00Z",
  "user_id": 1,
  "members": [
    {
      "id": 1,
      "email": "user1@example.com",
      "role": "owner"
    }
  ],
  "documents": 15,
  "activities": 8
}
```

### **Aggiorna Progetto**
```bash
PUT /api/projects/{id}
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description",
  "status": "completed"
}
```

### **Elimina Progetto**
```bash
DELETE /api/projects/{id}
```

---

## 🎓 **CAREER API**

### **Lista Corsi**
```bash
GET /api/career/courses
```

**Response:**
```json
{
  "courses": [
    {
      "id": 1,
      "name": "Machine Learning",
      "description": "Introduction to ML",
      "university": "MIT",
      "department": "Computer Science",
      "semester": "Fall 2025",
      "year": 2025,
      "status": "active",
      "created_at": "2025-10-22T20:00:00Z",
      "user_id": 1
    }
  ]
}
```

### **Crea Corso**
```bash
POST /api/career/courses
Content-Type: application/json

{
  "name": "Deep Learning",
  "description": "Advanced neural networks",
  "university": "Stanford",
  "department": "AI",
  "semester": "Spring 2026",
  "year": 2026
}
```

### **Lista Attività**
```bash
GET /api/career/activities
```

**Query Parameters:**
- `course_id` (int): Filtro per corso
- `status` (string): Filtro stato (pending, in_progress, completed)
- `priority` (string): Filtro priorità

**Response:**
```json
{
  "activities": [
    {
      "id": 1,
      "title": "Neural Network Assignment",
      "description": "Implement a simple neural network",
      "activity_type": "assignment",
      "status": "in_progress",
      "priority": "high",
      "due_date": "2025-11-15",
      "completed_at": null,
      "created_at": "2025-10-22T20:00:00Z",
      "course_id": 1,
      "user_id": 1
    }
  ]
}
```

### **Crea Attività**
```bash
POST /api/career/activities
Content-Type: application/json

{
  "title": "Research Paper",
  "description": "Write research paper on AI",
  "activity_type": "research",
  "priority": "medium",
  "due_date": "2025-12-01",
  "course_id": 1
}
```

---

## 👥 **USER API**

### **Profilo Utente**
```bash
GET /api/users/profile
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2025-10-22T20:00:00Z",
  "last_login": "2025-10-22T20:30:00Z",
  "preferences": {
    "theme": "auto",
    "language": "it",
    "notifications": true
  }
}
```

### **Aggiorna Profilo**
```bash
PUT /api/users/profile
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "preferences": {
    "theme": "dark",
    "language": "en"
  }
}
```

### **Lista Utenti** (Admin only)
```bash
GET /api/users
```

---

## 📊 **ANALYTICS API**

### **Dashboard Metrics**
```bash
GET /api/analytics/dashboard
```

**Response:**
```json
{
  "metrics": {
    "total_documents": 150,
    "total_users": 25,
    "total_projects": 8,
    "total_courses": 12,
    "storage_used": 2048000000,
    "system_health": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_usage": 34.1,
      "uptime": 99.9
    }
  },
  "trends": {
    "documents_last_7_days": 23,
    "users_last_30_days": 5,
    "projects_completed": 3
  }
}
```

### **Usage Analytics**
```bash
GET /api/analytics/usage
```

**Query Parameters:**
- `period` (string): "day", "week", "month", "year"
- `start_date` (string): Data inizio (YYYY-MM-DD)
- `end_date` (string): Data fine (YYYY-MM-DD)

---

## 🔧 **SYSTEM API**

### **Health Check**
```bash
GET /api/system/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T20:00:00Z",
  "services": {
    "database": "healthy",
    "ai_service": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  },
  "metrics": {
    "response_time": 0.045,
    "cpu_usage": 45.2,
    "memory_usage": 67.8
  }
}
```

### **System Info**
```bash
GET /api/system/info
```

**Response:**
```json
{
  "version": "1.0.0",
  "environment": "production",
  "python_version": "3.11.0",
  "database": "SQLite 3.40.0",
  "ai_models": ["gpt-4", "gpt-3.5-turbo", "ollama"],
  "features": [
    "document_management",
    "ai_chat",
    "project_management",
    "career_planning",
    "knowledge_graph"
  ]
}
```

---

## 🐛 **ERROR HANDLING**

### **Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2025-10-22T20:00:00Z"
}
```

### **Common Error Codes**
- `VALIDATION_ERROR` (400) - Dati input non validi
- `AUTHENTICATION_ERROR` (401) - Token non valido
- `AUTHORIZATION_ERROR` (403) - Permessi insufficienti
- `NOT_FOUND` (404) - Risorsa non trovata
- `CONFLICT` (409) - Conflitto dati
- `RATE_LIMITED` (429) - Limite rate superato
- `INTERNAL_ERROR` (500) - Errore interno server

---

## 📈 **RATE LIMITING**

### **Default Limits**
- **Per minute:** 60 requests
- **Per hour:** 1000 requests
- **Per day:** 10000 requests

### **Rate Limit Headers**
```bash
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1634937600
```

---

## 🔌 **WEBHOOKS**

### **Configura Webhook**
```bash
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["document.created", "project.updated"],
  "secret": "your_webhook_secret"
}
```

### **Eventi Supportati**
- `document.created` - Documento creato
- `document.updated` - Documento aggiornato
- `document.deleted` - Documento eliminato
- `project.created` - Progetto creato
- `project.updated` - Progetto aggiornato
- `user.created` - Utente creato
- `system.health_changed` - Salute sistema cambiata

### **Webhook Payload**
```json
{
  "event": "document.created",
  "timestamp": "2025-10-22T20:00:00Z",
  "data": {
    "id": 1,
    "title": "New Document",
    "user_id": 1
  },
  "webhook_id": "wh_123"
}
```

---

## 🧪 **SDK E LIBRERIE**

### **Python SDK**
```python
from assistente_ai import Client

client = Client(api_key="your_api_key")

# Documenti
documents = client.documents.list()
new_doc = client.documents.create(title="Test", content="Content")

# Chat
response = client.chat.send_message("Hello AI")

# Progetti
projects = client.projects.list()
```

### **JavaScript SDK**
```javascript
import { AssistenteAI } from 'assistente-ai';

const client = new AssistenteAI('your_api_key');

// Documenti
const documents = await client.documents.list();
const newDoc = await client.documents.create({
  title: 'Test Document',
  content: 'Content'
});
```

---

## 🔄 **MIGRAZIONE API**

### **Migration Endpoints**
```bash
# Verifica compatibilità
GET /api/migration/compatibility

# Migra dati
POST /api/migration/execute

# Status migrazione
GET /api/migration/status
```

---

## 📚 **ESEMPI INTEGRAZIONE**

### **Esempio 1: Integrazione CMS**
```python
import requests

def create_document_from_cms(title, content, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "title": title,
        "content": content,
        "category": "cms_import"
    }

    response = requests.post(
        "https://api.assistente-ai.com/documents",
        headers=headers,
        json=data
    )

    return response.json()
```

### **Esempio 2: Chatbot Integration**
```javascript
async function askAI(question, context, apiKey) {
    const response = await fetch('https://api.assistente-ai.com/chat/messages', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: question,
            context: context
        })
    });

    return await response.json();
}
```

---

## 🚀 **BEST PRACTICES**

### **API Usage**
- ✅ **Cache responses** quando possibile
- ✅ **Handle errors** gracefully
- ✅ **Use pagination** per liste grandi
- ✅ **Validate input** client-side
- ✅ **Monitor rate limits**

### **Security**
- ✅ **Store API keys** securely
- ✅ **Use HTTPS** only
- ✅ **Rotate tokens** regularly
- ✅ **Validate webhooks** signatures
- ✅ **Limit permissions** appropriately

### **Performance**
- ✅ **Batch requests** when possible
- ✅ **Use compression** for large payloads
- ✅ **Implement retry logic** with exponential backoff
- ✅ **Monitor API usage** and performance
- ✅ **Cache frequently accessed data**

---

## 📞 **SUPPORTO API**

### **Developer Resources**
- 📚 **Documentation:** Questa pagina
- 💻 **GitHub:** github.com/assistente-ai/api
- 🧪 **Sandbox:** sandbox.assistente-ai.com
- 📖 **Changelog:** changelog.assistente-ai.com
- 🐛 **Issue Tracker:** issues.assistente-ai.com

### **Supporto**
- 📧 **Email:** developers@assistente-ai.com
- 💬 **Discord:** Assistente AI Developers
- 📖 **Forum:** community.assistente-ai.com
- 📚 **Knowledge Base:** kb.assistente-ai.com

---

**Stato API:** ✅ **PRODUCTION READY**
**Versione:** 1.0.0
**Data Rilascio:** 22/10/2025
**Prossimo Aggiornamento:** 22/01/2026

**🔗 Base URL:** `https://api.assistente-ai.com`
**📖 Documentation:** `https://docs.assistente-ai.com`
