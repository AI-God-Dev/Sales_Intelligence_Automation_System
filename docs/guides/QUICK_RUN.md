# ⚡ Quick Run Guide

## Simplest Way to Run the Project

### Step 1: Install Dependencies

```powershell
# Activate virtual environment (if exists) or create new one
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install streamlit pandas requests google-cloud-bigquery google-auth
```

### Step 2: Set Environment Variables

```powershell
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
$env:GCP_REGION = "us-central1"
```

### Step 3: Run Web Application

```powershell
cd web_app
streamlit run app.py
```

**That's it!** The web app will open at `http://localhost:8501`

---

## Alternative: Run with Script

Just run:
```powershell
.\run_local.ps1
```

This script will:
1. ✅ Check Python installation
2. ✅ Create/activate virtual environment
3. ✅ Install all dependencies
4. ✅ Set environment variables
5. ✅ Start the web application

---

## Login

Use any email address to login:
- `anand@maharaniweddings.com`
- Any email works (simple auth for now)

---

## Troubleshooting

**If dependencies missing:**
```powershell
pip install -r requirements.txt
```

**If BigQuery errors:**
```powershell
gcloud auth application-default login
```

**If port 8501 already in use:**
```powershell
streamlit run app.py --server.port 8502
```

---

**Ready to go!** 🚀

