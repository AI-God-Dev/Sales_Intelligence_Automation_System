# 🚀 Running the Project - Step by Step

## ✅ Step 1: Prerequisites Check

**Completed:**
- ✅ Python installed
- ✅ Virtual environment exists
- ✅ Required packages installed:
  - streamlit (1.51.0)
  - pandas (2.3.3)
  - requests (2.32.5)
  - google-cloud-bigquery (3.38.0)

## ✅ Step 2: Environment Setup

**Environment Variables Set:**
- ✅ `GCP_PROJECT_ID` = `maharani-sales-hub-11-2025`
- ✅ `GCP_REGION` = `us-central1`
- ✅ `BIGQUERY_DATASET` = `sales_intelligence`

## ✅ Step 3: Start Web Application

**Status:** Starting Streamlit web application...

**Access Information:**
- 🌐 **URL**: http://localhost:8501
- 🔐 **Login**: Any email (e.g., `anand@maharaniweddings.com`)

## 📋 Available Features

Once logged in, you can access:

1. **📊 Dashboard**
   - Real-time metrics
   - Top priority accounts
   - Account score refresh

2. **🎯 Account Scoring**
   - AI-powered account scores
   - Distribution charts
   - Detailed score breakdowns

3. **💬 Natural Language Query**
   - Ask questions in plain English
   - See generated SQL
   - View results

4. **🔍 Semantic Search**
   - AI-powered intent-based search
   - Search emails, calls, or accounts
   - Adjustable similarity thresholds

5. **📧 Unmatched Emails**
   - View emails from unknown contacts
   - Create leads from selected emails

6. **🏢 Account Details**
   - Search accounts
   - View complete account information
   - Tabs for emails, calls, opportunities

7. **📬 Email Threads**
   - View email conversations
   - Generate AI-powered replies

## 🔧 Troubleshooting

### If the app doesn't open automatically:
1. **Manually open browser** → http://localhost:8501
2. **Check if port 8501 is available**
3. **Check terminal output** for errors

### If you see BigQuery errors:
- This is normal if GCP credentials aren't configured locally
- The app will still work, but some features may show "BigQuery client not available"
- Cloud Functions features work when deployed to GCP

### To stop the application:
- Press `Ctrl+C` in the terminal where Streamlit is running

## 📝 Next Steps

1. **Open the browser** → http://localhost:8501
2. **Login** with any email address
3. **Explore** the dashboard and all features
4. **Test** different pages and functionality

---

**🎉 The Sales Intelligence System is now running!**

