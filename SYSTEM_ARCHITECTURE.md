# Sales Intelligence Automation System - System Architecture

## Executive Summary

The Sales Intelligence Automation System is a **multi-layer, enterprise-grade platform** designed to ingest, centralize, and analyze sales communication data across Gmail, Salesforce, Dialpad, and HubSpot. The system provides AI-powered intelligence, semantic search, account scoring, and automation capabilities through a professional web application interface.

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Streamlit Web Application (Phase 3)                     │   │
│  │  - Account Dashboard                                     │   │
│  │  - Semantic Search                                       │   │
│  │  - Natural Language Queries                              │   │
│  │  - Unmatched Email Resolution                            │   │
│  │  - HubSpot Sequence Enrollment                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  INTELLIGENCE LAYER (Phase 2)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Embeddings  │  │   Scoring    │  │  Semantic    │         │
│  │  Generation  │  │   Engine     │  │   Search     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  NLP Query   │  │  Automation  │  │  Insights    │         │
│  │  Generator   │  │  (Leads/HS)  │  │  Generator   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (Phase 1)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  BigQuery Data Warehouse                                 │   │
│  │  - 16 Core Tables                                        │   │
│  │  - Vector Embeddings (ARRAY<FLOAT64>)                    │   │
│  │  - Partitioned & Clustered for Performance               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  INGESTION LAYER (Phase 1)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Gmail Sync  │  │ Salesforce   │  │   Dialpad    │         │
│  │  (DWD/OAuth) │  │    Sync      │  │    Sync      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  HubSpot     │  │   Entity     │                            │
│  │    Sync      │  │ Resolution   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL SYSTEMS                                │
│  Gmail │ Salesforce │ Dialpad │ HubSpot │ Vertex AI │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Data Ingestion (Phase 1)

### 1.1 Gmail Ingestion

**Technology**: Google Cloud Functions Gen2, Gmail API, Domain-Wide Delegation (DWD)

**Process**:
1. **Authentication**: Uses Domain-Wide Delegation for service account access to 3 mailboxes
2. **Sync Strategy**: 
   - Full sync: Initial historical data load
   - Incremental sync: Uses Gmail history API for delta updates
   - Sync state tracked in `gmail_sync_state` table
3. **Data Extracted**:
   - Message metadata (subject, from, to, cc, sent_at)
   - Body content (text and HTML)
   - Thread relationships
   - Labels
4. **Storage**: `gmail_messages` and `gmail_participants` tables

**Cloud Function**: `gmail-sync`
- Entry Point: `cloud_functions.gmail_sync.main.gmail_sync`
- Trigger: Cloud Scheduler (hourly) or HTTP POST
- Memory: 512MB
- Timeout: 540 seconds

### 1.2 Salesforce Ingestion

**Technology**: Salesforce REST API, OAuth 2.0 Refresh Token Flow

**Objects Synced**:
- Accounts
- Contacts
- Leads
- Opportunities
- Activities (Tasks, Events)
- EmailMessages (optional)

**Process**:
1. **Authentication**: OAuth 2.0 with refresh token stored in Secret Manager
2. **Sync Strategy**:
   - Full sync: Daily at 2 AM
   - Incremental sync: Uses LastModifiedDate for delta updates
   - Reconciliation: Weekly full re-sync
3. **Data Quality**: Validates required fields, handles missing data gracefully

**Cloud Function**: `salesforce-sync`
- Entry Point: `cloud_functions.salesforce_sync.main.salesforce_sync`
- Trigger: Cloud Scheduler (daily) or HTTP POST
- Memory: 512MB
- Timeout: 540 seconds

### 1.3 Dialpad Ingestion

**Technology**: Dialpad REST API, Private API Key

**Data Extracted**:
- Call logs (direction, duration, participants)
- Call transcripts (full text)
- Sentiment scores (Dialpad AI)
- Call metadata (timestamps, user IDs)

**Process**:
1. **Authentication**: API key stored in Secret Manager
2. **Sync Strategy**: Daily incremental sync based on call_time
3. **Transcript Processing**: Full transcripts stored in `dialpad_calls` and `dialpad_transcripts` tables

