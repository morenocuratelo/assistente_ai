# API Reference - Archivista AI v2.5

## 📋 Overview

This document provides comprehensive API documentation for Archivista AI v2.5, including all endpoints, data models, and integration patterns.

## 🏗️ API Architecture

### Base URL
```
http://localhost:8501/api/v1
```

### Authentication
All API endpoints require authentication via session token:
```
Authorization: Bearer <session_token>
```

### Response Format
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {},
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 🔐 Authentication API

### Login
**POST** `/auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "project_id": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "integer",
      "username": "string",
      "email": "string",
      "preferences": {},
      "is_active": true
    },
    "session": {
      "session_id": "string",
      "expires_at": "datetime",
      "metadata": {}
    }
  }
}
```

### Logout
**POST** `/auth/logout`

**Request Body:**
```json
{
  "session_id": "string"
}
```

### Create User
**POST** `/auth/users`

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "preferences": {}
}
```

## 📚 Document Management API

### Upload Document
**POST** `/documents/upload`

**Request Body (multipart/form-data):**
```
file: <file>
project_id: string
user_id: string (optional)
metadata: json (optional)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": "integer",
    "file_name": "string",
    "processing_status": "pending",
    "upload_timestamp": "datetime"
  }
}
```

### Get Document
**GET** `/documents/{document_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "document": {
      "id": "integer",
      "file_name": "string",
      "title": "string",
      "content_hash": "string",
      "file_size": "integer",
      "mime_type": "string",
      "processing_status": "completed",
      "formatted_preview": "string",
      "keywords": ["string"],
      "created_at": "datetime",
      "created_by": "integer"
    }
  }
}
```

### List Documents
**GET** `/documents`

**Query Parameters:**
- `project_id`: string (optional)
- `status`: string (optional)
- `limit`: integer (default: 50)
- `offset`: integer (default: 0)
- `search`: string (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "integer",
        "file_name": "string",
        "title": "string",
        "processing_status": "string",
        "created_at": "datetime"
      }
    ],
    "total_count": "integer",
    "has_more": "boolean"
  }
}
```

### Update Document
**PUT** `/documents/{document_id}`

**Request Body:**
```json
{
  "title": "string (optional)",
  "keywords": ["string"] (optional)",
  "metadata": {} (optional)
}
```

### Delete Document
**DELETE** `/documents/{document_id}`

### Batch Operations
**POST** `/documents/batch`

**Request Body:**
```json
{
  "operation": "delete|archive|reprocess",
  "document_ids": ["integer"],
  "parameters": {}
}
```

## 🔍 Search API

### Advanced Search
**POST** `/search/advanced`

**Request Body:**
```json
{
  "query": "string",
  "project_id": "string (optional)",
  "filters": {
    "status": "string (optional)",
    "date_from": "string (optional)",
    "date_to": "string (optional)",
    "size_min": "integer (optional)",
    "size_max": "integer (optional)",
    "mime_types": ["string"] (optional)
  },
  "limit": "integer (default: 50)",
  "offset": "integer (default: 0)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "document": {},
        "score": "float",
        "highlights": ["string"],
        "matched_fields": ["string"],
        "rank": "integer"
      }
    ],
    "total_found": "integer",
    "search_time_ms": "integer",
    "suggestions": ["string"],
    "facets": {}
  }
}
```

### Search Suggestions
**GET** `/search/suggestions`

**Query Parameters:**
- `query`: string
- `project_id`: string (optional)
- `limit`: integer (default: 10)

## 🧠 Knowledge Graph API

### Build Knowledge Graph
**POST** `/knowledge-graph/build`

**Request Body:**
```json
{
  "project_id": "string",
  "user_id": "string (optional)",
  "min_confidence": "float (default: 0.3)"
}
```

### Query Knowledge Graph
**POST** `/knowledge-graph/query`

**Request Body:**
```json
{
  "query": "string",
  "project_id": "string",
  "max_results": "integer (default: 10)"
}
```

### Get Graph Visualization
**GET** `/knowledge-graph/visualization/{project_id}`

**Query Parameters:**
- `format`: string (json|png|svg, default: json)

### Get Related Concepts
**GET** `/knowledge-graph/related/{concept}`

**Query Parameters:**
- `project_id`: string
- `max_neighbors`: integer (default: 10)

## 💬 Chat API

### Create Chat Session
**POST** `/chat/sessions`

**Request Body:**
```json
{
  "project_id": "string",
  "user_id": "string",
  "session_name": "string (optional)"
}
```

### Send Message
**POST** `/chat/sessions/{session_id}/messages`

**Request Body:**
```json
{
  "message": "string",
  "context_documents": ["integer"] (optional)
}
```

