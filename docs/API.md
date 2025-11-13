# API Documentation

## Overview

This document describes the API endpoints and interfaces for the Sales Intelligence & Automation System.

## Cloud Functions API

### Gmail Sync

**Endpoint**: `POST /gmail-sync`

**Description**: Syncs Gmail messages to BigQuery

**Request Body**:
```json
{
  "mailbox_email": "user@example.com",
  "sync_type": "incremental",
  "access_token": "oauth_access_token"
}
```

**Response**:
```json
{
  "status": "success",
  "messages_synced": 150,
  "errors": 0
}
```

**Error Response**:
```json
{
  "error": "mailbox_email and access_token required"
}
```

### Salesforce Sync

**Endpoint**: `POST /salesforce-sync`

**Description**: Syncs Salesforce objects to BigQuery

**Request Body**:
```json
{
  "object_type": "Account",
  "sync_type": "incremental"
}
```

**Response**:
```json
{
  "status": "success",
  "object_type": "Account",
  "rows_synced": 500,
  "errors": 0
}
```

### Dialpad Sync

**Endpoint**: `POST /dialpad-sync`

**Description**: Syncs Dialpad call logs to BigQuery

**Request Body**:
```json
{
  "user_id": "user123",
  "sync_type": "incremental"
}
```

**Response**:
```json
{
  "status": "success",
  "calls_synced": 75,
  "errors": 0
}
```

### HubSpot Sync

**Endpoint**: `POST /hubspot-sync`

**Description**: Syncs HubSpot sequences metadata

**Request Body**: `{}`

**Response**:
```json
{
  "status": "success",
  "sequences_synced": 10,
  "errors": 0
}
```

## Health Check

**Endpoint**: `GET /health`

**Description**: System health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "components": {
    "bigquery": {
      "status": "healthy"
    },
    "secret_manager": {
      "status": "healthy"
    }
  }
}
```

## Error Codes

- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Missing or invalid authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `500`: Internal Server Error - Server error
- `503`: Service Unavailable - Service temporarily unavailable

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- 100 requests per minute per IP
- 1000 requests per hour per API key

## Authentication

All endpoints require authentication via:
- OAuth 2.0 tokens (for Gmail)
- Service account credentials (for Cloud Functions)
- API keys (for external integrations)

## Versioning

API versioning is handled via URL path:
- `/v1/gmail-sync` (current)
- Future versions will use `/v2/`, etc.

