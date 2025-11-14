# Sales Intelligence & Automation System

AI-driven sales intelligence and outreach system that unifies communication data and automates sales workflows across Salesforce, Gmail, Dialpad, and HubSpot.

## Project Overview

This system consolidates all customer interactions (emails, calls, CRM activities) in BigQuery and provides:
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

## Quick Start

### Project Configuration
- **GCP Project**: `maharani-sales-hub-11-2025`
- **Service Account**: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- **Region**: `us-central1`
- **BigQuery Dataset**: `sales_intelligence`

### Setup Instructions

1. **Prerequisites**
   - Google Cloud Platform account with billing enabled
   - Python 3.11+
   - GCP SDK installed and configured
   - Access to Salesforce, Gmail, Dialpad, and HubSpot APIs

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Setup Secrets**
   ```bash
   # Create secrets in Secret Manager
   ./scripts/setup_secrets.sh
   # Add secret values (see docs/SECRETS_LIST.md)
   ```

5. **Deploy Infrastructure**
   ```bash
   cd infrastructure
   cp terraform.tfvars.example terraform.tfvars
   terraform init
   terraform plan
   terraform apply
   ```

6. **Create BigQuery Tables**
   ```bash
   sed "s/{project_id}/maharani-sales-hub-11-2025/g" bigquery/schemas/create_tables.sql | \
     bq query --use_legacy_sql=false
   ```

7. **Deploy Cloud Functions**
   ```bash
   ./scripts/deploy_functions.sh
   ```

See [DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) for complete deployment guide.

## Project Phases

### Phase 1: Foundation & Data Pipeline ✅ (Completed - Ready for Deployment)
- [x] Project structure setup
- [x] BigQuery schema creation (with sync state tracking)
- [x] Gmail ingestion (with domain-wide delegation)
- [x] Salesforce sync (all objects)
- [x] Dialpad sync (calls + transcripts)
- [x] HubSpot sync (sequences metadata)
- [x] Entity resolution (email & phone matching)
- [x] Pub/Sub topics and subscriptions
- [x] Cloud Scheduler jobs (automated ingestion)
- [x] Error handling and monitoring
- [x] Automated test suite

### Phase 2: Intelligence & Automation
- [ ] Embeddings generation
- [ ] Vector search
- [ ] Daily account scoring
- [ ] Natural language queries
- [ ] Lead creation automation
- [ ] HubSpot enrollment
- [ ] AI email replies

### Phase 3: Application and UAT
- [ ] Web application development
- [ ] Authentication setup
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Documentation

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

## Contact

**Client**: Anand Gohel (anand@maharaniweddings.com)  
**Company**: MaharaniWeddings.com

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

