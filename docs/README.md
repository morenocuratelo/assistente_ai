# Archivista AI v2.5 - Documentation

## 📋 Overview

**Archivista AI** is an intelligent document management and analysis system designed for academic and research use. This system provides AI-powered document processing, knowledge graph generation, real-time collaboration, and advanced search capabilities.

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit Web App  │  REST API  │  Real-time WebSocket       │
├─────────────────────────────────────────────────────────────────┤
│                    Services Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  Archive Service    │  Auth Service    │  AI Service          │
│  Chat Service       │  Collaboration   │  Search Engine       │
├─────────────────────────────────────────────────────────────────┤
│                    Core Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  Configuration      │  Error Handling  │  Performance         │
│  Security           │  Validation      │  Monitoring          │
├─────────────────────────────────────────────────────────────────┤
│                    Data Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  SQLite Database    │  File Storage    │  Cache Layer         │
│  Vector Store       │  Knowledge Graph  │  Model Registry      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **🤖 AI-Powered Document Analysis**: Advanced entity extraction, topic modeling, and sentiment analysis
- **🔍 Intelligent Search**: Full-text search with highlighting, ranking, and advanced filtering
- **🧠 Knowledge Graph**: Interactive knowledge graph with relationship mapping and visualization
- **💬 Smart Chat**: AI-powered chat with document context and confidence scoring
- **🤝 Real-time Collaboration**: Collaborative editing, annotations, and commenting
- **📊 Performance Monitoring**: Comprehensive performance tracking and optimization
- **🔒 Security First**: Input validation, secure authentication, and data protection
- **📱 Modern UI**: Responsive design with consistent components and accessibility

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- SQLite3
- Redis (for caching and background tasks)
- 4GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/morenocuratelo/assistente_ai.git
cd assistente_ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup development environment
pip install -e ".[dev]"

# Initialize database
python -c "from src.database.migrations.manager import MigrationManager; MigrationManager('db_memoria/metadata.sqlite').run_migrations()"

# Start application
streamlit run main.py
```

### Configuration

Create a `config.json` file or set environment variables:

```json
{
  "app_name": "Archivista AI",
  "environment": "development",
  "debug": true,
  "database": {
    "url": "sqlite:///db_memoria/metadata.sqlite",
    "pool_size": 5,
    "timeout": 30
  },
  "ai": {
    "model_name": "llama3",
    "temperature": 0.7,
    "max_tokens": 1000,
    "base_url": "http://localhost:11434"
  },
  "ui": {
    "theme": "light",
    "language": "it",
    "items_per_page": 20
  }
}
```

## 📚 Documentation Structure

### 📖 User Documentation

- **[User Guide](user_guide.md)**: Complete user manual with tutorials and examples
- **[Quick Start](quick_start.md)**: Fast setup and first steps
- **[Feature Guide](features.md)**: Detailed feature explanations
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions
- **[FAQ](faq.md)**: Frequently asked questions

### 🔧 Developer Documentation

- **[API Reference](api_reference.md)**: Complete API documentation
- **[Architecture Guide](architecture.md)**: System architecture and design decisions
- **[Development Guide](development.md)**: Development setup and workflows
- **[Testing Guide](testing.md)**: Testing strategies and practices
- **[Deployment Guide](deployment.md)**: Production deployment instructions

### 🛠️ Technical Documentation

- **[Database Schema](database_schema.md)**: Database design and relationships
- **[Security Guide](security.md)**: Security measures and best practices
- **[Performance Guide](performance.md)**: Performance optimization and monitoring
- **[Migration Guide](migration.md)**: Database migration procedures
- **[Monitoring Guide](monitoring.md)**: System monitoring and alerting

## 🎯 Key Features

### Document Management

- **Multi-format Support**: PDF, DOCX, TXT, RTF, HTML, and more
- **Intelligent Processing**: AI-powered content extraction and analysis
- **Duplicate Detection**: Automatic duplicate detection using content hashing
- **Batch Operations**: Bulk document operations with progress tracking
- **Export Capabilities**: Export documents in multiple formats (JSON, CSV, TXT)

### AI-Powered Analysis

- **Entity Extraction**: Automatic extraction of people, organizations, locations, dates
- **Topic Modeling**: Intelligent topic detection and categorization
- **Sentiment Analysis**: Document sentiment and emotion detection
- **Confidence Scoring**: AI response confidence with transparency
- **Knowledge Graph**: Interactive knowledge graph with relationship mapping

### Search & Discovery

- **Full-Text Search**: Advanced search with highlighting and ranking
- **Advanced Filters**: Filter by date, size, type, status, and metadata
- **Search Suggestions**: AI-powered search suggestions and auto-complete
- **Similar Documents**: Find similar documents using AI similarity detection
- **Search Analytics**: Search performance and usage analytics

### Collaboration

- **Real-time Editing**: Collaborative document editing with conflict resolution
- **Comments & Annotations**: Document commenting and annotation system
- **Change Tracking**: Complete change history and version control
- **Notification System**: Real-time notifications for collaboration events
- **Session Management**: Multi-user session management with permissions

### Performance & Security

- **Connection Pooling**: Database connection pooling for high performance
- **Caching System**: Multi-level caching for frequently accessed data
- **Lazy Loading**: Component lazy loading for improved UX
- **Security Auditing**: Comprehensive security vulnerability assessment
- **Performance Monitoring**: Real-time performance monitoring and alerting

## 🔧 Development

### Project Structure

```
src/
├── config/                 # Configuration management
│   ├── settings.py        # Main configuration
│   └── validation.py      # Configuration validation
├── core/                  # Core systems
│   ├── errors/           # Error handling
│   ├── performance/      # Performance optimization
│   └── security/         # Security systems
├── database/              # Data access layer
│   ├── models/           # Pydantic models
│   ├── repositories/     # Repository pattern
│   └── migrations/       # Database migrations
├── services/              # Business logic layer
│   ├── archive/          # Archive service
│   ├── auth/             # Authentication service
│   ├── ai/               # AI services
│   └── collaboration/    # Collaboration services
├── ui/                    # User interface layer
│   ├── components/       # Reusable UI components
│   └── pages/            # Page implementations
└── tests/                 # Test suite
    ├── conftest.py       # Test configuration
    └── test_*.py         # Test files
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m "unit"
pytest -m "integration"
pytest -m "performance"

