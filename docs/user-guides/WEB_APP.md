# Web Application Guide

User guide for the Sales Intelligence web application.

## Overview

The Sales Intelligence web application provides an intuitive interface for sales teams to access AI-powered insights, search communications, and manage accounts.

## Accessing the Application

### Cloud Deployment
Navigate to: `https://sales-intelligence-web-XXXXX.run.app`

### Local Development
```bash
cd web_app
pip install -r requirements.txt
streamlit run app.py
# Open http://localhost:8501
```

## Login

1. Enter your email address in the sidebar
2. Click **Login**
3. You'll see "Logged in as: your-email@example.com"

---

## Features

### Dashboard

**Purpose**: Overview of sales metrics and top priority accounts.

**Features**:
- Total accounts count
- High priority accounts
- Unmatched emails count
- Open opportunities
- Top 20 priority accounts table

**Actions**:
- Click **Refresh Account Scores** to regenerate AI scores
- Use **Test Mode** checkbox to limit to 10 accounts for testing

---

### Account Scoring

**Purpose**: View AI-generated account priority scores.

**Metrics**:
- **Priority Score** (0-100): Overall account priority
- **Budget Likelihood** (0-100): Likelihood of budget availability
- **Engagement Score** (0-100): Recent engagement level

**Features**:
- Priority score distribution chart
- Budget likelihood chart
- Sortable account table with scores
- AI-generated reasoning and recommendations

**Actions**:
- Click **🔄 Refresh Account Scores** to regenerate scores
- Scores are automatically generated daily at 7 AM

---

### Natural Language Query

**Purpose**: Ask questions about your data in plain English.

**How to Use**:
1. Enter a question in the text area
2. Click **Execute Query**
3. View the generated SQL and results

**Example Queries**:
- "Show me accounts with high engagement in the last week"
- "Which accounts are discussing budget for 2026?"
- "Find contacts who haven't been called in 30 days"
- "What are the top 10 accounts by revenue?"

**Features**:
- Automatic SQL generation
- Safety validation (SELECT queries only)
- Results in table format
- AI-generated summary

---

### Semantic Search

**Purpose**: Find communications by intent, not just keywords.

**How to Use**:
1. Enter a search query (e.g., "budget discussions")
2. Select search type: accounts, emails, or calls
3. Adjust results limit and similarity threshold
4. Click **Search**

**Example Searches**:
- "budget discussions for 2026"
- "renewal concerns"
- "pricing negotiations"
- "technical questions"

**Parameters**:
- **Results Limit**: Maximum results to return
- **Days Back**: How far back to search
- **Minimum Similarity**: Threshold for relevance (0.7 recommended)

---

### Unmatched Emails

**Purpose**: Manage emails from contacts not in Salesforce.

**How to Use**:
1. Click **Load Unmatched Emails**
2. Review the list of emails
3. Select emails to create leads from
4. Click **Create Leads from Selected**

**Features**:
- Email preview (sender, subject, body snippet)
- Bulk lead creation
- Automatic Salesforce lead creation

---

### Account Details

**Purpose**: View complete information for a specific account.

**How to Use**:
1. Enter an Account ID or name in the search box
2. Browse the tabs for different views

**Tabs**:
- **Overview**: Account info and latest score
- **Emails**: Recent emails for this account
- **Calls**: Recent call logs
- **Opportunities**: Open and closed opportunities
- **Scores**: Historical account scores

---

### Email Threads

**Purpose**: View email conversations and generate AI replies.

**How to Use**:
1. Enter a Thread ID or email address
2. View the complete thread
3. Select a message to reply to
4. Click **Generate Reply** for AI-assisted response

**Features**:
- Full thread view with all messages
- Chronological ordering
- AI-generated reply suggestions

---

## Tips for Best Results

### Natural Language Queries
- Be specific in your questions
- Include time frames when relevant
- Start with simple queries

### Semantic Search
- Use descriptive phrases, not single words
- Adjust similarity threshold if no results
- Try different search types

### Account Scoring
- Run scoring after data syncs complete
- Use test mode for quick validation
- Review reasoning for insights

---

## Troubleshooting

### "BigQuery Client Not Available"
1. Run: `gcloud auth application-default login`
2. Click **🔄 Retry BigQuery Connection**

### "Function Not Deployed"
Contact administrator to deploy Cloud Functions.

### No Results Found
- Check that data has been synced
- Adjust search parameters
- Verify filters aren't too restrictive

### Slow Performance
- Reduce results limit
- Use more specific queries
- Wait for cold-start if first request

---

## Best Practices

1. **Daily Workflow**
   - Check Dashboard for top priority accounts
   - Review any unmatched emails
   - Use semantic search for specific needs

2. **Account Research**
   - Use Account Details for complete view
   - Check email history for context
   - Review AI recommendations

3. **Data Quality**
   - Report unmatched emails that should match
   - Verify account scores seem reasonable
   - Note any data issues

---

## Support

For technical issues, see:
- [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)
- [Operations Runbook](../operations/RUNBOOK.md)

