# Web Application Guide - Sales Intelligence Automation System

## Overview

The Sales Intelligence Automation System includes a professional Streamlit-based web application that provides an intuitive interface for sales teams to interact with the unified data warehouse and AI-powered intelligence features.

## Table of Contents

1. [Application Architecture](#application-architecture)
2. [Features & Pages](#features--pages)
3. [Installation & Setup](#installation--setup)
4. [Running Locally](#running-locally)
5. [Deployment](#deployment)
6. [Configuration](#configuration)
7. [User Guide](#user-guide)
8. [Troubleshooting](#troubleshooting)

---

## Application Architecture

### Technology Stack

- **Framework**: Streamlit
- **Language**: Python 3.11
- **Backend**: Cloud Functions (Gen2) for AI operations
- **Data Source**: Google BigQuery
- **Authentication**: Google OAuth (optional, can be configured)
- **Hosting**: Google Cloud Run (recommended) or local development

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit Web Application                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Dashboard│  │  Search  │  │  Admin   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│              Google BigQuery Data Warehouse             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Accounts │  │  Emails  │  │  Calls   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│              Cloud Functions (AI Operations)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Scoring  │  │  Search  │  │  Replies │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Frontend (Streamlit)**: User interface and interaction layer
2. **BigQuery Client**: Direct queries to data warehouse
3. **Cloud Functions Integration**: Calls to AI-powered functions
4. **Authentication Layer**: Google OAuth integration (optional)

---

## Features & Pages

### 1. Account Priority Dashboard

**Purpose**: View and prioritize accounts based on AI-generated scores.

**Features**:
- Sortable table of all accounts with scores
- Priority score, budget likelihood, and engagement metrics
- Expandable rows showing detailed insights
- Search and filter capabilities
- Recommended actions per account
- Last interaction date tracking

**Usage**:
1. Navigate to "Account Priority Dashboard" from sidebar
2. View accounts sorted by priority score (highest first)
3. Click on any row to expand and see:
   - AI-generated reasoning
   - Key signals detected
   - Recommended actions
   - Recent activity summary

### 2. Semantic Search

**Purpose**: Find accounts and communications by natural language intent.

**Features**:
- Natural language query input
- Semantic search across emails and calls
- Results ranked by relevance
- Account context in results
- Snippet previews

**Usage**:
1. Navigate to "Semantic Search" from sidebar
2. Enter a query like:
   - "budget discussions"
   - "interested in pricing"
   - "technical questions"
   - "follow-up needed"
3. View results with:
   - Matching emails/calls
   - Associated accounts
   - Relevance scores
   - Snippet previews

**Example Queries**:
- "Show me accounts discussing budget"
- "Find conversations about pricing"
- "Accounts with technical questions"
- "Emails mentioning competitors"

### 3. Natural Language Queries

**Purpose**: Ask questions about your data in plain English.

**Features**:
- Convert natural language to SQL
- Safety validation (SELECT only)
- Result summarization
- Export capabilities

**Usage**:
1. Navigate to "Natural Language Query" from sidebar
2. Enter a question like:
   - "How many emails did we send last week?"
   - "What are the top 10 accounts by revenue?"
   - "Show me all unmatched emails"
3. Review the generated SQL (optional)
4. View results in table format
5. Export results if needed

**Safety Features**:
- Only SELECT queries allowed
- No DROP, DELETE, UPDATE, INSERT operations
- Input validation and sanitization
- Error handling for invalid queries

### 4. Unmatched Emails

**Purpose**: Manage emails that couldn't be automatically matched to Salesforce contacts.

**Features**:
- List of unmatched emails
- Email details (subject, body, sender, date)
- One-click lead creation in Salesforce
- Manual matching options

**Usage**:
1. Navigate to "Unmatched Emails" from sidebar
2. Review list of unmatched emails
3. For each email:
   - Review details
   - Click "Create Lead in Salesforce" to create a new lead
   - Or manually match to existing contact (if feature enabled)

### 5. Account Details

**Purpose**: View comprehensive details for a specific account.

**Features**:
- Account information
- Recent emails
- Call history
- Opportunities
- Activities timeline
- AI-generated insights

**Usage**:
1. Navigate to "Account Details" from sidebar
2. Select an account from dropdown
3. View:
   - Account summary
   - Recent communications
   - Open opportunities
   - Activity timeline
   - AI insights and recommendations

### 6. Email Threads

**Purpose**: View complete email threads for context.

**Features**:
- Thread view with all messages
- Chronological ordering
- Participant information
- Account context

**Usage**:
1. Navigate to "Email Threads" from sidebar
2. Select a thread ID or search by subject
3. View complete conversation history
4. See all participants and timestamps

### 7. Admin Panel

**Purpose**: Administrative functions and system management.

**Features**:
- Manual trigger for data syncs
- Trigger account scoring
- System health checks
- View ETL run status
- Configuration management

**Usage**:
1. Navigate to "Admin Panel" from sidebar
2. Use buttons to:
   - Trigger Gmail sync
   - Trigger Salesforce sync
   - Trigger Dialpad sync
   - Run account scoring
   - Check system health
3. View logs and status

---

## Installation & Setup

### Prerequisites

- Python 3.11 or higher
- Google Cloud SDK (`gcloud`) installed and configured
- Access to GCP project with BigQuery dataset
- Cloud Functions deployed (for AI features)

### Local Installation

1. **Navigate to web_app directory**:
   ```bash
   cd web_app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   # Windows PowerShell
   $env:GCP_PROJECT_ID = "your-project-id"
   $env:GCP_REGION = "us-central1"
   $env:DATASET_ID = "sales_intelligence"
   
   # Linux/Mac
   export GCP_PROJECT_ID="your-project-id"
   export GCP_REGION="us-central1"
   export DATASET_ID="sales_intelligence"
   ```

4. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth application-default login
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

6. **Access the application**:
   - Open browser to `http://localhost:8501`

### Docker Installation

1. **Build the Docker image**:
   ```bash
   cd web_app
   docker build -t sales-intelligence-webapp .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8501:8501 \
     -e GCP_PROJECT_ID="your-project-id" \
     -e GCP_REGION="us-central1" \
     -e DATASET_ID="sales_intelligence" \
     -v ~/.config/gcloud:/root/.config/gcloud:ro \
     sales-intelligence-webapp
   ```

---

## Running Locally

### Development Mode

For local development with MOCK_MODE:

```bash
# Set MOCK_MODE to use mock AI responses
export MOCK_MODE=1

# Run Streamlit
cd web_app
streamlit run app.py
```

**Note**: With `MOCK_MODE=1`, the web app will use mock responses for AI operations, allowing you to test the UI without API costs.

### Local Testing Checklist

- [ ] Application starts without errors
- [ ] Can connect to BigQuery
- [ ] Dashboard loads account data
- [ ] Semantic search works (with MOCK_MODE)
- [ ] Natural language queries work
- [ ] All pages are accessible
- [ ] Error handling works correctly

---

## Deployment

### Deploy to Cloud Run

1. **Build and push Docker image**:
   ```bash
   cd web_app
   gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/sales-intelligence-webapp
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy sales-intelligence-webapp \
     --image gcr.io/$GCP_PROJECT_ID/sales-intelligence-webapp \
     --platform managed \
     --region $GCP_REGION \
     --allow-unauthenticated \
     --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,DATASET_ID=sales_intelligence
   ```

3. **Get the URL**:
   ```bash
   gcloud run services describe sales-intelligence-webapp \
     --platform managed \
     --region $GCP_REGION \
     --format "value(status.url)"
   ```

### Environment Variables for Production

Set these in Cloud Run:

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: Your GCP region
- `DATASET_ID`: BigQuery dataset ID (default: `sales_intelligence`)
- `MOCK_MODE`: Set to `0` for production (use real AI)
- `LOCAL_MODE`: Set to `0` for production

### Authentication (Optional)

To enable Google OAuth:

1. **Create OAuth credentials** in GCP Console
2. **Update `app.py`** to include OAuth flow
3. **Set environment variables**:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

---

## Configuration

### Application Configuration

The web app uses the following configuration sources (in order of precedence):

1. **Environment Variables** (highest priority)
2. **Streamlit Config** (`web_app/.streamlit/config.toml`)
3. **Default Values** (hardcoded in `app.py`)

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | GCP project ID | Required |
| `GCP_REGION` | GCP region | `us-central1` |
| `DATASET_ID` | BigQuery dataset | `sales_intelligence` |
| `MOCK_MODE` | Use mock AI responses | `0` |
| `LOCAL_MODE` | Use local implementations | `0` |

### Streamlit Configuration

Edit `web_app/.streamlit/config.toml`:

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#2563eb"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f3f4f6"
textColor = "#000000"
```

---

## User Guide

### Getting Started

1. **Access the Application**:
   - Production: Navigate to your Cloud Run URL
   - Local: Open `http://localhost:8501`

2. **Navigate Pages**:
   - Use the sidebar to switch between pages
   - Each page has a specific purpose (see Features section)

3. **View Account Priorities**:
   - Start with "Account Priority Dashboard"
   - Accounts are sorted by priority score
   - Expand rows to see detailed insights

4. **Search for Information**:
   - Use "Semantic Search" for intent-based search
   - Use "Natural Language Query" for data questions

### Best Practices

1. **Account Prioritization**:
   - Review top 20 accounts daily
   - Focus on accounts with high priority scores
   - Take recommended actions promptly

2. **Semantic Search**:
   - Use specific, descriptive queries
   - Combine multiple keywords for better results
   - Review account context in results

3. **Unmatched Emails**:
   - Review weekly
   - Create leads for promising opportunities
   - Manually match when possible

4. **Natural Language Queries**:
   - Be specific in your questions
   - Review generated SQL before executing
   - Export results for further analysis

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Error**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
# Ensure you're in the web_app directory
cd web_app

# Install dependencies
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.11+
```

#### 2. BigQuery Connection Errors

**Error**: `403 Forbidden` or authentication errors

**Solution**:
```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Verify project is set
gcloud config get-value project

# Verify BigQuery API is enabled
gcloud services enable bigquery.googleapis.com
```

#### 3. Cloud Functions Not Responding

**Error**: `Function not found` or timeout errors

**Solution**:
- Verify Cloud Functions are deployed:
  ```bash
  gcloud functions list --gen2
  ```
- Check function URLs in `app.py` or environment variables
- Verify service account has proper permissions

#### 4. No Data Showing

**Error**: Empty tables or "No data available"

**Solution**:
- Verify data exists in BigQuery:
  ```bash
  bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`$GCP_PROJECT_ID.sales_intelligence.gmail_messages\`"
  ```
- Check ETL runs in `etl_runs` table
- Trigger manual sync from Admin Panel

#### 5. Semantic Search Not Working

**Error**: No results or errors

**Solution**:
- Verify embeddings are generated:
  ```bash
  bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`$GCP_PROJECT_ID.sales_intelligence.gmail_messages\` WHERE embedding IS NOT NULL"
  ```
- Trigger embeddings generation from Admin Panel
- Check MOCK_MODE is set correctly

### Performance Optimization

1. **Query Optimization**:
   - Use filters to limit data
   - Add date ranges for large datasets
   - Use pagination for large result sets

2. **Caching**:
   - Streamlit automatically caches function results
   - Use `@st.cache_data` for expensive queries
   - Clear cache if data is stale

3. **Resource Limits**:
   - Increase Cloud Run memory if needed
   - Use connection pooling for BigQuery
   - Limit concurrent requests

### Getting Help

1. **Check Logs**:
   - Local: View terminal output
   - Cloud Run: `gcloud run services logs read sales-intelligence-webapp`

2. **Review Documentation**:
   - `TROUBLESHOOTING.md` - Common issues
   - `SYSTEM_ARCHITECTURE.md` - System overview
   - `AI_SYSTEM_GUIDE.md` - AI features

3. **Contact Support**:
   - Review error messages carefully
   - Check Cloud Logging for detailed errors
   - Verify all prerequisites are met

---

## Advanced Features

### Custom Styling

The web app includes custom CSS in `app.py`. To modify:

1. Edit the `inject_custom_css()` function
2. Update CSS variables for colors
3. Modify component styles as needed

### Extending Functionality

To add new pages:

1. Create a new function in `app.py`:
   ```python
   def my_new_page():
       st.title("My New Page")
       # Your code here
   ```

2. Add to sidebar navigation:
   ```python
   if page == "My New Page":
       my_new_page()
   ```

### Integration with Cloud Functions

The web app calls Cloud Functions for AI operations. To add new functions:

1. Deploy the Cloud Function
2. Add function URL to `get_function_url()` in `app.py`
3. Create a UI component to call the function
4. Handle responses and errors

---

## Security Considerations

1. **Authentication**:
   - Enable Google OAuth for production
   - Restrict access to authorized users
   - Use IAM roles for fine-grained access

2. **Data Access**:
   - Service account should have minimal permissions
   - Use BigQuery row-level security if needed
   - Audit data access logs

3. **Input Validation**:
   - All user inputs are validated
   - SQL injection prevention in place
   - XSS protection enabled

4. **Secrets Management**:
   - Never commit secrets to code
   - Use Secret Manager for sensitive data
   - Rotate credentials regularly

---

## Maintenance

### Regular Tasks

1. **Monitor Performance**:
   - Check Cloud Run metrics
   - Review BigQuery query costs
   - Monitor error rates

2. **Update Dependencies**:
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

3. **Clear Cache**:
   - Streamlit cache clears on restart
   - Clear manually if needed: `Ctrl+C` and restart

4. **Review Logs**:
   - Check for errors weekly
   - Monitor user feedback
   - Address issues promptly

---

**Last Updated**: [Current Date]  
**Version**: 1.0.0  
**Status**: Production Ready
