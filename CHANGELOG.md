# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-03

### Added
- **Production Readiness**
  - SQL injection prevention with parameterized BigQuery queries
  - Comprehensive input validation across all endpoints
  - Enhanced error handling for Vertex AI responses
  - ResponseBlockedError handling for AI safety filters

- **AI Intelligence Layer**
  - Unified AI abstraction layer (`ai/` directory)
  - Account scoring with Gemini 2.5 Pro
  - Natural language to SQL query generation
  - Semantic search with vector embeddings
  - AI-generated email replies

- **Web Application**
  - Full Streamlit dashboard
  - Account priority visualization
  - Natural language query interface
  - Semantic search UI
  - Unmatched email management

### Changed
- Reorganized documentation structure
  - `docs/setup/` - Deployment and configuration
  - `docs/architecture/` - System design
  - `docs/operations/` - Runbooks and troubleshooting
  - `docs/user-guides/` - End-user documentation

- Reorganized scripts structure
  - `scripts/setup/` - Initial setup scripts
  - `scripts/deploy/` - Deployment scripts
  - `scripts/test/` - Testing and validation
  - `scripts/maintenance/` - Operations scripts

- Updated LLM model to `gemini-2.5-pro`
- Improved error messages throughout

### Removed
- Redundant documentation files
- Obsolete fix summary documents
- Duplicate application files

### Security
- Fixed SQL injection vulnerabilities in web app
- Added input validation for all user inputs
- Parameterized all BigQuery queries

## [1.0.0] - 2025-01-XX

### Added
- **Data Ingestion Layer**
  - Gmail sync with Domain-Wide Delegation
  - Salesforce sync with OAuth 2.0
  - Dialpad sync with API key auth
  - HubSpot sync with Private App token
  - Entity resolution (email/phone matching)

- **Data Warehouse**
  - BigQuery dataset with 16 tables
  - Partitioned and clustered tables
  - Vector embedding storage
  - ETL run tracking

- **Infrastructure**
  - Cloud Functions (Gen2) deployment
  - Cloud Scheduler jobs
  - Secret Manager integration
  - Terraform IaC

- **Testing**
  - Unit test suite
  - Integration tests
  - Mock mode for offline testing

### Technical Details
- Python 3.11+ runtime
- Vertex AI for LLM and embeddings
- BigQuery for data warehouse
- Cloud Run for web application

---

For upgrade instructions, see [docs/setup/DEPLOYMENT.md](docs/setup/DEPLOYMENT.md).
