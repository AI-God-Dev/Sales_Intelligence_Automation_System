# Sales Intelligence Web Application

Streamlit-based web interface for the Sales Intelligence & Automation System.

## Features

- **Dashboard**: Overview of key metrics and top priority accounts
- **Account Scoring**: View AI-generated account scores and recommendations
- **Natural Language Query**: Ask questions about sales data in plain English
- **Unmatched Emails**: View and create leads from unmatched emails
- **Account Details**: Detailed view of account information, emails, calls, and opportunities
- **Email Threads**: View email threads and generate AI-powered replies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export GCP_PROJECT_ID=maharani-sales-hub-11-2025
export GCP_REGION=us-central1
```

3. Run the application:
```bash
streamlit run app.py
```

## Deployment to Cloud Run

1. Build and deploy:
```bash
gcloud run deploy sales-intelligence-web \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1
```

## Authentication

Currently uses simple email-based authentication. In production, integrate with Google OAuth for secure authentication.

## Configuration

Update `FUNCTIONS_BASE_URL` in `app.py` to point to your Cloud Functions deployment.