**Cloud Function**: `dialpad-sync`
- Entry Point: `cloud_functions.dialpad_sync.main.dialpad_sync`
- Trigger: Cloud Scheduler (daily) or HTTP POST
- Memory: 512MB
- Timeout: 540 seconds

### 1.4 HubSpot Ingestion

**Technology**: HubSpot Private App API

**Data Extracted**:
- Sequences (available sequences for enrollment)
- Sequence metadata (name, active status, enrollment counts)

**Process**:
1. **Authentication**: Private App access token (pat-* format)
2. **Sync Strategy**: Daily sync of sequence metadata
3. **Enrollment Tracking**: Enrollments tracked in `hubspot_enrollments` table

**Cloud Function**: `hubspot-sync`
- Entry Point: `cloud_functions.hubspot_sync.main.hubspot_sync`
- Trigger: Cloud Scheduler (daily) or HTTP POST
- Memory: 512MB
- Timeout: 540 seconds

### 1.5 Entity Resolution

**Technology**: Python matching algorithms, BigQuery

**Matching Strategy**:
1. **Email Matching**:
   - Exact match on normalized email address
   - Domain-based matching (fallback)
   - Fuzzy matching (Levenshtein distance)
   - Manual overrides (via `manual_mappings` table)
2. **Phone Matching**:
   - E.164 normalization
   - Exact match on normalized number
   - Partial match (last 10 digits)
   - Manual overrides

**Process**:
1. Runs after each data ingestion
2. Updates `gmail_participants.sf_contact_id` and `sf_account_id`
3. Writes results to `entity_resolution_emails` and `entity_resolution_phones` tables
4. Weekly reconciliation job re-runs matching

**Cloud Function**: `entity-resolution`
- Entry Point: `cloud_functions.entity_resolution.main.entity_resolution`
- Trigger: After each sync or HTTP POST
- Memory: 512MB
- Timeout: 540 seconds

---

## Layer 2: Data Warehouse (BigQuery)

### 2.1 Schema Design

**Dataset**: `sales_intelligence`
**Location**: `us-central1` (configurable)

### 2.2 Core Tables (16 Required Tables)

1. **gmail_messages**: All emails with embeddings
2. **gmail_participants**: Email addresses for entity resolution
3. **sf_accounts**: Salesforce Account records
4. **sf_contacts**: Salesforce Contact records
5. **sf_leads**: Salesforce Lead records
6. **sf_opportunities**: Salesforce Opportunity records
7. **sf_activities**: Salesforce Tasks, Events, Activities
8. **dialpad_calls**: Call logs with transcripts and embeddings
9. **dialpad_transcripts**: Detailed call transcript segments
10. **hubspot_sequences**: Available HubSpot sequences
11. **hubspot_enrollments**: Sequence enrollment tracking
12. **entity_resolution_emails**: Email matching results
13. **entity_resolution_phones**: Phone matching results
14. **etl_runs**: ETL job execution tracking
15. **account_recommendations**: Daily AI-generated scores
16. **semantic_embeddings**: Centralized embeddings storage (optional)

### 2.3 Performance Optimizations

- **Partitioning**: Time-series tables partitioned by date (sent_at, call_time, activity_date)
- **Clustering**: Tables clustered by common query patterns (email, account_id, owner_id)
- **Vector Storage**: Embeddings stored as `ARRAY<FLOAT64>` for native vector search
- **Views**: Pre-computed views for common queries (e.g., `v_unmatched_emails`)

### 2.4 Data Quality

- **ETL Tracking**: All syncs logged in `etl_runs` table
- **Error Handling**: Failed rows tracked with error messages
- **Idempotency**: All ingestion functions are idempotent (safe to re-run)
- **Validation**: Input validation before BigQuery writes

---

## Layer 3: AI Intelligence (Phase 2)

### 3.1 Unified Model Abstraction Layer

**Location**: `ai/` directory

