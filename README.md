# Sales Intelligence & Automation System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GCP](https://img.shields.io/badge/cloud-Google%20Cloud-4285F4.svg)](https://cloud.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-driven sales intelligence platform that unifies communication data and automates sales workflows across Salesforce, Gmail, Dialpad, and HubSpot.

## Overview

This system consolidates all customer interactions (emails, calls, CRM activities) into a unified BigQuery data warehouse, providing AI-powered insights for sales prioritization and automation.

### Key Features

- **Unified Data Warehouse** - Consolidate Gmail, Salesforce, Dialpad, and HubSpot data
- **AI Account Scoring** - Daily prioritization using Vertex AI (Gemini)
- **Natural Language Queries** - Ask questions about your data in plain English
- **Semantic Search** - Find communications by intent, not just keywords
- **Automated Lead Creation** - Convert unmatched emails to Salesforce leads
- **HubSpot Integration** - Automatic sequence enrollment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
├──────────┬──────────┬──────────┬──────────────────────────────┤
│  Gmail   │Salesforce│ Dialpad  │         HubSpot            │
└────┬─────┴────┬─────┴────┬─────┴────────────┬───────────────┘
     │          │          │                  │
     ▼          ▼          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloud Functions (ETL)                          │
│   gmail-sync │ salesforce-sync │ dialpad-sync │ hubspot-sync│
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 BigQuery Data Warehouse                     │
│  └─ sales_intelligence dataset (16 tables)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Account      │ │ NLP Query    │ │ Vector       │
│ Scoring      │ │ Generator    │ │ Search       │
└──────────────┘ └──────────────┘ └──────────────┘
          │              │              │
          └──────────────┼──────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Web Application                      │
│     Dashboard │ Search │ Queries │ Account Details         │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Google Cloud Platform project with billing enabled
- Python 3.11+
- `gcloud` CLI installed and configured
- API credentials for: Salesforce, Gmail, Dialpad, HubSpot

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Sales_Intelligence_Automation_System

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Set required environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Authenticate with GCP
gcloud auth login
gcloud auth application-default login
gcloud config set project $GCP_PROJECT_ID
```

### 3. Deploy Infrastructure

```bash
# Enable required APIs
./scripts/setup/enable_apis.ps1

# Create BigQuery dataset
./scripts/setup/create_bigquery.ps1

# Deploy Cloud Functions
./scripts/deploy/deploy_all.ps1
```

### 4. Run Web Application

```bash
cd web_app
streamlit run app.py
```

📖 **Detailed setup guide:** [docs/setup/DEPLOYMENT.md](docs/setup/DEPLOYMENT.md)

## Project Structure

```
├── ai/                    # AI abstraction layer (LLM, embeddings)
├── cloud_functions/       # GCP Cloud Functions for data ingestion
│   ├── gmail_sync/
│   ├── salesforce_sync/
│   ├── dialpad_sync/
│   └── hubspot_sync/
├── config/                # Configuration management
├── docs/                  # Documentation
│   ├── setup/             # Setup and deployment guides
│   ├── architecture/      # Technical architecture
│   ├── operations/        # Runbooks and troubleshooting
│   └── user-guides/       # End-user documentation
├── infrastructure/        # Terraform IaC
├── intelligence/          # AI features (scoring, NLP, search)
├── integrations/          # External API clients
├── scripts/               # Automation scripts
│   ├── setup/             # Initial setup
│   ├── deploy/            # Deployment
│   └── maintenance/       # Operations
├── tests/                 # Test suite
├── utils/                 # Shared utilities
└── web_app/               # Streamlit web application
```

## Configuration

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GCP_PROJECT_ID` | Google Cloud project ID | Yes |
| `GCP_REGION` | GCP region (default: us-central1) | No |
| `DATASET_ID` | BigQuery dataset name | No |
| `LLM_MODEL` | Vertex AI model (default: gemini-2.5-pro) | No |

### Required Secrets (Secret Manager)

- `salesforce-client-id`
- `salesforce-client-secret`
- `dialpad-api-key`
- `hubspot-api-key`

📖 **Configuration guide:** [docs/setup/CONFIGURATION.md](docs/setup/CONFIGURATION.md)

## Documentation

| Document | Description |
|----------|-------------|
| [Deployment Guide](docs/setup/DEPLOYMENT.md) | Complete deployment instructions |
| [Configuration](docs/setup/CONFIGURATION.md) | Environment and secrets setup |
| [Architecture](docs/architecture/SYSTEM_OVERVIEW.md) | System design and components |
| [API Reference](docs/architecture/API.md) | Cloud Functions API documentation |
| [Troubleshooting](docs/operations/TROUBLESHOOTING.md) | Common issues and solutions |
| [Operations Runbook](docs/operations/RUNBOOK.md) | Production operations guide |
| [Web App Guide](docs/user-guides/WEB_APP.md) | Web application usage |

### Role-Based Guides

| Guide | Audience |
|-------|----------|
| [Sales Rep Guide](docs/usage/SALES_REP_GUIDE.md) | Daily usage for sales team |
| [Manager Guide](docs/usage/MANAGER_GUIDE.md) | Visibility and coaching |
| [Engineering/Ops Guide](docs/usage/ENGINEERING_OPS_GUIDE.md) | Safe system interaction |

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
make lint

# Format code
make format
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Data Warehouse | Google BigQuery |
| ETL | Cloud Functions (Python 3.11) |
| Scheduling | Cloud Scheduler |
| AI/LLM | Vertex AI (Gemini 2.5 Pro) |
| Embeddings | textembedding-gecko@001 |
| Web App | Streamlit |
| Infrastructure | Terraform |
| Secrets | Secret Manager |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Client:** MaharaniWeddings.com  
**Contact:** anand@maharaniweddings.com