**Response (Streaming):**
```json
{
  "message_id": "string",
  "content": "string",
  "confidence": "float",
  "sources": ["string"],
  "timestamp": "datetime"
}
```

### Get Chat History
**GET** `/chat/sessions/{session_id}/history`

## 🤝 Collaboration API

### Create Collaboration Session
**POST** `/collaboration/sessions`

**Request Body:**
```json
{
  "document_id": "string",
  "creator_user_id": "string",
  "max_participants": "integer (default: 10)"
}
```

### Join Session
**POST** `/collaboration/sessions/{session_id}/join`

**Request Body:**
```json
{
  "user_id": "string"
}
```

### Add Annotation
**POST** `/collaboration/annotations`

**Request Body:**
```json
{
  "document_id": "string",
  "user_id": "string",
  "annotation_type": "comment|highlight|note|suggestion",
  "content": "string",
  "position": {
    "x": "float",
    "y": "float",
    "page": "integer"
  }
}
```

### Add Comment
**POST** `/collaboration/comments`

**Request Body:**
```json
{
  "document_id": "string",
  "user_id": "string",
  "content": "string",
  "parent_comment_id": "string (optional)",
  "position": {} (optional)
}
```

## 📊 Analytics API

### Get Archive Statistics
**GET** `/analytics/archive/{project_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_documents": "integer",
    "processing_stats": {},
    "storage_summary": {},
    "recent_activity": {}
  }
}
```

### Get User Analytics
**GET** `/analytics/users/{user_id}`

**Query Parameters:**
- `days`: integer (default: 30)

### Get System Health
**GET** `/analytics/system/health`

**Response:**
```json
{
  "success": true,
  "data": {
    "database": "healthy|warning|critical",
    "ai_services": "healthy|warning|critical",
    "performance": "healthy|warning|critical",
    "security": "healthy|warning|critical"
  }
}
```

## ⚙️ Configuration API

### Get Configuration
**GET** `/config`

**Response:**
```json
{
  "success": true,
  "data": {
    "app_name": "string",
    "version": "string",
    "environment": "string",
    "features": {},
    "settings": {}
  }
}
```

### Update Configuration
**PUT** `/config`

**Request Body:**
```json
{
  "updates": {
    "ui": {
      "theme": "dark",
      "items_per_page": 50
    }
  }
}
```

### Get Feature Settings
**GET** `/config/features/{feature_name}`

## 🔧 System Management API

### Run Database Migration
**POST** `/system/migrate`

**Request Body:**
```json
{
  "target_version": "string (optional)"
}
```

### Get System Status
**GET** `/system/status`

**Response:**
```json
{
  "success": true,
  "data": {
    "database": "connected",
    "ai_services": "available",
    "file_storage": "accessible",
    "cache": "healthy",
    "uptime_seconds": "integer"
  }
}
```

### Health Check
**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "datetime",
  "version": "string",
  "checks": {
    "database": "pass|fail",
    "ai_service": "pass|fail",
    "file_system": "pass|fail"
  }
}
```

## 📈 Performance API

### Get Performance Metrics
**GET** `/performance/metrics`

**Query Parameters:**
- `hours`: integer (default: 24)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_operations": "integer",
    "avg_response_time_ms": "float",
    "cache_hit_rate": "float",
    "error_rate": "float",
    "slow_operations": []
  }
}
```

### Get Cache Statistics
**GET** `/performance/cache`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_entries": "integer",
    "hit_rate": "float",
    "memory_usage_mb": "float",
    "oldest_entry": "datetime",
    "newest_entry": "datetime"
  }
}
```

## 🔒 Security API

### Get Security Audit
**GET** `/security/audit`

**Response:**
```json
{
  "success": true,
  "data": {
    "audit_id": "string",
    "timestamp": "datetime",
    "vulnerabilities_found": "integer",
    "critical_issues": "integer",
    "high_issues": "integer",
    "summary": "string"
  }
}
```

### Get Security Events
**GET** `/security/events`

**Query Parameters:**
- `hours`: integer (default: 24)
- `severity`: string (optional)

## 🛠️ Development API

### Run Tests
**POST** `/dev/tests`

**Request Body:**
```json
{
  "test_type": "unit|integration|performance",
  "modules": ["string"] (optional),
  "coverage": "boolean (optional)"
}
```

### Get Code Metrics
**GET** `/dev/metrics`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_lines": "integer",
    "test_coverage": "float",
    "complexity_score": "float",
    "maintainability_index": "float"
  }
}
```

## 📋 Data Models

