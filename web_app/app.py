"""
Sales Intelligence & Automation System - Professional Web Application
Streamlit-based web interface with Google OAuth and full BigQuery integration
Refined UI with professional styling and enhanced user experience
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path
# Use resolve() to get absolute path, then go up two levels (web_app -> project root)
project_root = Path(__file__).resolve().parent.parent
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

# Inject custom CSS for professional styling
def inject_custom_css():
    """Inject simple, clean, professional custom CSS styling."""
    css = """
    <style>
    /* ===== SIMPLE DESIGN SYSTEM ===== */
    :root {
        --primary: #2563eb;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        
        --bg-primary: #ffffff;
        --bg-secondary: #f3f4f6;
        
        --text-primary: #000000;
        --text-secondary: #374151;
        
        --border: #d1d5db;
    }
    
    /* ===== BASE STYLES ===== */
    .main {
        padding: 2rem;
        background: #ffffff;
    }
    
    .block-container {
        max-width: 1200px;
        background: #ffffff;
    }
    
    /* Main content text - high contrast */
    .main h1 {
        color: #000000 !important;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .main h2 {
        color: #111827 !important;
        font-weight: 600;
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .main h3 {
        color: #111827 !important;
        font-weight: 600;
        font-size: 1.25rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    .main p {
        color: #1f2937 !important;
        line-height: 1.6;
    }
    
    /* Ensure text is readable in main content */
    .main .stMarkdown {
        color: #1f2937 !important;
    }
    
    .main .stMarkdown strong {
        color: #000000 !important;
    }
    
    .main .stMarkdown code {
        background: #f3f4f6 !important;
        color: #111827 !important;
        padding: 0.125rem 0.375rem;
        border-radius: 0.25rem;
    }
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: #111827 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label {
        color: #f3f4f6 !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div > select {
        color: #ffffff !important;
        background: #1f2937 !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        border-color: #60a5fa !important;
        background: #1f2937 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1d4ed8 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stSuccess {
        background: #065f46 !important;
        color: #d1fae5 !important;
        border: 1px solid #10b981 !important;
    }
    
    [data-testid="stSidebar"] .stError {
        background: #991b1b !important;
        color: #fee2e2 !important;
        border: 1px solid #ef4444 !important;
    }
    
    [data-testid="stSidebar"] .stInfo {
        background: #1e3a8a !important;
        color: #dbeafe !important;
        border: 1px solid #3b82f6 !important;
    }
    
    [data-testid="stSidebar"] .stWarning {
        background: #92400e !important;
        color: #fef3c7 !important;
        border: 1px solid #f59e0b !important;
    }
    
    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: var(--bg-primary);
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid var(--border);
        height: 100%;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #000000;
        line-height: 1;
    }
    
    .metric-card.success .metric-value {
        color: #059669;
    }
    
    .metric-card.warning .metric-value {
        color: #d97706;
    }
    
    .metric-card.info .metric-value {
        color: #1d4ed8;
    }
    
    .metric-icon {
        font-size: 1rem;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: var(--primary);
        color: white;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
    }
    
    .stButton > button:hover {
        background: #1d4ed8;
    }
    
    /* ===== ALERT BOXES (Main Content) ===== */
    .main .stInfo {
        background: #dbeafe !important;
        border-left: 4px solid #2563eb !important;
        border-radius: 0.375rem;
        padding: 1rem;
        color: #1e3a8a !important;
    }
    
    .main .stInfo [data-testid="stMarkdownContainer"] {
        color: #1e3a8a !important;
    }
    
    .main .stSuccess {
        background: #d1fae5 !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 0.375rem;
        padding: 1rem;
        color: #065f46 !important;
    }
    
    .main .stSuccess [data-testid="stMarkdownContainer"] {
        color: #065f46 !important;
    }
    
    .main .stWarning {
        background: #fef3c7 !important;
        border-left: 4px solid #f59e0b !important;
        border-radius: 0.375rem;
        padding: 1rem;
        color: #92400e !important;
    }
    
    .main .stWarning [data-testid="stMarkdownContainer"] {
        color: #92400e !important;
    }
    
    .main .stError {
        background: #fee2e2 !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 0.375rem;
        padding: 1rem;
        color: #991b1b !important;
    }
    
    .main .stError [data-testid="stMarkdownContainer"] {
        color: #991b1b !important;
    }
    
    /* ===== DATA TABLES ===== */
    .dataframe {
        border-radius: 0.5rem;
        border: 1px solid #d1d5db;
    }
    
    .dataframe thead {
        background: #f3f4f6 !important;
    }
    
    .dataframe thead th {
        padding: 0.75rem 1rem;
        font-weight: 600;
        font-size: 0.75rem;
        color: #000000 !important;
        background: #f3f4f6 !important;
    }
    
    .dataframe tbody tr:hover {
        background: #f9fafb !important;
    }
    
    .dataframe tbody td {
        padding: 0.75rem 1rem;
        color: #1f2937 !important;
        background: #ffffff !important;
    }
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary);
        outline: none;
    }
    
    /* ===== CARDS ===== */
    .content-card {
        background: var(--bg-primary);
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #d1d5db;
        margin-bottom: 1.5rem;
    }
    
    /* ===== INPUT FIELDS (Main Content) ===== */
    .main .stTextInput > div > div > input,
    .main .stTextArea > div > div > textarea,
    .main .stSelectbox > div > div > select {
        color: #000000 !important;
        background: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    .main .stTextInput > div > div > input:focus,
    .main .stTextArea > div > div > textarea:focus,
    .main .stSelectbox > div > div > select:focus {
        border-color: #2563eb !important;
        outline: none;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    
    .main .stTextInput label,
    .main .stTextArea label,
    .main .stSelectbox label {
        color: #111827 !important;
        font-weight: 600 !important;
    }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Inject CSS on page load
inject_custom_css()

# Try to import Google OAuth
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

# Try to import BigQuery client
try:
    # Ensure path is set before importing (use absolute path)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    from utils.bigquery_client import BigQueryClient
    BQ_AVAILABLE = True
except ImportError as e:
    BQ_AVAILABLE = False
    import logging
    logging.warning(f"BigQueryClient import failed: {e}. Project root: {project_root_str}, sys.path: {sys.path[:3]}")

# Page configuration
st.set_page_config(
    page_title="Sales Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "maharani-sales-hub-11-2025")
REGION = os.getenv("GCP_REGION", "us-central1")
# Note: For local dev, use your Google account (gcloud auth login) - you have run.invoker permission
# For production, web-app-runtime-sa automatically has run.invoker permission
# No service account impersonation needed - use Application Default Credentials directly
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'bq_client' not in st.session_state:
    st.session_state.bq_client = None
if 'function_urls' not in st.session_state:
    st.session_state.function_urls = {}

# Function to initialize BigQuery client (can be called manually)
def init_bigquery_client():
    """Initialize BigQuery client and return success status."""
    if not BQ_AVAILABLE:
        return False, "BigQueryClient import not available"
    
    try:
        import logging
        import os
        import sys
        from pathlib import Path
        
        # Ensure project root is in path (in case it's not)
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Ensure project ID is set in environment
        os.environ["GCP_PROJECT_ID"] = PROJECT_ID
        
        logger.info(f"Initializing BigQuery client for project: {PROJECT_ID}...")
        logger.info(f"GCP_PROJECT_ID env var: {os.getenv('GCP_PROJECT_ID')}")
        logger.info(f"Project root in path: {str(project_root) in sys.path}")
        
        # Verify ADC is available
        try:
            from google.auth import default
            credentials, project = default()
            logger.info(f"Application Default Credentials found. Project: {project}")
        except Exception as auth_error:
            logger.warning(f"Could not verify ADC: {auth_error}")
            return False, f"Application Default Credentials not found. Please run: gcloud auth application-default login. Error: {auth_error}"
        
        # Try to initialize with explicit project ID
        st.session_state.bq_client = BigQueryClient(project_id=PROJECT_ID)
        
        # Test the connection with a simple query (just SELECT 1, no table needed)
        test_query = "SELECT 1 as test"
        try:
            result = st.session_state.bq_client.query(test_query, max_results=1)
            logger.info(f"BigQuery connection test successful: {result}")
        except Exception as test_error:
            # If even basic query fails, there's a connectivity issue
            logger.warning(f"BigQuery connection test failed: {test_error}")
            return False, f"BigQuery connection test failed: {test_error}"
        
        logger.info("BigQuery client initialized successfully")
        # Clear any previous errors on success
        if 'bq_error' in st.session_state:
            del st.session_state.bq_error
        return True, "BigQuery client initialized successfully"
    except Exception as e:
        import traceback
        error_details = f"Error: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
        st.session_state.bq_client = None
        # Store error message for display
        st.session_state.bq_error = error_details
        import logging
        logging.error(f"BigQuery client initialization failed: {error_details}")
        # Also print to console for debugging
        print(f"BIGQUERY INIT ERROR: {error_details}")
        import sys
        sys.stderr.write(f"BIGQUERY INIT ERROR: {error_details}\n")
        return False, error_details

# Initialize BigQuery client if available
if BQ_AVAILABLE and st.session_state.bq_client is None:
    success, message = init_bigquery_client()
    if not success:
        # Error already stored in st.session_state.bq_error by init_bigquery_client
        pass

# Helper functions
def get_function_url(function_name: str) -> str:
    """Get Cloud Function URL for Gen2 functions (Cloud Run)."""
    # Check cache first
    if function_name in st.session_state.function_urls:
        cached_url = st.session_state.function_urls[function_name]
        if cached_url:  # Only return if not None
            return cached_url
    
    # Try using Google Cloud Functions client library first (most reliable)
    try:
        from google.cloud import functions_v2
        client = functions_v2.FunctionServiceClient()
        parent = f"projects/{PROJECT_ID}/locations/{REGION}"
        function_path = f"{parent}/functions/{function_name}"
        
        function_obj = client.get_function(name=function_path)
        if function_obj.service_config:
            # Get the Cloud Run service URL
            url = function_obj.service_config.uri
            if url:
                st.session_state.function_urls[function_name] = url
                return url
        # Fallback to the top-level URL
        if hasattr(function_obj, 'url') and function_obj.url:
            st.session_state.function_urls[function_name] = function_obj.url
            return function_obj.url
    except Exception as e:
        # Client library not available or failed, try subprocess
        pass
    
    # Fallback: Try subprocess with gcloud
    import subprocess
    import shutil
    
    # Check if gcloud is available
    gcloud_path = shutil.which("gcloud")
    if not gcloud_path:
        # gcloud not in PATH, use constructed URL
        url = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/{function_name}"
        st.session_state.function_urls[function_name] = url
        return url
    
    # Method 1: Try top-level url field (Cloud Functions URL) - More stable than direct Cloud Run URL
    try:
        result = subprocess.run(
            [gcloud_path, "functions", "describe", function_name, 
             "--gen2", "--region", REGION, "--project", PROJECT_ID,
             "--format", "value(url)"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            st.session_state.function_urls[function_name] = url
            return url
    except Exception as e:
        pass
    
    # Method 2: Try serviceConfig.uri (Cloud Run direct URL) - Fallback if Cloud Functions URL not available
    try:
        result = subprocess.run(
            [gcloud_path, "functions", "describe", function_name, 
             "--gen2", "--region", REGION, "--project", PROJECT_ID,
             "--format", "value(serviceConfig.uri)"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            st.session_state.function_urls[function_name] = url
            return url
    except Exception as e:
        pass
    
    # Method 3: Construct URL from known pattern (final fallback)
    # Gen2 functions have a predictable URL pattern
    url = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/{function_name}"
    st.session_state.function_urls[function_name] = url
    return url

def call_function(function_name: str, data: Dict = None, method: str = "POST") -> Dict:
    """Call a Cloud Function with improved error handling."""
    url = get_function_url(function_name)
    
    # If URL is None, try to get it from gcloud or return error
    if url is None:
        try:
            import subprocess
            result = subprocess.run(
                ["gcloud", "functions", "describe", function_name, 
                 "--gen2", "--region", REGION, "--project", PROJECT_ID,
                 "--format", "value(serviceConfig.uri)"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                url = result.stdout.strip()
                st.session_state.function_urls[function_name] = url
            else:
                return {
                    "error": f"Cloud Function '{function_name}' is not deployed yet. Please deploy it using the deployment scripts.",
                    "error_type": "not_deployed",
                    "suggestion": f"Deploy using: ./scripts/deploy_phase2_functions.ps1"
                }
        except Exception:
            return {
                "error": f"Cloud Function '{function_name}' URL could not be determined. The function may not be deployed.",
                "error_type": "not_deployed",
                "suggestion": f"Deploy using: ./scripts/deploy_phase2_functions.ps1"
            }
    
    try:
        # For Gen2 functions (Cloud Run), we need an identity token with the service URL as audience
        # Following Anand's approach:
        # - Local dev: Use your Google account (via gcloud auth login) - you have run.invoker permission
        # - Production: web-app-runtime-sa automatically has run.invoker permission
        # - Get ID token directly using Application Default Credentials (no impersonation needed)
        token = None
        headers = {}
        auth_lib_error = None
        
        # Method 1: Use Google Auth library to get ID token directly (Anand's recommended approach)
        try:
            from google.auth import default
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token
            
            # Explicitly get Application Default Credentials
            credentials, project = default()
            
            # Refresh credentials if needed
            request = google_requests.Request()
            if not credentials.valid:
                credentials.refresh(request)
            
            # Get identity token for the Cloud Run service URL (audience)
            # Uses Application Default Credentials (your user account in local dev, service account in production)
            token = id_token.fetch_id_token(request, url)
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                import logging
                logging.info("Successfully obtained ID token using Google Auth library")
        except Exception as auth_error:
            auth_lib_error = auth_error
            import logging
            logging.warning(f"ID token fetch failed: {str(auth_error)}")
            # Will try gcloud command fallback
            pass
        
        # If we got a token from Method 1, use it
        if token and headers:
            # Retry logic for 503 errors (cold start)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if method == "GET":
                        response = requests.get(url, headers=headers, timeout=60)
                    else:
                        response = requests.post(url, json=data or {}, headers=headers, timeout=60)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 503 and attempt < max_retries - 1:
                        # Service is starting up, wait and retry
                        import time
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                        import logging
                        logging.info(f"Service unavailable (503), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    raise
        
        # Fallback 1: Use gcloud functions call command (handles authentication automatically)
        # This is the most reliable method for local development
        try:
            import subprocess
            import shutil
            import json
            gcloud_path = shutil.which("gcloud")
            if gcloud_path:
                # Use gcloud functions call which handles authentication automatically
                cmd = [
                    gcloud_path, "functions", "call", function_name,
                    "--gen2",
                    "--region", REGION,
                    "--project", PROJECT_ID
                ]
                if method == "POST" and data:
                    cmd.extend(["--data", json.dumps(data)])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # Functions can take time
                )
                
                if result.returncode == 0:
                    # Try to parse JSON response
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError:
                        # If not JSON, return the raw output
                        return {"result": result.stdout, "message": "Function executed successfully"}
                else:
                    # Log the error but continue to next fallback
                    import logging
                    logging.warning(f"gcloud functions call failed: {result.stderr}")
                    # Check if it's a 503 error (service unavailable) - return immediately
                    if "503" in result.stderr or "Service Unavailable" in result.stderr:
                        return {
                            "error": "Cloud Run service is temporarily unavailable (503 error).",
                            "error_type": "service_unavailable",
                            "suggestion": "The Cloud Run service may be starting up, experiencing issues, or needs to be restarted. Please:\n1. Wait 1-2 minutes and try again (cold start)\n2. Contact Anand with this error message\n3. The service may need to be checked/restarted in GCP Console"
                        }
        except Exception as gcloud_error:
            import logging
            error_str = str(gcloud_error)
            logging.warning(f"gcloud functions call exception: {gcloud_error}")
            # Check if it's a 503 error in the exception message
            if "503" in error_str or "Service Unavailable" in error_str:
                return {
                    "error": "Cloud Run service is temporarily unavailable (503 error).",
                    "error_type": "service_unavailable",
                    "suggestion": "The Cloud Run service may be starting up, experiencing issues, or needs to be restarted. Please:\n1. Wait 1-2 minutes and try again (cold start)\n2. Contact Anand with this error message\n3. The service may need to be checked/restarted in GCP Console"
                }
            pass
        
        # Fallback 2: Try gcloud auth print-identity-token (without --audiences for user accounts)
        # Note: This may not work for user accounts, but we try it as a last resort
        try:
            import subprocess
            import shutil
            gcloud_path = shutil.which("gcloud")
            if gcloud_path:
                # Try without --audiences first (works for some account types)
                token_result = subprocess.run(
                    [gcloud_path, "auth", "print-identity-token"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if token_result.returncode == 0 and token_result.stdout.strip():
                    token = token_result.stdout.strip()
                    headers = {"Authorization": f"Bearer {token}"}
                    if method == "GET":
                        response = requests.get(url, headers=headers, timeout=60)
                    else:
                        response = requests.post(url, json=data or {}, headers=headers, timeout=60)
                    response.raise_for_status()
                    return response.json()
                else:
                    # Log the error for debugging
                    import logging
                    logging.warning(f"gcloud identity token failed: {token_result.stderr}")
        except Exception as gcloud_error:
            import logging
            logging.warning(f"gcloud identity token exception: {gcloud_error}")
            pass
        
        # If all methods fail, return error with helpful message
        error_msg = f"Could not authenticate with Cloud Run service."
        if auth_lib_error:
            error_msg += f" Primary method failed: {str(auth_lib_error)}"
        
        # Check if it's a 503 error (service unavailable)
        error_str = str(auth_lib_error) if auth_lib_error else ""
        if "503" in error_str or "Service Unavailable" in error_str:
            return {
                "error": "Cloud Run service is temporarily unavailable (503 error).",
                "error_type": "service_unavailable",
                "suggestion": "The Cloud Run service may be starting up or experiencing issues. Please wait a few moments and try again. If the problem persists, check the Cloud Run service status in GCP Console or ask Anand to verify the service is running."
            }
        
        return {
            "error": error_msg,
            "error_type": "auth_error",
            "suggestion": f"All authentication methods failed. Please ensure:\n1. You're logged in with: gcloud auth login\n2. Project is set: gcloud config set project maharani-sales-hub-11-2025\n3. Application Default Credentials are set: gcloud auth application-default login\n4. You have run.invoker permission on the Cloud Run service (ask Anand if needed).\n\nIf you see a 503 error, the service may be starting up - wait a moment and try again."
        }
    except HTTPError as e:
        if e.response.status_code == 404:
            return {
                "error": f"Cloud Function '{function_name}' is not deployed yet. Please deploy it using the deployment scripts.",
                "error_type": "not_deployed",
                "suggestion": f"Deploy using: ./scripts/deploy_phase2_functions.ps1"
            }
        elif e.response.status_code == 401:
            return {
                "error": f"HTTP 401: Unauthorized. The authentication token is invalid or expired. This usually means the identity token doesn't have the correct audience for the Cloud Run service.",
                "error_type": "auth_error",
                "suggestion": "Try refreshing the page or re-authenticating. If the issue persists, we may need to use service account impersonation for Cloud Run authentication."
            }
        elif e.response.status_code == 403:
            return {
                "error": f"HTTP 403: Permission denied. You don't have permission to invoke '{function_name}'. Please ask Anand to grant you the 'run.invoker' role on the Cloud Run service.",
                "error_type": "permission_denied",
                "suggestion": f"Ask Anand to run: gcloud run services add-iam-policy-binding {function_name} --region={REGION} --member='user:atajanbaratov360@gmail.com' --role='roles/run.invoker' --project={PROJECT_ID}"
            }
        else:
            error_text = str(e)
            try:
                error_text = e.response.text[:500] if e.response.text else str(e)
            except:
                pass
            return {
                "error": f"HTTP {e.response.status_code}: {error_text}",
                "error_type": "http_error"
            }
    except ConnectionError as e:
        return {
            "error": f"Cannot connect to Cloud Function '{function_name}'. It may not be deployed or the URL is incorrect.",
            "error_type": "connection_error",
            "suggestion": "Check if the function is deployed and the URL is correct."
        }
    except Timeout as e:
        return {
            "error": f"Request to '{function_name}' timed out. The function may be cold-starting or overloaded.",
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "error": f"Error calling {function_name}: {str(e)}",
            "error_type": "unknown"
        }

def query_bigquery(query: str, max_results: int = 100) -> List[Dict]:
    """Query BigQuery directly with improved error handling."""
    if not st.session_state.bq_client:
        return []
    try:
        return st.session_state.bq_client.query(query, max_results=max_results)
    except Exception as e:
        # Handle table not found errors gracefully
        error_str = str(e).lower()
        if "not found" in error_str or "does not exist" in error_str or "table" in error_str:
            # Table doesn't exist yet - return empty result
            return []
        # For other errors, log but don't crash
        import logging
        logging.getLogger(__name__).warning(f"BigQuery query error: {e}")
        return []

# Google OAuth authentication
def verify_google_token(token: str) -> Optional[str]:
    """Verify Google OAuth token and return email."""
    if not GOOGLE_AUTH_AVAILABLE or not GOOGLE_CLIENT_ID:
        return None
    try:
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return idinfo.get('email')
    except ValueError:
        return None

# Sidebar navigation
st.sidebar.markdown("""
<div style='text-align: center; padding: 2rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem;'>
    <h1 style='color: white; font-size: 1.25rem; font-weight: 600; margin: 0;'>
        Sales Intelligence
    </h1>
    <p style='color: #9ca3af; font-size: 0.875rem; margin: 0.5rem 0 0 0;'>
        AI-Powered Sales Automation
    </p>
</div>
""", unsafe_allow_html=True)

# Authentication
if not st.session_state.authenticated:
    st.sidebar.subheader("Login")
    
    # Google OAuth (if configured)
    if GOOGLE_AUTH_AVAILABLE and GOOGLE_CLIENT_ID:
        st.sidebar.info("Google OAuth authentication available")
    
    # Simple email authentication
    user_email = st.sidebar.text_input("Email", value="")
    if st.sidebar.button("Login", use_container_width=True):
        if user_email and "@" in user_email:
            st.session_state.authenticated = True
            st.session_state.user_email = user_email
            st.rerun()
        else:
            st.sidebar.error("Please enter a valid email address")
else:
    st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()

if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h1>Sales Intelligence</h1>
        <p style='color: var(--text-secondary); margin-bottom: 2rem;'>
            AI-Powered Sales Intelligence & Automation Platform
        </p>
        <p>Please log in using the sidebar to access the dashboard.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Navigation
page = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Account Scoring",
        "Natural Language Query",
        "Semantic Search",
        "Unmatched Emails",
        "Account Details",
        "Email Threads"
    ]
)

# Dashboard Page
if page == "Dashboard":
    st.title("Sales Intelligence Dashboard")
    st.markdown("Real-time insights and metrics for your sales pipeline")
    
    # Get metrics from BigQuery
    if st.session_state.bq_client:
        try:
            total_accounts_query = f"""
            SELECT COUNT(DISTINCT account_id) as count
            FROM `{PROJECT_ID}.sales_intelligence.sf_accounts`
            """
            total_accounts = query_bigquery(total_accounts_query)
            total_accounts_count = total_accounts[0]['count'] if total_accounts else 0
            
            # Check if account_recommendations table exists first
            try:
                high_priority_query = f"""
                SELECT COUNT(DISTINCT account_id) as count
                FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                WHERE score_date = CURRENT_DATE()
                AND priority_score >= 70
                """
                high_priority = query_bigquery(high_priority_query)
                high_priority_count = high_priority[0]['count'] if high_priority else 0
            except Exception:
                high_priority_count = 0
            
            unmatched_query = f"""
            SELECT COUNT(DISTINCT p.participant_id) as count
            FROM `{PROJECT_ID}.sales_intelligence.gmail_participants` p
            WHERE p.sf_contact_id IS NULL
            AND p.role = 'from'
            AND EXISTS (
                SELECT 1 FROM `{PROJECT_ID}.sales_intelligence.gmail_messages` m
                WHERE m.message_id = p.message_id
                AND m.sent_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
            )
            """
            unmatched = query_bigquery(unmatched_query)
            unmatched_count = unmatched[0]['count'] if unmatched else 0
            
            opportunities_query = f"""
            SELECT COUNT(DISTINCT opportunity_id) as count
            FROM `{PROJECT_ID}.sales_intelligence.sf_opportunities`
            WHERE is_closed = FALSE
            """
            opportunities = query_bigquery(opportunities_query)
            opportunities_count = opportunities[0]['count'] if opportunities else 0
        except Exception as e:
            st.warning(f"Could not load metrics: {str(e)}")
            total_accounts_count = high_priority_count = unmatched_count = opportunities_count = 0
    else:
        # Show helpful message when BigQuery is not available
        error_msg = ""
        if 'bq_error' in st.session_state and st.session_state.bq_error:
            error_msg = st.session_state.bq_error
        
        st.error("""
        **BigQuery Client Not Available**
        
        The BigQuery client failed to initialize. Please check the following:
        1. ✅ Run: `gcloud auth application-default login` (you've done this)
        2. ✅ Verify credentials: The app should automatically use Application Default Credentials
        3. ⚠️ Check error details below for specific issues
        
        **Troubleshooting Steps:**
        - Verify you're logged in: `gcloud auth list`
        - Set project: `gcloud config set project maharani-sales-hub-11-2025`
        - Set quota project: `gcloud auth application-default set-quota-project maharani-sales-hub-11-2025`
        - Click "Retry BigQuery Connection" button below to retry initialization
        - Restart the Streamlit app after making changes
        """)
        
        # Add retry button with better feedback
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Retry BigQuery Connection", use_container_width=True):
                # Clear the error and retry initialization
                if 'bq_error' in st.session_state:
                    del st.session_state.bq_error
                st.session_state.bq_client = None
                with st.spinner("Initializing BigQuery client..."):
                    success, message = init_bigquery_client()
                    if success:
                        st.success("✅ " + message)
                        st.rerun()
                    else:
                        st.error("❌ " + message)
                        st.session_state.bq_error = message
        with col2:
            if st.button("🧪 Run Diagnostic Test", use_container_width=True):
                with st.spinner("Running diagnostic test..."):
                    import subprocess
                    import os
                    from pathlib import Path
                    # Get project root (parent of web_app directory)
                    project_root = Path(__file__).parent.parent
                    test_script = project_root / "test_bq_init.py"
                    
                    if test_script.exists():
                        result = subprocess.run(
                            ["python", str(test_script)],
                            capture_output=True,
                            text=True,
                            cwd=str(project_root)
                        )
                        st.code(result.stdout, language="text")
                        if result.stderr:
                            st.code(result.stderr, language="text")
                    else:
                        st.error(f"Test script not found at: {test_script}")
                        # Run inline test - use the BigQueryClient that's already imported
                        st.info("Running inline diagnostic test...")
                        try:
                            import os
                            
                            os.environ["GCP_PROJECT_ID"] = PROJECT_ID
                            
                            # Test 1: ADC
                            from google.auth import default
                            creds, proj = default()
                            st.success(f"✅ ADC working! Project: {proj}")
                            
                            # Test 2: Check if BigQueryClient is available
                            if not BQ_AVAILABLE:
                                st.error("❌ BigQueryClient not available - import failed at startup")
                                st.warning("Trying to import BigQueryClient now...")
                                # Try to import now with path set
                                try:
                                    if str(project_root) not in sys.path:
                                        sys.path.insert(0, str(project_root))
                                    from utils.bigquery_client import BigQueryClient
                                    st.success("✅ BigQueryClient imported successfully!")
                                    # Now try to use it
                                    client = BigQueryClient(project_id=PROJECT_ID)
                                    st.success("✅ BigQueryClient created")
                                    result = client.query("SELECT 1 as test", max_results=1)
                                    st.success(f"✅ Query successful: {result}")
                                    st.success("🎉 All diagnostic tests passed! BigQuery should work.")
                                    st.info("💡 The import failed at startup but works now. Try restarting Streamlit.")
                                except ImportError as import_err:
                                    st.error(f"❌ Import still failed: {import_err}")
                                    st.info(f"Project root: {project_root}")
                                    st.info(f"Utils exists: {(project_root / 'utils').exists()}")
                            else:
                                st.success("✅ BigQueryClient is available (imported at startup)")
                                
                                # Test 3: Initialize
                                client = BigQueryClient(project_id=PROJECT_ID)
                                st.success("✅ BigQueryClient created")
                                
                                # Test 4: Query
                                result = client.query("SELECT 1 as test", max_results=1)
                                st.success(f"✅ Query successful: {result}")
                                
                                st.success("🎉 All diagnostic tests passed! BigQuery should work.")
                        except Exception as e:
                            import traceback
                            st.error(f"❌ Test failed: {str(e)}")
                            with st.expander("Full traceback"):
                                st.code(traceback.format_exc(), language="text")
                            # Show debug info
                            with st.expander("Debug Info"):
                                st.code(f"""
BQ_AVAILABLE: {BQ_AVAILABLE}
Project root: {project_root}
sys.path (first 5): {sys.path[:5]}
Current working directory: {os.getcwd()}
__file__: {__file__}
                                """, language="text")
        
        if error_msg:
            with st.expander("🔍 Detailed Error Information", expanded=True):
                st.code(error_msg, language="text")
                st.info("💡 **Tip:** Copy this error and check if it's a permissions issue or missing dataset.")
                
                # Try to diagnose common issues
                error_lower = error_msg.lower()
                if "credentials" in error_lower or "authentication" in error_lower:
                    st.warning("""
                    **Credentials Issue Detected:**
                    - Run: `gcloud auth application-default login`
                    - Verify: `gcloud auth list`
                    - Set quota: `gcloud auth application-default set-quota-project maharani-sales-hub-11-2025`
                    """)
                elif "permission" in error_lower or "denied" in error_lower:
                    st.warning("""
                    **Permission Issue Detected:**
                    - Your account may not have BigQuery access
                    - Contact Anand to grant BigQuery Data Viewer and Job User roles
                    """)
                elif "not found" in error_lower or "does not exist" in error_lower:
                    st.info("""
                    **Table/Dataset Not Found:**
                    - This might be normal if data hasn't been synced yet
                    - The app will work once data is available
                    """)
        total_accounts_count = high_priority_count = unmatched_count = opportunities_count = 0
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Accounts", f"{total_accounts_count:,}")
    with col2:
        st.metric("High Priority", f"{high_priority_count:,}")
    with col3:
        st.metric("Unmatched Emails", f"{unmatched_count:,}")
    with col4:
        st.metric("Open Opportunities", f"{opportunities_count:,}")
    
    st.markdown("---")
    
    # Top priority accounts
    st.subheader("Top Priority Accounts")
    
    # Test mode option for Dashboard
    test_mode_dashboard = st.checkbox("🧪 Test Mode (10 accounts)", value=False, key="dashboard_test", help="Test with only 10 accounts for faster testing")
    
    if st.button("Refresh Account Scores"):
        request_data = {}
        if test_mode_dashboard:
            request_data = {"limit": 10}
            st.info("🧪 Test Mode: Scoring only 10 accounts for testing purposes")
        
        with st.spinner("Refreshing account scores..."):
            result = call_function("account-scoring", request_data)
            if "error" in result:
                error_type = result.get("error_type", "unknown")
                if error_type == "not_deployed":
                    st.warning(f"⚠️ {result['error']}")
                    with st.expander("How to deploy Cloud Functions"):
                        st.code("""
# Deploy Phase 2 Functions including account-scoring:
./scripts/deploy_phase2_functions.ps1

# Or deploy individually:
gcloud functions deploy account-scoring `
  --gen2 --runtime=python311 --region=us-central1 `
  --source=. `
  --entry-point=account_scoring_job `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com `
  --memory=2048MB `
  --timeout=540s `
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,LLM_PROVIDER=vertex_ai" `
  --project=maharani-sales-hub-11-2025
                        """, language="bash")
                    if "suggestion" in result:
                        st.info(f"💡 {result['suggestion']}")
                else:
                    st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ Successfully scored {result.get('accounts_scored', 0)} accounts!")
                st.rerun()
    
    # Display top accounts
    if st.session_state.bq_client:
        try:
            try:
                top_accounts_query = f"""
                SELECT 
                    a.account_name,
                    r.priority_score,
                    r.budget_likelihood,
                    r.engagement_score,
                    r.recommended_action,
                    r.last_interaction_date
                FROM `{PROJECT_ID}.sales_intelligence.account_recommendations` r
                JOIN `{PROJECT_ID}.sales_intelligence.sf_accounts` a
                    ON r.account_id = a.account_id
                WHERE r.score_date = (
                    SELECT MAX(score_date) 
                    FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                )
                ORDER BY r.priority_score DESC
                LIMIT 20
                """
                top_accounts = query_bigquery(top_accounts_query)
                if top_accounts:
                    df = pd.DataFrame(top_accounts)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No account scores available for today. Click 'Refresh Account Scores' to generate.")
            except Exception as e:
                st.info("Account scoring has not been run yet. Click 'Refresh Account Scores' to generate scores.")
        except Exception as e:
            st.error(f"Error loading accounts: {str(e)}")
    else:
        st.info("""
        💡 **BigQuery Client Not Available**
        
        Account scores are generated daily at 7 AM when the system is fully deployed.
        To view scores, ensure:
        1. BigQuery client is configured (GCP credentials)
        2. Cloud Functions are deployed
        3. Account scoring has run at least once
        
        For now, you can use the "Refresh Account Scores" button above once functions are deployed.
        """)

# Account Scoring Page
elif page == "Account Scoring":
    st.title("Account Scoring")
    st.markdown("AI-powered account prioritization and scoring")
    
    st.info("""
    **Account Scoring Methodology**
    
    Account scores are generated daily using AI analysis of:
    - **Email Engagement** - Response rates and interaction patterns
    - **Call Activity** - Call frequency and sentiment analysis
    - **Opportunities** - Pipeline health and deal progression
    - **Activity Level** - Overall account activity and touchpoints
    """)
    
    # Refresh button at top
    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 1, 3])
    with col_refresh1:
        test_mode = st.checkbox("🧪 Test Mode (10 accounts)", value=False, help="Test with only 10 accounts for faster testing")
    with col_refresh2:
        if st.button("🔄 Refresh Account Scores", type="primary"):
            request_data = {}
            if test_mode:
                request_data = {"limit": 10}
                st.info("🧪 Test Mode: Scoring only 10 accounts for testing purposes")
            
            with st.spinner("Refreshing account scores... This may take a few minutes."):
                result = call_function("account-scoring", request_data)
                if "error" in result:
                    error_type = result.get("error_type", "unknown")
                    if error_type == "not_deployed":
                        st.warning(f"⚠️ {result['error']}")
                        with st.expander("How to deploy Cloud Functions"):
                            st.code("""
# Deploy Phase 2 Functions including account-scoring:
.\scripts\deploy_phase2_functions.ps1

# Or deploy individually:
gcloud functions deploy account-scoring `
  --gen2 --runtime=python311 --region=us-central1 `
  --source=. `
  --entry-point=account_scoring_job `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com `
  --memory=2048MB `
  --timeout=540s `
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,LLM_PROVIDER=vertex_ai" `
  --project=maharani-sales-hub-11-2025
                            """, language="bash")
                        if "suggestion" in result:
                            st.info(f"💡 {result['suggestion']}")
                    elif error_type == "service_unavailable":
                        st.warning(f"⚠️ {result['error']}")
                        if "suggestion" in result:
                            st.info(f"💡 {result['suggestion']}")
                    else:
                        st.error(f"❌ {result.get('error', 'Unknown error occurred')}")
                else:
                    accounts_scored = result.get('accounts_scored', 0)
                    st.success(f"✅ Successfully scored {accounts_scored} accounts!")
                    st.rerun()
    
    if st.session_state.bq_client:
        # Score distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Priority Score Distribution")
            try:
                dist_query = f"""
                SELECT 
                    CASE 
                        WHEN priority_score >= 80 THEN 'High (80-100)'
                        WHEN priority_score >= 60 THEN 'Medium (60-79)'
                        ELSE 'Low (0-59)'
                    END as score_range,
                    COUNT(*) as count
                FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                WHERE score_date = (
                    SELECT MAX(score_date) 
                    FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                )
                GROUP BY score_range
                ORDER BY score_range
                """
                dist_data = query_bigquery(dist_query)
                if dist_data:
                    df_dist = pd.DataFrame(dist_data)
                    if not df_dist.empty and 'count' in df_dist.columns:
                        # Set index and ensure count column is numeric
                        df_dist = df_dist.set_index('score_range')
                        df_dist['count'] = pd.to_numeric(df_dist['count'], errors='coerce')
                        st.bar_chart(df_dist)
                    else:
                        st.info("No distribution data available")
                else:
                    st.info("No distribution data available")
            except Exception as e:
                st.info("No distribution data available")
        
        with col2:
            st.subheader("Budget Likelihood")
            try:
                budget_query = f"""
                SELECT 
                    CASE 
                        WHEN budget_likelihood >= 70 THEN 'High (70-100)'
                        WHEN budget_likelihood >= 50 THEN 'Medium (50-69)'
                        ELSE 'Low (0-49)'
                    END as likelihood_range,
                    COUNT(*) as count
                FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                WHERE score_date = (
                    SELECT MAX(score_date) 
                    FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                )
                GROUP BY likelihood_range
                ORDER BY likelihood_range
                """
                budget_data = query_bigquery(budget_query)
                if budget_data:
                    df_budget = pd.DataFrame(budget_data)
                    if not df_budget.empty and 'count' in df_budget.columns:
                        # Set index and ensure count column is numeric
                        df_budget = df_budget.set_index('likelihood_range')
                        df_budget['count'] = pd.to_numeric(df_budget['count'], errors='coerce')
                        st.bar_chart(df_budget)
                    else:
                        st.info("No budget likelihood data available")
                else:
                    st.info("No budget likelihood data available")
            except Exception as e:
                st.info("No budget likelihood data available")
        
        # Account list
        st.subheader("All Account Scores")
        try:
            # Try today first, then fall back to most recent
            all_scores_query = f"""
            SELECT 
                a.account_name,
                r.priority_score,
                r.budget_likelihood,
                r.engagement_score,
                r.reasoning,
                r.recommended_action,
                r.key_signals,
                r.last_interaction_date,
                r.score_date
            FROM `{PROJECT_ID}.sales_intelligence.account_recommendations` r
            JOIN `{PROJECT_ID}.sales_intelligence.sf_accounts` a
                ON r.account_id = a.account_id
            WHERE r.score_date = (
                SELECT MAX(score_date) 
                FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
            )
            ORDER BY r.priority_score DESC
            LIMIT 100
            """
            all_scores = query_bigquery(all_scores_query, max_results=100)
            if all_scores and len(all_scores) > 0:
                df = pd.DataFrame(all_scores)
                # Show score date info
                if 'score_date' in df.columns and not df.empty:
                    latest_date = df['score_date'].iloc[0] if len(df) > 0 else None
                    if latest_date:
                        st.caption(f"📅 Showing scores from: {latest_date}")
                # Remove score_date from display
                if 'score_date' in df.columns:
                    df_display = df.drop(columns=['score_date'])
                else:
                    df_display = df
                st.dataframe(df_display, use_container_width=True, height=400)
            else:
                st.info("""
                ℹ️ **No scores available yet.**
                
                Click the "🔄 Refresh Account Scores" button above to generate scores for all accounts.
                This process may take several minutes depending on the number of accounts.
                """)
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Error loading scores: {error_msg}")
            if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                st.info("💡 The account_recommendations table may not exist yet. Run account scoring first.")
            else:
                with st.expander("🔍 Error Details"):
                    st.code(error_msg)

# Natural Language Query Page
elif page == "Natural Language Query":
    st.title("Natural Language Query")
    st.markdown("Ask questions about your sales data in plain English")
    
    st.info("""
    **How It Works**
    
    Ask questions about your sales data in plain English. The AI will convert your question into SQL and execute it.
    
    **Example Queries:**
    - "Show me accounts with high engagement in the last week"
    - "Which accounts are discussing budget for 2026?"
    - "Find contacts who haven't been called in 30 days"
    """)
    
    query = st.text_area("Enter your question:", height=100)
    
    if st.button("Execute Query"):
        if query:
            with st.spinner("Processing your query..."):
                result = call_function("nlp-query", {"query": query})
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success("Query executed successfully!")
                    
                    # Show SQL
                    if "sql" in result:
                        with st.expander("Generated SQL"):
                            st.code(result["sql"], language="sql")
                    
                    # Show results
                    if "results" in result and result["results"]:
                        df = pd.DataFrame(result["results"])
                        st.dataframe(df, use_container_width=True)
                        
                        # Show summary
                        if "summary" in result:
                            st.info(result["summary"])
                    else:
                        st.info("No results found.")
        else:
            st.warning("Please enter a query.")

# Semantic Search Page
elif page == "Semantic Search":
    st.title("Semantic Search")
    st.markdown("AI-powered intent-based search across all communications")
    
    st.info("""
    **AI-Powered Semantic Search**
    
    Find accounts, emails, or calls by intent using advanced vector search technology. Search by meaning, not just keywords.
    
    **Example Searches:**
    - "budget discussions for 2026" - Find budget-related conversations
    - "renewal concerns" - Discover accounts worried about renewals
    - "pricing negotiations" - Locate pricing discussion threads
    """)
    
    search_query = st.text_input("Enter search query:")
    search_type = st.selectbox("Search Type", ["accounts", "emails", "calls"])
    limit = st.slider("Results Limit", 10, 100, 50)
    days_back = st.slider("Days Back", 7, 180, 60)
    min_similarity = st.slider("Minimum Similarity", 0.0, 1.0, 0.7, 0.05)
    
    if st.button("Search"):
        if search_query:
            with st.spinner("Searching..."):
                result = call_function("semantic-search", {
                    "query": search_query,
                    "type": search_type,
                    "limit": limit,
                    "days_back": days_back,
                    "min_similarity": min_similarity
                })
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                elif "results" in result and result["results"]:
                    st.success(f"Found {result['count']} results")
                    df = pd.DataFrame(result["results"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No results found. Try adjusting similarity threshold or search query.")
        else:
            st.warning("Please enter a search query.")

# Unmatched Emails Page
elif page == "Unmatched Emails":
    st.title("Unmatched Emails")
    st.markdown("Create leads from emails with unknown contacts")
    
    st.markdown("""
    Emails from contacts not yet in Salesforce. Create leads from these emails.
    """)
    
    limit = st.slider("Number of emails to show", 10, 100, 20)
    
    if st.button("Load Unmatched Emails"):
        if st.session_state.bq_client:
            try:
                unmatched_query = f"""
                SELECT 
                    p.participant_id,
                    p.email_address,
                    m.subject,
                    m.sent_at,
                    m.mailbox_email,
                    m.from_email,
                    LEFT(m.body_text, 200) as body_preview
                FROM `{PROJECT_ID}.sales_intelligence.gmail_participants` p
                JOIN `{PROJECT_ID}.sales_intelligence.gmail_messages` m
                    ON p.message_id = m.message_id
                WHERE p.sf_contact_id IS NULL
                    AND p.role = 'from'
                    AND m.sent_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
                    AND p.email_address NOT LIKE '%maharaniweddings.com'
                    AND p.email_address NOT LIKE '%noreply%'
                ORDER BY m.sent_at DESC
                LIMIT {limit}
                """
                unmatched_emails = query_bigquery(unmatched_query)
                if unmatched_emails:
                    st.session_state.unmatched_emails = unmatched_emails
                    st.success(f"Loaded {len(unmatched_emails)} unmatched emails")
                else:
                    st.info("No unmatched emails found")
            except Exception as e:
                st.error(f"Error loading emails: {str(e)}")
        else:
            st.warning("BigQuery client not available")
    
    if 'unmatched_emails' in st.session_state and st.session_state.unmatched_emails:
        st.subheader("Create Leads")
        
        # Display emails with checkboxes
        selected_emails = []
        for email_data in st.session_state.unmatched_emails:
            key = email_data.get('participant_id', email_data.get('email_address'))
            if st.checkbox(
                f"{email_data.get('email_address')} - {email_data.get('subject', 'No subject')}",
                key=key
            ):
                selected_emails.append(email_data)
        
        if st.button("Create Leads from Selected"):
            if selected_emails:
                with st.spinner("Creating leads..."):
                    result = call_function("create-leads", {
                        "limit": len(selected_emails),
                        "emails": [e.get("email_address") for e in selected_emails]
                    })
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success(f"Created {result.get('created', 0)} leads")
                        # Refresh unmatched emails
                        if 'unmatched_emails' in st.session_state:
                            del st.session_state.unmatched_emails
                        st.rerun()
            else:
                st.warning("Please select at least one email.")

# Account Details Page
elif page == "Account Details":
    st.title("Account Details")
    st.markdown("Complete account information and interaction history")
    
    account_search = st.text_input("Search Account by ID or Name:")
    
    if account_search:
        if st.session_state.bq_client:
            try:
                # Get account details
                account_query = f"""
                SELECT *
                FROM `{PROJECT_ID}.sales_intelligence.sf_accounts`
                WHERE account_id = @account_id OR account_name LIKE @account_name
                LIMIT 1
                """
                # Use parameterized query to prevent SQL injection
                # Escape single quotes in search term
                safe_search = account_search.replace("'", "''")
                account_query = f"""
                SELECT *
                FROM `{PROJECT_ID}.sales_intelligence.sf_accounts`
                WHERE account_id = '{safe_search}' OR account_name LIKE '%{safe_search}%'
                LIMIT 1
                """
                accounts = query_bigquery(account_query)
                
                if accounts:
                    account = accounts[0]
                    account_id = account['account_id']
                    # Escape account_id to prevent SQL injection (define once for all tabs)
                    safe_account_id = account_id.replace("'", "''")
                    
                    st.subheader(f"Account: {account.get('account_name', 'Unknown')}")
                    
                    # Tabs for different views
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "Overview", "Emails", "Calls", "Opportunities", "Scores"
                    ])
                    
                    with tab1:
                        try:
                            st.json(account)
                        except Exception as e:
                            st.error(f"Error displaying account data: {str(e)}")
                            st.write("**Account Data:**")
                            for key, value in account.items():
                                st.write(f"**{key}:** {value}")
                        
                        # Get latest score
                        score_query = f"""
                        SELECT *
                        FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                        WHERE account_id = '{safe_account_id}'
                        ORDER BY score_date DESC
                        LIMIT 1
                        """
                        scores = query_bigquery(score_query)
                        if scores:
                            st.subheader("Latest Account Score")
                            try:
                                st.json(scores[0])
                            except Exception as e:
                                st.error(f"Error displaying score data: {str(e)}")
                                st.write("**Score Data:**")
                                for key, value in scores[0].items():
                                    st.write(f"**{key}:** {value}")
                    
                    with tab2:
                        email_query = f"""
                        SELECT 
                            m.subject,
                            m.from_email,
                            m.sent_at,
                            LEFT(m.body_text, 300) as body_preview
                        FROM `{PROJECT_ID}.sales_intelligence.gmail_messages` m
                        JOIN `{PROJECT_ID}.sales_intelligence.gmail_participants` p
                            ON m.message_id = p.message_id
                        WHERE p.sf_account_id = '{safe_account_id}'
                        ORDER BY m.sent_at DESC
                        LIMIT 20
                        """
                        emails = query_bigquery(email_query)
                        if emails:
                            st.dataframe(pd.DataFrame(emails), use_container_width=True)
                        else:
                            st.info("No emails found")
                    
                    with tab3:
                        call_query = f"""
                        SELECT 
                            direction,
                            from_number,
                            to_number,
                            duration_seconds,
                            call_time,
                            sentiment_score
                        FROM `{PROJECT_ID}.sales_intelligence.dialpad_calls`
                        WHERE matched_account_id = '{safe_account_id}'
                        ORDER BY call_time DESC
                        LIMIT 20
                        """
                        calls = query_bigquery(call_query)
                        if calls:
                            st.dataframe(pd.DataFrame(calls), use_container_width=True)
                        else:
                            st.info("No calls found")
                    
                    with tab4:
                        opp_query = f"""
                        SELECT *
                        FROM `{PROJECT_ID}.sales_intelligence.sf_opportunities`
                        WHERE account_id = '{safe_account_id}'
                        ORDER BY created_date DESC
                        """
                        opps = query_bigquery(opp_query)
                        if opps:
                            st.dataframe(pd.DataFrame(opps), use_container_width=True)
                        else:
                            st.info("No opportunities found")
                    
                    with tab5:
                        all_scores_query = f"""
                        SELECT *
                        FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                        WHERE account_id = '{safe_account_id}'
                        ORDER BY score_date DESC
                        LIMIT 30
                        """
                        all_scores = query_bigquery(all_scores_query)
                        if all_scores:
                            st.dataframe(pd.DataFrame(all_scores), use_container_width=True)
                        else:
                            st.info("No scores available")
                else:
                    st.warning("Account not found")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("BigQuery client not available")

# Email Threads Page
elif page == "Email Threads":
    st.title("Email Threads")
    st.markdown("View conversations and generate AI-powered replies")
    
    thread_search = st.text_input("Enter Thread ID or Email Address:")
    
    if thread_search:
        if st.session_state.bq_client:
            try:
                # Get thread - escape search term to prevent SQL injection
                safe_thread_search = thread_search.replace("'", "''")
                thread_query = f"""
                SELECT 
                    message_id,
                    thread_id,
                    subject,
                    from_email,
                    to_emails,
                    sent_at,
                    body_text
                FROM `{PROJECT_ID}.sales_intelligence.gmail_messages`
                WHERE thread_id = '{safe_thread_search}' OR from_email = '{safe_thread_search}'
                ORDER BY sent_at ASC
                """
                thread_emails = query_bigquery(thread_query)
                
                if thread_emails:
                    st.subheader(f"Thread: {thread_emails[0].get('subject', 'No subject')}")
                    
                    # Display thread
                    for idx, email in enumerate(thread_emails):
                        email_from = email.get('from_email', 'Unknown')
                        email_date = email.get('sent_at', 'Unknown date')
                        email_body = email.get('body_text', 'No content')
                        with st.expander(f"{email_from} - {email_date}"):
                            st.write("**Subject:**", email.get('subject', 'No subject'))
                            st.write("**Body:**")
                            st.write(email_body)
                    
                    # AI Reply Generation
                    st.subheader("🤖 Generate AI Reply")
                    
                    # Create options for selectbox with message preview
                    message_options = [
                        f"{e.get('from_email', 'Unknown')} - {e.get('subject', 'No subject')[:50]}"
                        for e in thread_emails
                    ]
                    selected_idx = st.selectbox(
                        "Select message to reply to:",
                        range(len(thread_emails)),
                        format_func=lambda x: message_options[x] if x < len(message_options) else "Unknown"
                    )
                    message_id = thread_emails[selected_idx]['message_id'] if thread_emails else None
                    
                    if st.button("Generate Reply"):
                        if message_id:
                            with st.spinner("Generating AI reply..."):
                                result = call_function("generate-email-reply", {
                                    "thread_id": thread_emails[0].get('thread_id'),
                                    "message_id": message_id,
                                    "reply_to_email": thread_emails[-1].get('from_email'),
                                    "send": False
                                })
                                
                                if "error" in result:
                                    st.error(f"Error: {result['error']}")
                                elif "reply_text" in result:
                                    st.text_area("Generated Reply:", result["reply_text"], height=200)
                                    
                                    if st.button("Send Reply"):
                                        st.info("Sending requires Gmail OAuth token. Feature coming soon.")
                                else:
                                    st.error("Failed to generate reply")
                else:
                    st.warning("Thread not found")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("BigQuery client not available")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #9ca3af; font-size: 0.75rem;'>
    Sales Intelligence v2.0
</div>
""", unsafe_allow_html=True)

