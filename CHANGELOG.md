# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Infrastructure & Deployment (2025-01-XX)
- Pub/Sub topics for Gmail, Salesforce, Dialpad, and HubSpot ingestion pipelines
- Dead letter queues (DLQ) for all ingestion topics
- Cloud Scheduler jobs for automated data ingestion with retry policies
- Service account configuration for `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- Gmail domain-wide delegation (DWD) implementation
- Gmail sync state table for incremental sync tracking
- Enhanced entity resolution with fuzzy matching and batch processing
- Entity resolution Cloud Function
- Comprehensive error handling with Pub/Sub notifications
- Performance monitoring utilities with context managers
- Health check endpoints
- Automated test suite (unit and integration tests)
- Documentation for HubSpot OAuth scopes
- Comprehensive secrets list documentation
- Deployment summary guide

### Changed
- Updated Gmail sync to use domain-wide delegation (no OAuth tokens required)
- Enhanced entity resolution with MERGE statements for efficient BigQuery updates
- Updated deployment scripts to use service account impersonation
- Enhanced BigQuery schemas with sync state tracking
- Improved error messages and logging throughout
- Better type hints throughout codebase

### Previous Additions
- Production-ready error handling with retry logic
- Comprehensive monitoring and observability
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Terraform infrastructure-as-code
- Caching layer for performance optimization
- Rate limiting utilities
- Comprehensive API documentation
- Security scanning integration
- Pre-commit hooks for code quality

## [1.0.0] - 2025-01-XX

### Added
- Initial project structure
- BigQuery schema definitions
- Gmail sync Cloud Function
- Salesforce sync Cloud Function
- Dialpad sync Cloud Function
- HubSpot sync Cloud Function
- Entity resolution logic
- ETL run tracking
- Basic unit tests
- Setup and architecture documentation

[Unreleased]: https://github.com/AI-God-Dev/Sales_Intelligence_Automation_System/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/AI-God-Dev/Sales_Intelligence_Automation_System/releases/tag/v1.0.0

