#!/bin/bash
# Quick Start Script - Run Sales Intelligence System Locally
# Bash script to set up and run the web application

echo "🚀 Starting Sales Intelligence System..."
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r web_app/requirements.txt
echo "✅ Dependencies installed"
echo ""

# Set environment variables
echo "Setting environment variables..."
export GCP_PROJECT_ID="maharani-sales-hub-11-2025"
export GCP_REGION="us-central1"
export BIGQUERY_DATASET="sales_intelligence"
echo "✅ Environment variables set"
echo ""

# Check Google Cloud authentication
echo "Checking Google Cloud authentication..."
if ! command -v gcloud &> /dev/null; then
    echo "⚠️  Google Cloud SDK not found"
    echo "   Install from: https://cloud.google.com/sdk/docs/install"
else
    echo "✅ Google Cloud SDK found"
    # Check if authenticated
    if ! gcloud auth list 2>&1 | grep -q "ACTIVE"; then
        echo "⚠️  Not authenticated. Run: gcloud auth application-default login"
    else
        echo "✅ Google Cloud authenticated"
    fi
fi
echo ""

# Change to web app directory
cd web_app

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Starting Sales Intelligence Web Application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The web app will open at: http://localhost:8501"
echo ""
echo "Login with any email (e.g., anand@maharaniweddings.com)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Streamlit
streamlit run app.py

