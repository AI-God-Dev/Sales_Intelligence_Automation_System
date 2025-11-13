# System Architecture

## Overview

The Sales Intelligence & Automation System follows a cloud-native architecture with five primary layers:

1. **Data Ingestion Layer**: Cloud Functions extract data from source APIs
2. **Data Warehouse Layer**: BigQuery stores normalized, queryable data
3. **Entity Resolution Layer**: Matches emails/calls to Salesforce contacts and accounts
4. **Intelligence Layer**: LLM-powered semantic search, scoring, and email generation
5. **Application Layer**: Web UI for queries, dashboards, and automation actions

## Data Flow

```
┌─────────────┐
│ Gmail API   │
└──────┬──────┘
       │
┌──────▼──────┐
│ Salesforce  │
│    API      │
└──────┬──────┘
       │
┌──────▼──────┐      ┌──────────────────┐
│  Dialpad    │─────►│  Cloud Functions │
│    API      │      │  (ETL Jobs)      │
└──────┬──────┘      └────────┬─────────┘
       │                      │
┌──────▼──────┐              │
│  HubSpot    │              │
│    API      │              │
└─────────────┘              │
                             ▼
                    ┌─────────────────┐
                    │    BigQuery     │
                    │   Data Warehouse│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Entity Resolution│
                    │    (Matching)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Vector Search  │
                    │  + LLM (Claude) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Web App       │
                    │  (Streamlit/    │
                    │   Next.js)      │
                    └─────────────────┘
```

## Components

### 1. Data Ingestion (Cloud Functions)

**Gmail Sync** (`cloud_functions/gmail_sync/`)
- Full historical sync + incremental sync using historyId
- Extracts: message ID, thread ID, participants, subject, body, labels
- Stores in `gmail_messages` and `gmail_participants` tables

**Salesforce Sync** (`cloud_functions/salesforce_sync/`)
- Syncs: Account, Contact, Lead, Opportunity, Task, Event
- Incremental sync based on LastModifiedDate
- Weekly full refresh for data integrity

**Dialpad Sync** (`cloud_functions/dialpad_sync/`)
- Extracts call logs and transcripts
- Normalizes phone numbers to E.164 format
- Stores in `dialpad_calls` table

**HubSpot Sync** (`cloud_functions/hubspot_sync/`)
- Syncs available sequences metadata
- Stores in `hubspot_sequences` table

### 2. Data Warehouse (BigQuery)

**Schema Design**
- Partitioned by date for time-series data (emails, calls, activities)
- Clustered by common query patterns (email, account_id, owner_id)
- Vector embeddings stored as ARRAY<FLOAT64> for semantic search

**Key Tables**
- `gmail_messages`: All emails with embeddings
- `gmail_participants`: Email addresses for entity resolution
- `sf_accounts`, `sf_contacts`, `sf_leads`, `sf_opportunities`: CRM data
- `dialpad_calls`: Call logs with transcripts and embeddings
- `account_recommendations`: Daily AI-generated scores
- `etl_runs`: ETL job execution tracking

### 3. Entity Resolution

**Matching Strategy**
1. **Email Matching**: Exact match on normalized email address
2. **Phone Matching**: E.164 normalization + partial match (last 10 digits)
3. **Manual Overrides**: `manual_mappings` table for explicit mappings

**Process**
- Runs after each data ingestion
- Updates `gmail_participants.sf_contact_id` and `sf_account_id`
- Weekly reconciliation job re-runs matching

### 4. Intelligence Layer

**Embeddings Generation**
- OpenAI `text-embedding-3-small` or Vertex AI embeddings
- Generated for: email body text, call transcripts
- Stored in BigQuery ARRAY<FLOAT64> columns

**Vector Search**
- BigQuery Vector Search with cosine similarity
- Enables semantic queries like "accounts discussing budget"

**Account Scoring**
- Daily job runs before 8 AM
- Aggregates: last 5 emails, last 3 calls, open opportunities, recent activities
- LLM analyzes and generates priority score, budget likelihood, engagement score
- Stores in `account_recommendations` table

**Natural Language Queries**
- LLM converts natural language to SQL
- Safety validation (SELECT only, no DROP/DELETE/UPDATE)
- Results summarized by LLM in natural language

### 5. Application Layer

**Web Application** (Streamlit or Next.js)
- Dashboard: Daily priority accounts
- Query Interface: Natural language questions
- Unmatched Emails View: Lead creation workflow
- Account Detail View: Timeline of interactions
- Email Thread View: AI reply generation

**Authentication**
- Google Workspace SSO (OAuth 2.0)
- Restricted to MaharaniWeddings.com domain

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Data Warehouse | Google BigQuery |
| ETL/Ingestion | Google Cloud Functions (Python 3.11) |
| Scheduling | Google Cloud Scheduler |
| LLM Provider | Anthropic Claude API or Google Vertex AI |
| Embeddings | OpenAI text-embedding-3-small or Vertex AI |
| Vector Search | BigQuery Vector Search |
| Web Application | Streamlit or Next.js |
| Hosting | Google Cloud Run |
| Authentication | Google Workspace OAuth |
| Secrets Management | Google Secret Manager |

## Security

- **Encryption**: At rest (BigQuery default) and in transit (HTTPS/TLS 1.2+)
- **Secrets**: Stored in Google Secret Manager, never in code
- **Access Control**: IAM roles with least privilege
- **API Security**: OAuth 2.0 for all integrations, read-only scopes where possible
- **Audit Logging**: Cloud Audit Logs enabled for all GCP services

## Scalability

- **BigQuery**: Handles petabyte-scale data with automatic scaling
- **Cloud Functions**: Auto-scales based on request volume
- **Partitioning**: Tables partitioned by date for efficient queries
- **Clustering**: Optimized for common query patterns
- **Caching**: Query results cached where appropriate

## Monitoring

- **ETL Runs**: Tracked in `etl_runs` table with success/failure status
- **Data Quality**: Match percentages monitored (target: 90%+ email, 85%+ calls)
- **Performance**: Query execution times logged
- **Errors**: Structured logging with Google Cloud Logging

## Future Enhancements

- Real-time webhooks (beyond daily scheduled jobs)
- Custom LLM fine-tuning
- Advanced BI dashboards
- Multi-language support
- Role-based access control for larger teams