# Run with verbose output
pytest -v -s
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Lint code
flake8 src tests
mypy src

# Security scan
bandit -r src

# Check documentation coverage
interrogate src
```

## 🚀 Deployment

### Production Deployment

```bash
# Build for production
python -m build

# Install in production mode
pip install archivista-ai

# Run with production settings
ENVIRONMENT=production streamlit run main.py
```

### Docker Deployment

```bash
# Build Docker image
docker build -f Dockerfile.prod -t archivista-ai .

# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up
```

### Environment Variables

```bash
# Required environment variables
DATABASE_URL=sqlite:///db_memoria/metadata.sqlite
SECRET_KEY=your-secret-key-here
AI_API_KEY=your-ai-api-key
REDIS_URL=redis://localhost:6379

# Optional configuration
DEBUG=false
LOG_LEVEL=INFO
MAX_WORKERS=4
CACHE_TTL=300
```

## 📊 Monitoring

### Health Checks

```bash
# Health check endpoint
curl http://localhost:8501/health

# Database health
python -c "from src.database.connection import check_database_health; print(check_database_health())"

# Service health
python -c "from src.core.monitoring import get_system_health; print(get_system_health())"
```

### Performance Monitoring

```bash
# Get performance metrics
python -c "from src.core.performance.optimizer import get_performance_summary; print(get_performance_summary())"

# Database performance
python -c "from src.core.performance.database_optimizer import get_database_performance_dashboard; print(get_database_performance_dashboard('db_memoria/metadata.sqlite'))"
```

### Security Monitoring

```bash
# Run security audit
python -c "from src.core.security.auditor import run_security_audit; print(run_security_audit())"

# Check security events
python -c "from src.core.security.auditor import get_security_events; print(get_security_events())"
```

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Add type hints for all functions
- Include unit tests for new features
- Update documentation as needed

### Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add changelog entry
4. Request code review
5. Address review feedback

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check this documentation first
- **Issues**: Search existing issues on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact the development team

### Reporting Bugs

1. **Search** existing issues
2. **Create** a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment information
   - Error logs if applicable

### Feature Requests

1. **Search** existing feature requests
2. **Create** a new feature request with:
   - Clear use case
   - Proposed solution
   - Benefits and impact
   - Implementation suggestions

## 🎉 Acknowledgments

- **Streamlit** for the amazing web framework
- **LlamaIndex** for AI capabilities
- **NetworkX** for graph algorithms
- **SQLite** for reliable data storage
- **Open Source Community** for tools and libraries

## 📈 Roadmap

### Version 2.5 (Current)

- ✅ Modular architecture implementation
- ✅ AI confidence system
- ✅ Advanced search and filtering
- ✅ Real-time collaboration
- ✅ Performance optimization
- ✅ Security hardening

### Version 2.6 (Next)

- 🔄 Advanced AI model management
- 🔄 Multi-language support
- 🔄 Plugin system
- 🔄 API rate limiting
- 🔄 Enhanced analytics

### Version 3.0 (Future)

- 🚀 Machine learning model training
- 🚀 Advanced knowledge graph features
- 🚀 Mobile application
- 🚀 Multi-tenant support
- 🚀 Advanced security features

---

**Built with ❤️ for the academic and research community**

*For more information, visit our [GitHub repository](https://github.com/morenocuratelo/assistente_ai)*
