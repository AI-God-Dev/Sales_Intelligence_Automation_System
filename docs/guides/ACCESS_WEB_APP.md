# 🌐 Accessing the Sales Intelligence Web Application

## The Web App is Starting!

The Streamlit web application is launching in the background.

### Access the Application

**Open your web browser and navigate to:**
```
http://localhost:8501
```

### Login Information

**Use any email address to login:**
- `anand@maharaniweddings.com`
- Or any email you prefer (simple authentication for now)

### What You Can Test

Once logged in, you can access:

1. **📊 Dashboard**
   - View key metrics
   - See top priority accounts
   - Real-time data from BigQuery (if connected)

2. **🎯 Account Scoring**
   - View account scores and recommendations
   - See score distributions
   - Check budget likelihood charts

3. **💬 Natural Language Query**
   - Ask questions in plain English
   - Example: "Show me accounts with high engagement"
   - See generated SQL and results

4. **🔍 Semantic Search** ⭐ NEW
   - Search by intent using AI
   - Example: "budget discussions for 2026"
   - Find accounts, emails, or calls by meaning

5. **📧 Unmatched Emails**
   - View emails not in Salesforce
   - Create leads from unmatched emails

6. **🏢 Account Details**
   - Search for any account
   - View complete account information
   - See emails, calls, opportunities, and scores

7. **📬 Email Threads**
   - View email conversations
   - Generate AI-powered replies

### If the App Doesn't Open Automatically

1. **Check if it's running:**
   ```powershell
   netstat -ano | findstr "8501"
   ```

2. **Manual access:**
   - Open browser
   - Go to: http://localhost:8501

3. **Check for errors:**
   - Look at the terminal output
   - Check if port 8501 is available

### Troubleshooting

**Port already in use:**
```powershell
# Stop the current process and restart
streamlit run app.py --server.port 8502
```

**BigQuery connection errors:**
- The app will still run, but some features may show "BigQuery client not available"
- This is expected if GCP credentials aren't configured
- Cloud Functions will work if deployed

**Module import errors:**
```powershell
# Install missing dependencies
pip install -r web_app/requirements.txt
```

### Stop the Application

Press `Ctrl+C` in the terminal where Streamlit is running, or:
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process
```

---

**🎉 Enjoy exploring the Sales Intelligence System!**

