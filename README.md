# Sales Intelligence & Automation System

AI-driven sales intelligence and outreach system that unifies communication data and automates sales workflows across Salesforce, Gmail, Dialpad, and HubSpot.

> **📖 New to this project?** Start with **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** for complete deployment instructions, or use **[DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)** for a fast-track deployment.

> **🏗️ Architecture & AI System:** See **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** for system design and **[AI_SYSTEM_GUIDE.md](AI_SYSTEM_GUIDE.md)** for AI capabilities.

> **🧪 Testing & Operations:** See **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** for local development and **[RUNBOOK_OPERATIONS.md](RUNBOOK_OPERATIONS.md)** for production operations.

## Project Overview

This system consolidates all customer interactions (emails, calls, CRM activities) in BigQuery and provides a unified data warehouse for sales intelligence and automation.

### Phase 1: Data Foundation ✅ (Completed - Production Ready)
- Multi-source data ingestion (Gmail, Salesforce, Dialpad, HubSpot)
- Unified BigQuery data warehouse
- Entity resolution (email & phone matching)
- Automated sync scheduling
- Comprehensive monitoring and error handling

### Phase 2: Intelligence & Automation ✅ (Completed - Production Ready)
- **Unified AI Abstraction Layer** (`ai/` directory) - Provider-agnostic LLM and embedding interfaces
- **MOCK_MODE & LOCAL_MODE** - Full offline testing capabilities
- Daily AI-powered account scoring and prioritization
- Automated lead creation from unmatched emails
- AI-generated email replies
- HubSpot sequence enrollment
- Natural language query interface
- Semantic search across all communications
- BigQuery Vector Search implementation

## Architecture

```
[Gmail API]──┐
[Salesforce API]──┼──► Cloud Functions → BigQuery
[Dialpad API]──┤
[HubSpot API]──┘
        │
        ▼
 ┌─────────────────────────────────────────────┐
 │              BigQuery Warehouse             │
 └─────────────────────────────────────────────┘
        │
        ▼
 [Vector Search + LLM (Vertex AI)]
        │
        ▼
 [Web App – Query + Lead Dashboard + Actions]
```

## Technology Stack

- **Data Warehouse**: Google BigQuery
- **ETL/Ingestion**: Google Cloud Functions + Cloud Scheduler (Python 3.11)
- **LLM Provider**: Google Vertex AI (Gemini models)
- **Embeddings**: Vertex AI textembedding-gecko@001
- **Vector Search**: BigQuery Vector Search
- **Web Application**: Streamlit or Next.js
- **Hosting**: Google Cloud Run
- **Authentication**: Google Workspace OAuth

## Project Structure

