# Sales Intelligence Web Application

Streamlit-based dashboard for the Sales Intelligence Automation System.

## Features

- **Dashboard** - Overview with metrics and priority accounts
- **Account Scoring** - AI-generated priority scores
- **Natural Language Query** - Ask questions in plain English
- **Semantic Search** - Find communications by intent
- **Account Details** - Complete account information
- **Email Threads** - View and reply to conversations

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID="your-project-id"

# Run application
streamlit run app.py
```

Access at: http://localhost:8501

### Cloud Run Deployment

```bash
gcloud run deploy sales-intelligence-web \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GCP_PROJECT_ID` | GCP project ID | Yes |
| `GCP_REGION` | GCP region | No |
| `DATASET_ID` | BigQuery dataset | No |

### Required Permissions

The application needs access to:
- BigQuery (read/query)
- Cloud Functions (invoke)

## Project Structure

```
web_app/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── Dockerfile          # Container build
└── styles.css          # Custom styling
```

## Usage Guide

See [docs/user-guides/WEB_APP.md](../docs/user-guides/WEB_APP.md) for detailed usage instructions.

## Troubleshooting

### BigQuery Connection Failed

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GCP_PROJECT_ID
```

### Permission Denied

Ensure your user has:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`

## Development

```bash
# Install dev dependencies
pip install -r ../requirements-dev.txt

# Run with auto-reload
streamlit run app.py --server.runOnSave true
```