**Components**:
- `ai/models.py`: LLM provider abstraction (Vertex AI only, with Mock mode for testing)
- `ai/embeddings.py`: Embedding provider abstraction
- `ai/semantic_search.py`: Semantic search provider
- `ai/scoring.py`: Account scoring provider
- `ai/summarization.py`: Text summarization provider
- `ai/insights.py`: Insights generation provider

**Key Features**:
- **Provider Switching**: Seamless switching between providers via environment variables
- **MOCK_MODE**: Fake responses for testing without API calls
- **LOCAL_MODE**: Local implementations using numpy, SQLite
- **Error Handling**: Comprehensive error handling and retry logic
- **Rate Limiting**: Built-in rate limiting for API calls

### 3.2 Embeddings Generation

**Sources**:
- Gmail email bodies (subject + body)
- Salesforce activity notes
- Salesforce opportunity descriptions
- Dialpad call transcripts
- HubSpot sequence content

**Models**:
- Vertex AI: `textembedding-gecko@001` (768 dimensions) - THE ONLY PERMITTED EMBEDDING MODEL

**Storage**:
- Primary: `gmail_messages.embedding`, `dialpad_calls.embedding`
- Centralized: `semantic_embeddings` table (optional)

**Cloud Function**: `generate-embeddings`
- Entry Point: `intelligence.embeddings.main.generate_embeddings`
- Trigger: Cloud Scheduler (daily) or HTTP POST
- Memory: 1024MB
- Timeout: 540 seconds

### 3.3 Semantic Search

**Technology**: BigQuery Vector Search with cosine similarity

**Capabilities**:
- Search emails by intent (e.g., "budget discussions for 2026")
- Search calls by intent (e.g., "renewal concerns")
- Cross-content semantic search

**Implementation**:
- Query embedding generated using same model as content
- Cosine similarity calculated in BigQuery
- Results ranked by similarity score
- Configurable similarity threshold (default: 0.7)

**Cloud Function**: `vector-search`
- Entry Point: `intelligence.vector_search.main.vector_search`
- Trigger: HTTP POST (called from web app)
- Memory: 512MB
- Timeout: 60 seconds

### 3.4 Account Scoring

**Process**:
1. Aggregates account data:
   - Last 5 emails
   - Last 3 calls
   - Open opportunities
   - Recent activities
2. LLM Analysis:
   - Generates priority score (0-100)
   - Budget likelihood (0-100)
   - Engagement score (0-100)
   - Reasoning and recommendations
3. Storage: Results stored in `account_recommendations` table

**Cloud Function**: `account-scoring`
- Entry Point: `intelligence.scoring.main.account_scoring_job`
- Trigger: Cloud Scheduler (daily at 7 AM)
- Memory: 1024MB
- Timeout: 540 seconds

### 3.5 Natural Language Queries

**Process**:
1. User submits natural language question
2. LLM converts to BigQuery SQL
3. Safety validation (SELECT only, no DROP/DELETE/UPDATE)
4. Query executed against BigQuery
5. Results summarized by LLM in natural language

**Cloud Function**: `nlp-query`
- Entry Point: `intelligence.nlp_query.main.nlp_query`
- Trigger: HTTP POST (called from web app)
- Memory: 512MB
- Timeout: 60 seconds

### 3.6 Automation

**Lead Creation**:
- Creates Salesforce Leads from unmatched emails
- Sets lead source: "AI Inbound Email"
- Links to source Gmail message

**HubSpot Enrollment**:
- Enrolls contacts in HubSpot sequences
- Tracks enrollments in `hubspot_enrollments` table
- Handles errors gracefully

**Cloud Functions**:
- `create-lead`: `intelligence.automation.main.create_lead`
- `enroll-hubspot`: `intelligence.automation.main.enroll_hubspot`

---

## Layer 4: Web Application (Phase 3)

### 4.1 Technology Stack

- **Framework**: Streamlit
- **Language**: Python 3.11
- **Deployment**: Cloud Run (or local)
- **Authentication**: Google OAuth (optional, simple email auth for now)

### 4.2 Pages