```
.
├── cloud_functions/          # GCP Cloud Functions for data ingestion
│   ├── gmail_sync/
│   ├── salesforce_sync/
│   ├── dialpad_sync/
│   ├── hubspot_sync/
│   └── entity_resolution/
├── bigquery/                 # Schema definitions and SQL scripts
│   ├── schemas/
│   └── queries/
├── intelligence/             # AI/LLM integration code
│   ├── scoring/
│   ├── embeddings/
│   └── nlp_query/
├── web_app/                  # Web application (Streamlit/Next.js)
├── infrastructure/           # Terraform/IaC configurations
├── tests/                    # Unit and integration tests
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## 🚀 Quick Start

### Fast Deployment (4 Steps)

1. **Set Environment Variables** - Configure your GCP project ID and region
2. **Setup Service Account** - Run `.\scripts\setup_service_account.ps1`
3. **Create BigQuery Dataset** - Run `.\scripts\create_bigquery_datasets.ps1`
4. **Deploy All Functions** - Run `.\scripts\deploy_all.ps1`

**📖 Detailed Instructions:** See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for complete step-by-step guide.

**⚡ Quick Reference:** See [DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md) for fast-track deployment.

## 📊 Project Status

### Phase 1: Foundation & Data Pipeline ✅ **COMPLETE**

**Status:** ✅ Production Ready | **Tests:** 45/45 passing (100%) | **Coverage:** 30% overall

**Completed Components:**
- [x] Project structure setup
- [x] BigQuery schema creation (13 tables with sync state tracking)
- [x] Gmail ingestion (with domain-wide delegation)
- [x] Salesforce sync (all objects: Account, Contact, Lead, Opportunity, Activity)
- [x] Dialpad sync (calls + transcripts)
- [x] HubSpot sync (sequences metadata)
- [x] Entity resolution (email & phone matching)
- [x] Pub/Sub topics and subscriptions
- [x] Cloud Scheduler jobs (automated ingestion)
- [x] Comprehensive error handling and monitoring
- [x] Automated test suite (45 tests, 100% pass rate)
- [x] Complete documentation

### Phase 2: Intelligence & Automation ✅ (Completed - Production Ready)
- ✅ Embeddings generation
- ✅ Vector search
- ✅ Daily account scoring
- ✅ Natural language queries
- ✅ Lead creation automation
- ✅ HubSpot enrollment
- ✅ AI email replies

### Phase 3: Application and UAT ✅ (Completed - Production Ready)
- ✅ Web application development (Streamlit)
- ✅ Authentication setup (Google OAuth ready)
- ✅ Complete dashboard and views
- ✅ Mobile-responsive design

## Success Criteria

- 95%+ of emails successfully ingested and linked to Salesforce contacts
- 90%+ of known contacts matched to correct Salesforce accounts
- Daily account scores delivered by 8 AM each morning
- Natural language queries return results in under 10 seconds
- AI-generated email replies are contextually accurate and editable
- HubSpot sequence enrollments succeed with 98%+ success rate

## Production Readiness

**✅ Production-Ready Features**:
- Comprehensive input validation and sanitization
- SQL injection prevention
- Secure secret management
- Robust error handling with user-friendly messages
- Monitoring and observability
- Complete documentation
- Unified AI abstraction layer with provider switching
- MOCK_MODE and LOCAL_MODE for testing

## Documentation

### Core Documentation
- **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** - Complete deployment guide
- **[DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)** - Fast-track deployment
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### Architecture & Design
- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Complete system architecture
- **[AI_SYSTEM_GUIDE.md](AI_SYSTEM_GUIDE.md)** - AI system usage and configuration
- **[WEB_APP_GUIDE.md](WEB_APP_GUIDE.md)** - Web application guide

### Operations & Testing
- **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** - Local development and testing
- **[RUNBOOK_OPERATIONS.md](RUNBOOK_OPERATIONS.md)** - Production operations guide
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Development roadmap

### Handoff & Validation
- **[HANDOFF_DOCUMENT.md](HANDOFF_DOCUMENT.md)** - Complete project handoff document
- **[FINAL_VALIDATION_CHECKLIST.md](FINAL_VALIDATION_CHECKLIST.md)** - Pre-deployment validation checklist
- **[PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md)** - Project completion summary

### Additional Resources
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture documentation
- **[docs/API.md](docs/API.md)** - API reference
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Configuration guide

## Production Requirements

**⚠️ Important**: Before deploying to production, ensure you have:

1. **All Required Credentials**:
   - GCP project with billing enabled
   - Salesforce API credentials
   - Gmail OAuth credentials (for mailboxes)
   - Dialpad API key
   - HubSpot API credentials
   - GCP Project ID (Vertex AI uses Application Default Credentials - no API keys needed)

2. **Infrastructure Setup**:
   - GCP APIs enabled
   - Service accounts configured
   - Secret Manager secrets created
   - BigQuery dataset created

3. **Access & Permissions**:
   - Google Workspace admin access
   - Salesforce admin access
   - All users authorized for OAuth

See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for complete deployment instructions.

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** | Complete deployment guide - **Start here!** |
| **[DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)** | Fast-track deployment (4 steps) |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and solutions |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | System architecture overview |
| **[docs/API.md](docs/API.md)** | API documentation |
| **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** | Configuration guide |

## 📞 Contact

**Client**: Anand Gohel (anand@maharaniweddings.com)  
**Company**: MaharaniWeddings.com  
**Project**: Sales Intelligence & Automation System

## Development

### Setup

```bash
# Install dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Run linters
make lint
```

### Docker Development

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## CI/CD

The project uses GitHub Actions for continuous integration:
- Automated testing on push/PR
- Code quality checks (linting, formatting)
- Security scanning
- Docker image building
- Automated deployment to staging/production

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) file for details.

