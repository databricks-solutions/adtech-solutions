# Audience Segmentation Databricks App

A Databricks App that enables advertisers to create audience segments without writing SQL. Built with React frontend and FastAPI backend.

## Features

**Agent Mode** - Conversational segment building powered by LLM
- Natural language input: "Dog owners in California aged 25-54"
- Automatic conversion to SQL queries
- Real-time preview with audience counts

**Builder Mode** - Visual no-code query builder
- Drag-and-drop condition builder
- Support for AND/OR logic with nested groups
- Multi-select dropdowns for categorical values

## Quick Start

```bash
# Install dependencies
bun install
uv venv && uv pip install -r requirements.txt

# Build frontend
bun run build

# Run backend
source .venv/bin/activate && uvicorn backend.main:app --reload
```

See [CLAUDE.md](CLAUDE.md) for comprehensive documentation including architecture, API endpoints, deployment, and troubleshooting.

## Architecture

```
frontend/          React + TypeScript + Tailwind CSS
  src/features/segment-builder/
    components/    UI components
    hooks/         Custom React hooks
    api/           API client functions

backend/           FastAPI + Python
  routers/         API endpoints
  services/        Business logic (SQL generation, LLM integration)
  config/          Feature metadata
```

## Live Demo

https://dq-adtech-1444828305810485.aws.databricksapps.com/

## Deployment

```bash
databricks apps deploy dq-adtech
```

## Data

- **Input**: Unity Catalog table with 3.4M audience profiles
- **Output**: Segments saved to Unity Catalog for activation
