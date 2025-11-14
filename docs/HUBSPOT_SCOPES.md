# HubSpot OAuth Scopes for Private App

This document lists the required OAuth scopes for the HubSpot Private App used in the Sales Intelligence system.

## Required Scopes

The following scopes are necessary for reading contacts, companies, and sequences:

### Contacts Scopes
- **`contacts.read`** - Read access to contacts
  - Required for: Reading contact information, email addresses, phone numbers
  - Used in: Entity resolution, contact matching

### Companies Scopes
- **`companies.read`** - Read access to companies
  - Required for: Reading company information, account data
  - Used in: Account matching, entity resolution

### Sequences Scopes
- **`sequences.read`** - Read access to sequences
  - Required for: Reading sequence metadata, enrollment information
  - Used in: HubSpot sync function, sequence enrollment automation

- **`sequences.write`** - Write access to sequences
  - Required for: Enrolling contacts in sequences
  - Used in: Automated sequence enrollment feature

### Additional Recommended Scopes
- **`timeline.read`** - Read access to timeline events
  - Optional but recommended for: Tracking engagement history
  - Used in: Activity tracking, engagement scoring

- **`timeline.write`** - Write access to timeline events
  - Optional but recommended for: Creating timeline events
  - Used in: Activity logging

## Scope Summary

**Minimum Required Scopes:**
```
contacts.read
companies.read
sequences.read
sequences.write
```

**Full Recommended Scopes:**
```
contacts.read
companies.read
sequences.read
sequences.write
timeline.read
timeline.write
```

## Private App Creation Steps

1. Log in to HubSpot
2. Navigate to **Settings** → **Integrations** → **Private Apps**
3. Click **Create a private app**
4. Name the app: "Sales Intelligence System"
5. In the **Scopes** tab, select the scopes listed above
6. Save the app
7. Copy the **Access Token** (this will be stored in Secret Manager as `hubspot-api-key`)

## Security Notes

- The Private App access token should be stored in Google Secret Manager
- Never commit the access token to version control
- Rotate the token periodically (recommended: every 90 days)
- Use the token only from secure Cloud Functions with proper IAM permissions

## API Rate Limits

HubSpot API has rate limits:
- **Free/Starter**: 100 requests per 10 seconds
- **Professional**: 100 requests per 10 seconds
- **Enterprise**: 100 requests per 10 seconds

The sync functions implement retry logic with exponential backoff to handle rate limits gracefully.

