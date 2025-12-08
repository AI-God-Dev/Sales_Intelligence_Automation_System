# Quick Start Script - Run Sales Intelligence System Locally
# PowerShell script to set up and run the web application

Write-Host "🚀 Starting Sales Intelligence System..." -ForegroundColor Green
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"
Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r web_app/requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
$env:GCP_REGION = "us-central1"
$env:BQ_DATASET_NAME = "sales_intelligence"
Write-Host "✅ Environment variables set" -ForegroundColor Green
Write-Host ""

# Check Google Cloud authentication
Write-Host "Checking Google Cloud authentication..." -ForegroundColor Yellow
$gcloudAuth = gcloud auth list 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Google Cloud SDK not found or not authenticated" -ForegroundColor Yellow
    Write-Host "   Run: gcloud auth application-default login" -ForegroundColor Yellow
} else {
    Write-Host "✅ Google Cloud authenticated" -ForegroundColor Green
}
Write-Host ""

# Change to web app directory
Set-Location web_app

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Starting Sales Intelligence Web Application..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "The web app will open at: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Login with any email (e.g., anand@maharaniweddings.com)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run Streamlit
streamlit run app.py

