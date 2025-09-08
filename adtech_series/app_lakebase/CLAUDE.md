# CLAUDE.md - AI Chatbot with Databricks Lakebase

## Repository Overview
This is an AI chatbot application built with **Dash** that leverages **Databricks Lakebase** (PostgreSQL + pgvector) for data persistence and vector search capabilities. The app includes sophisticated conversation handling with persistent history and AI agent integration.

## Architecture
- **Frontend**: Dash application (`app/dash_app.py`)
- **Backend**: PostgreSQL via Databricks Lakebase with pgvector for embeddings
- **AI Agent**: Deployed via Databricks serving endpoints
- **Infrastructure**: Terraform-managed Databricks Lakebase resources
- **Data Pipelines**: Notebooks for chat history sync and agent deployment

## Key Commands (via Justfile)

### Environment & Development
```bash
just venv                    # Create virtual environment and install dependencies
just run                     # Run application locally for development
just clean                   # Remove virtual environment and cache
```

### Infrastructure Management
```bash
just terraform-full         # Deploy terraform end-to-end
just terraform-init         # Initialize terraform
just terraform-plan         # Plan terraform changes
just terraform-apply        # Apply terraform changes
just terraform-destroy      # Destroy infrastructure
```

### Database Management
```bash
just migrations-generate "message"  # Generate new Alembic migration
just migrations-upgrade             # Apply pending migrations
just jdbc-url                       # Get JDBC connection string
just wait-for-database              # Wait for database availability
```

### Deployment
```bash
just full-deploy            # Complete end-to-end deployment
just bundle-deploy          # Deploy source code only
just app-start              # Start app compute
just app-stop               # Stop app compute
just app-deploy             # Deploy app to running compute
just app-permissions        # Configure app permissions
just agent-deploy           # Deploy AI agent
```

## Important Files & Directories

### Core Application
- `app/dash_app.py` - Main Dash application
- `app/requirements.txt` - Python dependencies
- `app/app.yml` - App configuration and environment variables
- `app/alembic.ini` - Database migration configuration

### Services & Models
- `app/services/chat_service.py` - Chat session management
- `app/services/agent_service.py` - AI agent interaction
- `app/services/embeddings_service.py` - Vector embeddings handling
- `app/services/task_queue.py` - Background task processing
- `app/models/` - SQLAlchemy models for database schema

### Database
- `app/migrations/` - Alembic database migrations
- `app/lakebase.py` - Database connection and utilities
- `app/databricks_utils.py` - Databricks SDK utilities

### Infrastructure
- `terraform/` - Infrastructure as Code for Databricks Lakebase
- `databricks.yml` - Databricks bundle configuration
- `resources/` - Databricks job and app definitions

### Data Pipelines
- `data_pipelines/src/00-postgres-catalog.ipynb` - Catalog setup
- `data_pipelines/src/01-sync-chat-history.ipynb` - Chat history sync
- `data_pipelines/src/02-chat-history-agent.ipynb` - AI agent creation

## Configuration

### Environment Variables (app/app.yml)
- `LAKEBASE_DB_NAME` - Database instance name
- `POSTGRES_GROUP` - Database access group
- `AGENT_ENDPOINT` - AI agent serving endpoint

### Database Configuration
- PostgreSQL with pgvector extension
- Tables: `chat_sessions`, `chat_history`, `message_embeddings`
- Vector search capabilities for semantic similarity

## Development Guidelines

### Python Dependencies
- **Always pin versions** in requirements.txt
- Use Databricks Apps pre-installed versions when possible:
  - streamlit==1.38.0
  - dash==2.18.1
  - databricks-sdk==0.58.0
  - sqlalchemy==2.0.30

### Database Migrations
- **NEVER write SQL migrations manually**
- Always use: `just migrations-generate "description"`
- Apply with: `just migrations-upgrade`

### Common Development Tasks
1. **Setup**: `just venv`
2. **Database changes**: `just migrations-generate "description"` → `just migrations-upgrade`
3. **Local testing**: `just run`
4. **Full deployment**: `just full-deploy`

## Quick Start for New Contributors
1. Install required tools: databricks CLI, terraform, jq, just, uv
2. Configure `databricks.yml` with your workspace
3. Run `just full-deploy` for complete setup
4. Use `just run` for local development

## Security Notes
- Uses Databricks workspace authentication
- Role-based access control via Databricks groups  
- Automatic service principal management
- Input validation and SQL injection prevention
- Secure SSL connections to database