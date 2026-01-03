# Project Structure

Complete directory structure for the Sales Intelligence Automation System.

## Root Directory

```
Sales_Intelligence_Automation_System/
├── README.md               # Main project documentation
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
├── Makefile                # Build and development commands
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml          # Python project config
├── pytest.ini              # Test configuration
├── Dockerfile              # Container build
├── docker-compose.yml      # Local development
├── main.py                 # Cloud Function entry points
├── run_local.ps1           # Local run (Windows)
└── run_local.sh            # Local run (Unix)
```

## Source Code

### `ai/` - AI Abstraction Layer

Provider-agnostic interfaces for LLM and embeddings.

```
ai/
├── __init__.py
├── models.py           # LLM provider abstraction
├── embeddings.py       # Embedding provider
├── semantic_search.py  # Vector search
├── scoring.py          # Account scoring
├── summarization.py    # Text summarization
└── insights.py         # Insights generation
```

### `cloud_functions/` - Data Ingestion

Cloud Functions for syncing external data sources.

```
cloud_functions/
├── gmail_sync/         # Gmail API integration
├── salesforce_sync/    # Salesforce API integration
├── dialpad_sync/       # Dialpad API integration
├── hubspot_sync/       # HubSpot API integration
└── entity_resolution/  # Email/phone matching
```

### `intelligence/` - AI Features

AI-powered intelligence functions.

```
intelligence/
├── scoring/           # Account scoring
├── nlp_query/         # Natural language queries
├── vector_search/     # Semantic search
├── embeddings/        # Vector generation
├── automation/        # Workflows (leads, HubSpot)
├── email_replies/     # AI reply generation
└── README.md
```

### `integrations/` - External APIs

API client implementations.

```
integrations/
├── gmail_oauth.py
├── salesforce_oauth.py
├── dialpad_api.py
└── hubspot_api.py
```

### `utils/` - Shared Utilities

Common utilities and helpers.

```
utils/
├── bigquery_client.py    # BigQuery wrapper
├── secret_manager.py     # Secret access
├── logger.py             # Structured logging
├── retry.py              # Retry logic
├── input_validation.py   # Input validation
├── email_normalizer.py   # Email normalization
├── phone_normalizer.py   # Phone normalization
├── circuit_breaker.py    # Circuit breaker
├── cache.py              # Caching
├── monitoring.py         # Performance monitoring
└── vertex_ai_init.py     # Vertex AI setup
```

### `config/` - Configuration

Configuration management.

```
config/
├── __init__.py
└── config.py           # Settings loader
```

### `web_app/` - Web Application

Streamlit dashboard.

```
web_app/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── Dockerfile          # Container build
├── styles.css          # Custom styling
└── README.md
```

## Documentation

```
docs/
├── setup/              # Setup and configuration guides
│   ├── DEPLOYMENT.md
│   ├── CONFIGURATION.md
│   ├── GMAIL_DWD_SETUP.md
│   ├── HUBSPOT_SETUP.md
│   ├── SALESFORCE_OAUTH_SETUP.md
│   └── SECRETS_LIST.md
├── architecture/       # Technical architecture
│   ├── SYSTEM_OVERVIEW.md
│   ├── API.md
│   └── api/openapi.yaml
├── operations/         # Runbooks and troubleshooting
│   ├── RUNBOOK.md
│   └── TROUBLESHOOTING.md
├── user-guides/        # End-user documentation
│   └── WEB_APP.md
└── adr/                # Architecture decisions
    ├── 001-use-vertex-ai-gemini.md
    └── 002-date-serialization-fix.md
```

## Scripts

```
scripts/
├── setup/              # Initial setup scripts
│   ├── setup_service_account.ps1
│   ├── setup_bigquery.ps1
│   ├── setup_secrets.ps1
│   └── ...
├── deploy/             # Deployment scripts
│   ├── deploy_all.ps1
│   ├── deploy_functions.ps1
│   └── ...
├── test/               # Testing and validation
│   ├── test_ingestion.ps1
│   ├── verify_deployment.ps1
│   └── ...
└── maintenance/        # Operations scripts
    ├── run_all_syncs.ps1
    ├── update_secrets.ps1
    └── ...
```

## Infrastructure

```
infrastructure/
├── main.tf             # Main Terraform config
├── variables.tf        # Variables
├── outputs.tf          # Outputs
├── scheduler.tf        # Cloud Scheduler
├── pubsub.tf           # Pub/Sub topics
├── monitoring.tf       # Monitoring/alerting
└── terraform.tfvars.example
```

## Tests

```
tests/
├── conftest.py         # Pytest configuration
├── fixtures/           # Test data
├── unit/               # Unit tests
├── integration/        # Integration tests
├── e2e/                # End-to-end tests
└── test_*.py           # Test files
```

## BigQuery

```
bigquery/
└── schemas/
    └── create_tables.sql  # Table definitions
```

