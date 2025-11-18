# Sales Intelligence & Automation System

AI-driven sales intelligence and outreach system that unifies communication data and automates sales workflows across Salesforce, Gmail, Dialpad, and HubSpot.

> **📖 New Owner?** Start with the **[HANDOFF_DOCUMENT.md](HANDOFF_DOCUMENT.md)** for complete handoff information, then follow **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** for setup instructions.

## Project Overview

This system consolidates all customer interactions (emails, calls, CRM activities) in BigQuery and provides a unified data warehouse for sales intelligence and automation.

### Phase 1: Data Foundation ✅ (Completed - Production Ready)
- Multi-source data ingestion (Gmail, Salesforce, Dialpad, HubSpot)
- Unified BigQuery data warehouse
- Entity resolution (email & phone matching)
- Automated sync scheduling
- Comprehensive monitoring and error handling

### Phase 2: Intelligence & Automation (Planned)
- Daily AI-powered account scoring and prioritization
- Automated lead creation from unmatched emails
- AI-generated email replies
- HubSpot sequence enrollment
- Natural language query interface
- Semantic search across all communications

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
 [Vector Search + LLM (Vertex AI / OpenAI)]
        │
        ▼
 [Web App – Query + Lead Dashboard + Actions]
```

## Technology Stack

- **Data Warehouse**: Google BigQuery
- **ETL/Ingestion**: Google Cloud Functions + Cloud Scheduler (Python 3.11)
- **LLM Provider**: Anthropic Claude API or Google Vertex AI
- **Embeddings**: OpenAI text-embedding-3-small or Vertex AI
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

### For New Users

1. **Read the Handoff Document** - Start here: [HANDOFF_DOCUMENT.md](HANDOFF_DOCUMENT.md)
2. **Follow Getting Started Guide** - Complete setup: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
3. **Use Deployment Checklist** - Step-by-step: [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)

### Project Configuration
- **GCP Project**: `maharani-sales-hub-11-2025`
- **Service Account**: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- **Region**: `us-central1`
- **BigQuery Dataset**: `sales_intelligence`

### Essential Setup Steps

1. **Prerequisites** - GCP account, Python 3.11+, `gcloud` CLI, API access
2. **Enable APIs** - Run `.\enable_apis.ps1`
3. **Configure Secrets** - Run `.\create_secrets.ps1`
4. **Setup Gmail DWD** - Follow [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)
5. **Create BigQuery Tables** - Run `.\scripts\setup_bigquery.ps1`
6. **Deploy Functions** - Run `.\scripts\deploy_functions.ps1`
7. **Test Everything** - Follow [docs/STEP_BY_STEP_TESTING_GUIDE.md](docs/STEP_BY_STEP_TESTING_GUIDE.md)

**📖 Detailed Instructions:** See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) and [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)

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

### Phase 2: Intelligence & Automation (Planned - Not Included)
- [ ] Embeddings generation
- [ ] Vector search
- [ ] Daily account scoring
- [ ] Natural language queries
- [ ] Lead creation automation
- [ ] HubSpot enrollment
- [ ] AI email replies

### Phase 3: Application and UAT (Planned - Not Included)
- [ ] Web application development
- [ ] Authentication setup
- [ ] User acceptance testing
- [ ] Performance optimization

**📖 Detailed Status:** See [PROJECT_STATUS.md](PROJECT_STATUS.md) and [docs/PHASE1_HANDOFF.md](docs/PHASE1_HANDOFF.md)

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

See [PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) for the complete production readiness checklist and [PRODUCTION_REVIEW_SUMMARY.md](docs/PRODUCTION_REVIEW_SUMMARY.md) for review details.

## Production Requirements

**⚠️ Important**: Before deploying to production, ensure you have:

1. **All Required Credentials** (see [Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)):
   - GCP project with billing enabled
   - Salesforce API credentials
   - Gmail OAuth credentials (for 3 mailboxes)
   - Dialpad API key
   - HubSpot API credentials
   - LLM provider API key (Anthropic/OpenAI/Vertex AI)

2. **Infrastructure Setup**:
   - GCP APIs enabled
   - Service accounts configured
   - Secret Manager secrets created
   - BigQuery dataset created

3. **Access & Permissions**:
   - Google Workspace admin access
   - Salesforce admin access
   - All users authorized for OAuth

See [DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) for complete requirements.

**⚠️ Important**: Adding credentials is just the first step! See [Getting Started Guide](docs/GETTING_STARTED.md) for the complete 8-step process to go from credentials to a running system.

## 📚 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| **[HANDOFF_DOCUMENT.md](HANDOFF_DOCUMENT.md)** | Complete handoff package - **Start here** |
| **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** | Step-by-step setup guide |
| **[docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)** | Deployment checklist |
| **[docs/STEP_BY_STEP_TESTING_GUIDE.md](docs/STEP_BY_STEP_TESTING_GUIDE.md)** | Testing procedures |
| **[docs/PHASE1_ENVIRONMENT_SETUP.md](docs/PHASE1_ENVIRONMENT_SETUP.md)** | Environment setup |
| **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** | Gmail DWD complete setup |
| **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Common issues and solutions |

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