1. **Dashboard**: Real-time metrics, top priority accounts
2. **Account Scoring**: AI-powered account scores with charts
3. **Natural Language Query**: Ask questions in plain English
4. **Semantic Search**: AI-powered intent-based search
5. **Unmatched Emails**: Create leads from unmatched emails
6. **Account Details**: Complete account information view
7. **Email Threads**: View conversations and generate AI replies

### 4.3 Integration

- All data pulls through centralized query functions
- AI calls wrapped with error handling
- Supports LOCAL_MODE for offline development
- Professional UI/UX with custom CSS

---

## Deployment Architecture

### 5.1 Cloud Functions Gen2

**Runtime**: Python 3.11
**Deployment**: From project root using `--source=.`
**Entry Points**: Full module paths (e.g., `cloud_functions.gmail_sync.main.gmail_sync`)

**Total Functions**: 13
- Phase 1: 5 ingestion functions
- Phase 2: 6 intelligence functions
- Phase 2: 2 automation functions

### 5.2 Cloud Scheduler

**Jobs**:
- Gmail sync: Hourly
- Salesforce sync: Daily at 2 AM
- Dialpad sync: Daily at 3 AM
- HubSpot sync: Daily at 4 AM
- Entity resolution: After each sync
- Embeddings generation: Daily at 5 AM
- Account scoring: Daily at 7 AM

### 5.3 Secret Manager

**Secrets Stored**:
- Salesforce OAuth credentials
- Dialpad API key
- HubSpot API key
- Note: Vertex AI uses Application Default Credentials (ADC) - no API keys needed

### 5.4 IAM Roles

**Service Account**: `sales-intelligence-sa@PROJECT_ID.iam.gserviceaccount.com`
- BigQuery Data Editor
- BigQuery Job User
- Secret Manager Secret Accessor
- Cloud Functions Invoker
- AI Platform User (for Vertex AI)

---

## Security & Compliance

### 6.1 Authentication

- **Gmail**: Domain-Wide Delegation (service account)
- **Salesforce**: OAuth 2.0 Refresh Token Flow
- **Dialpad**: Private API Key
- **HubSpot**: Private App Access Token
- **Web App**: Google OAuth (optional)

### 6.2 Data Security

- All secrets stored in Google Secret Manager
- No credentials in code or environment variables
- BigQuery access via service account
- HTTPS only for all external communications

### 6.3 Compliance

- Data retention: 3 years (configurable)
- Audit logging: All ETL runs logged
- Error tracking: Failed operations logged with details

---

## Scalability & Performance

### 7.1 Scalability

- **BigQuery**: Handles petabytes of data
- **Cloud Functions**: Auto-scales based on load
- **Partitioning**: Enables efficient querying of large datasets
- **Clustering**: Optimizes query performance

### 7.2 Performance Targets

- Email ingestion: 95%+ success rate
- Entity resolution: 90%+ match rate
- Account scoring: Delivered by 8 AM daily
- NLP queries: Results in under 10 seconds
- Semantic search: Results in under 5 seconds

---

## Monitoring & Observability

### 8.1 Logging

- All functions log to Cloud Logging
- Structured logging with context
- Error tracking with stack traces

### 8.2 Metrics

- ETL run status tracked in `etl_runs` table
- Success/failure rates
- Processing times
- Row counts

### 8.3 Alerts

- Failed ETL runs
- Account scoring job failures
- High error rates

---

## Local Development

### 9.1 LOCAL_MODE

- Mock AI responses
- Local SQLite database (optional)
- Local embeddings using numpy
- No external API calls

### 9.2 MOCK_MODE

- Fake AI responses
- Deterministic outputs
- Fast testing without API costs

### 9.3 Functions Framework

- Run Cloud Functions locally
- Test ingestion pipelines
- Debug without deploying

---

## Future Enhancements

- Real-time streaming ingestion (Pub/Sub)
- Advanced ML models for scoring
- Multi-language support
- Mobile app
- Advanced analytics dashboard
- Custom report generation

---

## Conclusion

The Sales Intelligence Automation System is a comprehensive, enterprise-grade platform that provides end-to-end sales intelligence capabilities. The architecture is designed for scalability, reliability, and maintainability, with clear separation of concerns across ingestion, storage, intelligence, and presentation layers.
