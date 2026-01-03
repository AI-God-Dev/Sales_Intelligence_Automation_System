# System Architecture

Technical architecture overview for the Sales Intelligence Automation System.

## Overview

The system is a multi-layer, enterprise-grade platform that ingests, centralizes, and analyzes sales communication data across Gmail, Salesforce, Dialpad, and HubSpot.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       WEB APPLICATION                           │
│  Streamlit Dashboard │ Search │ Queries │ Account Details      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                    INTELLIGENCE LAYER                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Scoring  │ │ NLP      │ │ Semantic │ │ Auto-    │          │
│  │ Engine   │ │ Query    │ │ Search   │ │ mation   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                     DATA WAREHOUSE                              │
│                   BigQuery (16 Tables)                          │
│         Vector Embeddings │ Partitioned │ Clustered            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                    INGESTION LAYER                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Gmail    │ │Salesforce│ │ Dialpad  │ │ HubSpot  │          │
│  │ Sync     │ │ Sync     │ │ Sync     │ │ Sync     │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                   EXTERNAL SYSTEMS                              │
│      Gmail API │ Salesforce API │ Dialpad API │ HubSpot API    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ingestion Layer

Cloud Functions that sync data from external systems to BigQuery.

| Function | Source | Schedule | Key Features |
|----------|--------|----------|--------------|
| `gmail-sync` | Gmail API | Hourly | Domain-Wide Delegation |
| `salesforce-sync` | Salesforce API | Daily | OAuth 2.0, incremental |
| `dialpad-sync` | Dialpad API | Daily | Transcripts, sentiment |
| `hubspot-sync` | HubSpot API | Daily | Sequences metadata |
| `entity-resolution` | BigQuery | After syncs | Email/phone matching |

### 2. Data Warehouse

BigQuery dataset with 16 core tables:

**Communication Tables**
- `gmail_messages` - Email messages with embeddings
- `gmail_participants` - Email addresses for resolution
- `dialpad_calls` - Call logs with transcripts

**CRM Tables**
- `sf_accounts` - Salesforce accounts
- `sf_contacts` - Salesforce contacts
- `sf_leads` - Salesforce leads
- `sf_opportunities` - Salesforce opportunities
- `sf_activities` - Tasks and events

**Integration Tables**
- `hubspot_sequences` - Available sequences
- `hubspot_enrollments` - Enrollment tracking
- `entity_resolution_emails` - Email matching
- `entity_resolution_phones` - Phone matching

**System Tables**
- `etl_runs` - Job execution tracking
- `account_recommendations` - AI-generated scores

### 3. Intelligence Layer

AI-powered features using Vertex AI (Gemini).

| Feature | Description | Function |
|---------|-------------|----------|
| Account Scoring | Daily priority scores | `account-scoring` |
| NLP Query | Natural language to SQL | `nlp-query` |
| Semantic Search | Intent-based search | `semantic-search` |
| Lead Creation | Auto-create Salesforce leads | `create-leads` |
| HubSpot Enrollment | Auto-enroll in sequences | `enroll-hubspot` |

### 4. Web Application

Streamlit-based dashboard with:
- Account priority dashboard
- Natural language query interface
- Semantic search
- Unmatched email management
- Account details view

## Data Flow

```
1. External APIs → Cloud Functions → BigQuery
2. BigQuery → Entity Resolution → Updated References
3. BigQuery + Vertex AI → Account Scores → BigQuery
4. Web App → Cloud Functions → BigQuery → Response
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
| Hosting | Cloud Run |

## Security

### Authentication Methods
- **Gmail**: Domain-Wide Delegation
- **Salesforce**: OAuth 2.0 Refresh Token
- **Dialpad**: API Key
- **HubSpot**: Private App Token
- **Vertex AI**: Application Default Credentials

### Data Security
- All secrets in Secret Manager
- Service account with least privilege
- HTTPS for all communications
- BigQuery access via IAM

## Performance

### Targets
- Email ingestion: 95%+ success rate
- Entity resolution: 90%+ match rate
- Account scoring: Complete by 8 AM daily
- NLP queries: < 10 seconds
- Semantic search: < 5 seconds

### Optimizations
- BigQuery partitioning by date
- Clustering on common query columns
- Vector embeddings as `ARRAY<FLOAT64>`
- Incremental sync for delta updates

## Scalability

- **BigQuery**: Handles petabytes
- **Cloud Functions**: Auto-scales
- **Cloud Run**: Scales to zero

## Monitoring

- Cloud Logging for all functions
- `etl_runs` table for job tracking
- BigQuery metrics for data quality
- Cloud Monitoring for alerts

---

See [API Reference](API.md) for detailed API documentation.