### Document Model
```json
{
  "id": "integer",
  "project_id": "string",
  "file_name": "string",
  "title": "string",
  "content_hash": "string",
  "file_size": "integer",
  "mime_type": "string",
  "processing_status": "string",
  "formatted_preview": "string",
  "keywords": ["string"],
  "ai_tasks": {},
  "created_by": "integer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### User Model
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "preferences": {},
  "is_active": "boolean",
  "is_new_user": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Project Model
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "owner_id": "integer",
  "is_default": "boolean",
  "settings": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 🔌 Integration Examples

### Python SDK Example
```python
from archivista_ai import ArchivistaClient

# Initialize client
client = ArchivistaClient(base_url="http://localhost:8501/api/v1")

# Login
auth_result = client.login("username", "password")
session_token = auth_result['session']['session_id']

# Upload document
with open("document.pdf", "rb") as f:
    upload_result = client.upload_document(
        file=f,
        project_id="my_project",
        session_token=session_token
    )

document_id = upload_result['document_id']

# Search documents
search_results = client.search_documents(
    query="machine learning",
    project_id="my_project",
    session_token=session_token
)

# Get document
document = client.get_document(document_id, session_token=session_token)
```

### JavaScript Example
```javascript
const ArchivistaAPI = {
  baseURL: 'http://localhost:8501/api/v1',

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });

    return response.json();
  },

  async uploadDocument(file, projectId, sessionToken) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);

    const response = await fetch(`${this.baseURL}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`
      },
      body: formData
    });

    return response.json();
  }
};
```

### cURL Examples
```bash
# Login
curl -X POST "http://localhost:8501/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Upload document
curl -X POST "http://localhost:8501/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "project_id=my_project"

# Search documents
curl -X POST "http://localhost:8501/api/v1/search/advanced" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "project_id": "my_project",
    "limit": 20
  }'
```

## 🚨 Error Codes

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid input parameters | 400 |
| `AUTHENTICATION_ERROR` | Authentication failed | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `NOT_FOUND_ERROR` | Resource not found | 404 |
| `CONFLICT_ERROR` | Resource conflict | 409 |
| `RATE_LIMIT_ERROR` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789",
    "retry_after": "integer (optional)"
  }
}
```

## 📊 Rate Limits

### Default Rate Limits

| Endpoint | Requests/Minute | Burst Limit |
|----------|----------------|-------------|
| `/auth/*` | 10 | 5 |
| `/documents/*` | 100 | 20 |
| `/search/*` | 60 | 10 |
| `/chat/*` | 30 | 10 |
| `/analytics/*` | 20 | 5 |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## 🔒 Security Considerations

### Authentication Security

- All API endpoints require valid session token
- Session tokens expire after 24 hours
- Account lockout after 5 failed attempts
- Password requirements: 8+ characters, mixed case, numbers, symbols

### Data Security

- All data encrypted in transit (HTTPS/TLS)
- Sensitive data encrypted at rest
- Input validation and sanitization
- SQL injection prevention
- XSS protection

### API Security

- Rate limiting to prevent abuse
- Request size limits
- File upload restrictions
- CORS configuration for web clients

## 📈 Monitoring & Analytics

### API Usage Metrics

- Request count and latency
- Error rates by endpoint
- User activity patterns
- Performance bottlenecks

### Health Check Endpoints

- `/health` - Basic health check
- `/system/status` - Detailed system status
- `/analytics/system/health` - AI service health

## 🔧 Webhook Support

### Webhook Configuration
```json
{
  "webhook_url": "https://your-app.com/webhooks/archivista",
  "events": [
    "document_processed",
    "collaboration_session_created",
    "user_registered"
  ],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

- `document.uploaded` - New document uploaded
- `document.processed` - Document processing completed
- `collaboration.session_created` - New collaboration session
- `user.registered` - New user registered
- `system.maintenance` - System maintenance events

## 🚀 Best Practices

### API Usage

1. **Reuse Connections**: Keep session tokens for multiple requests
2. **Handle Errors**: Always check response success field
3. **Rate Limiting**: Respect rate limits and implement exponential backoff
4. **Pagination**: Use limit/offset for large result sets
5. **Caching**: Cache frequently accessed data

### Security

1. **Store Tokens Securely**: Never log or expose session tokens
2. **Validate Input**: Always validate API responses
3. **Use HTTPS**: Always use HTTPS in production
4. **Monitor Usage**: Monitor API usage for anomalies

### Performance

1. **Batch Operations**: Use batch endpoints for multiple operations
2. **Optimize Queries**: Use filters to limit result sets
3. **Cache Results**: Cache search and document data
4. **Async Processing**: Use async endpoints for long operations

## 📞 Support

For API support and questions:

- **Documentation**: This API reference
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: development team contact

---

*API Reference - Archivista AI v2.5*
*Generated: $(date)*
