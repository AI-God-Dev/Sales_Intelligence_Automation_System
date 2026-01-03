# API Reference

Cloud Functions API documentation for the Sales Intelligence Automation System.

## Overview

All Cloud Functions are deployed as HTTP-triggered Gen2 functions in `us-central1`. Authentication is required via OIDC tokens.

## Data Ingestion APIs

### Gmail Sync

**Function:** `gmail-sync`

Syncs Gmail messages to BigQuery using Domain-Wide Delegation.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "incremental"}'
```

**Request:**
```json
{
  "sync_type": "incremental",    // "full" or "incremental"
  "mailbox": "user@example.com"  // Optional: specific mailbox
}
```

**Response:**
```json
{
  "status": "success",
  "messages_synced": 150,
  "errors": 0
}
```

### Salesforce Sync

**Function:** `salesforce-sync`

Syncs Salesforce objects to BigQuery.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"object_type": "Account"}'
```

**Request:**
```json
{
  "object_type": "Account",      // Account, Contact, Lead, Opportunity, Activity
  "sync_type": "incremental"     // "full" or "incremental"
}
```

**Response:**
```json
{
  "status": "success",
  "object_type": "Account",
  "rows_synced": 500
}
```

### Dialpad Sync

**Function:** `dialpad-sync`

Syncs Dialpad calls and transcripts.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

**Response:**
```json
{
  "status": "success",
  "calls_synced": 75
}
```

### HubSpot Sync

**Function:** `hubspot-sync`

Syncs HubSpot sequences metadata.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

**Response:**
```json
{
  "status": "success",
  "sequences_synced": 10
}
```

### Entity Resolution

**Function:** `entity-resolution`

Matches emails/phones to Salesforce contacts.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

**Response:**
```json
{
  "status": "success",
  "emails_matched": 500,
  "phones_matched": 200
}
```

---

## Intelligence APIs

### Account Scoring

**Function:** `account-scoring`

Generates AI-powered account priority scores.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

**Request:**
```json
{
  "limit": 100  // Optional: max accounts to score
}
```

**Response:**
```json
{
  "status": "success",
  "accounts_scored": 100,
  "duration_seconds": 45
}
```

### NLP Query

**Function:** `nlp-query`

Converts natural language to SQL and executes.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show top 10 accounts by revenue"}'
```

**Request:**
```json
{
  "query": "Show top 10 accounts by revenue"
}
```

**Response:**
```json
{
  "status": "success",
  "sql": "SELECT account_name, annual_revenue FROM...",
  "results": [...],
  "summary": "Here are the top 10 accounts..."
}
```

### Semantic Search

**Function:** `semantic-search`

Searches communications by intent.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"query": "budget discussions", "type": "emails"}'
```

**Request:**
```json
{
  "query": "budget discussions",
  "type": "emails",              // "emails", "calls", "accounts"
  "limit": 20,
  "min_similarity": 0.7
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "msg_123",
      "content": "...",
      "similarity": 0.85
    }
  ]
}
```

### Generate Embeddings

**Function:** `generate-embeddings`

Generates vector embeddings for content.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"type": "emails", "limit": 1000}'
```

**Request:**
```json
{
  "type": "emails",    // "emails", "calls", "both"
  "limit": 1000
}
```

---

## Automation APIs

### Create Leads

**Function:** `create-leads`

Creates Salesforce leads from unmatched emails.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"email_ids": ["msg_123", "msg_456"]}'
```

**Request:**
```json
{
  "email_ids": ["msg_123", "msg_456"]
}
```

### Enroll HubSpot

**Function:** `enroll-hubspot`

Enrolls contact in HubSpot sequence.

```bash
curl -X POST $FUNCTION_URL \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"contact_email": "user@example.com", "sequence_id": "seq_123"}'
```

**Request:**
```json
{
  "contact_email": "user@example.com",
  "sequence_id": "seq_123"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid credentials |
| 403 | Forbidden - Missing permissions |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |

---

## Authentication

All functions require OIDC authentication:

```bash
# Get token
TOKEN=$(gcloud auth print-identity-token)

# Call function
curl -X POST $URL -H "Authorization: Bearer $TOKEN"
```

For Cloud Scheduler, use service account with `roles/cloudfunctions.invoker`.

---

## Rate Limits

- 100 requests/minute per function
- Account scoring: 1 request/hour (scheduled)
- Embedding generation: 1 request/day (scheduled)

---

See also: [OpenAPI Specification](api/openapi.yaml)
