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
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

# Inject custom CSS for professional styling
def inject_custom_css():
    """Inject professional custom CSS styling with modern design system."""
    css = """
    <style>
    /* ===== DESIGN SYSTEM ===== */
    :root {
        --primary: #2563eb;
        --primary-dark: #1e40af;
        --primary-light: #3b82f6;
        --secondary: #64748b;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: #3b82f6;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-tertiary: #94a3b8;
        --border: #e2e8f0;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
        --radius-xl: 1rem;
    }
    
    /* ===== GLOBAL RESET & BASE ===== */
    * {
        box-sizing: border-box;
    }
    
    .main {
        padding: 2rem 2.5rem;
        background: var(--bg-secondary);
        min-height: 100vh;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }
    
    /* ===== TYPOGRAPHY ===== */
    h1 {
        color: var(--text-primary);
        font-weight: 800;
        font-size: 2.5rem;
        line-height: 1.2;
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 1.875rem;
        margin-top: 2.5rem;
        margin-bottom: 1.25rem;
        letter-spacing: -0.01em;
    }
    
    h3 {
        color: var(--text-primary);
        font-weight: 600;
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    p {
        color: var(--text-secondary);
        line-height: 1.7;
    }
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        box-shadow: var(--shadow-xl);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e2e8f0;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: #cbd5e1 !important;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] .stTextInput label {
        color: #cbd5e1 !important;
    }
    
    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: var(--bg-primary);
        padding: 2rem;
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        height: 100%;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }
    
    .metric-card.success::before {
        background: linear-gradient(90deg, var(--success) 0%, #34d399 100%);
    }
    
    .metric-card.warning::before {
        background: linear-gradient(90deg, var(--warning) 0%, #fbbf24 100%);
    }
    
    .metric-card.info::before {
        background: linear-gradient(90deg, var(--info) 0%, #60a5fa 100%);
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1;
        margin-bottom: 0.5rem;
        font-variant-numeric: tabular-nums;
    }
    
    .metric-icon {
        font-size: 1.5rem;
        opacity: 0.8;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        color: white;
        border-radius: var(--radius-md);
        padding: 0.75rem 1.75rem;
        font-weight: 600;
        font-size: 0.9375rem;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-md);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* ===== ALERT BOXES ===== */
    .stInfo {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-left: 4px solid var(--info);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border-left: 4px solid var(--success);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 4px solid var(--warning);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left: 4px solid var(--error);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    
    /* ===== DATA TABLES ===== */
    .dataframe {
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        background: var(--bg-primary);
    }
    
    .dataframe thead {
        background: linear-gradient(135deg, var(--text-primary) 0%, #1e293b 100%);
        color: white;
    }
    
    .dataframe thead th {
        padding: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    
    .dataframe tbody tr {
        transition: background-color 0.2s;
    }
    
    .dataframe tbody tr:hover {
        background-color: var(--bg-tertiary);
    }
    
    .dataframe tbody td {
        padding: 0.875rem 1rem;
        border-bottom: 1px solid var(--border);
    }
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border-radius: var(--radius-md);
        border: 2px solid var(--border);
        padding: 0.75rem 1rem;
        transition: all 0.2s;
        background: var(--bg-primary);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary);
        outline: none;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* ===== CARDS & CONTAINERS ===== */
    .content-card {
        background: var(--bg-primary);
        padding: 2rem;
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border);
    }
    
    /* ===== LOADING STATES ===== */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .loading-skeleton {
        background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%);
        background-size: 200% 100%;
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        border-radius: var(--radius-md);
        height: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-tertiary);
    }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        .metric-value {
            font-size: 2rem;
        }
    }
    
    /* ===== UTILITY CLASSES ===== */
    .text-gradient {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .badge-error {
        background: #fee2e2;
        color: #991b1b;
    }
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
    from utils.bigquery_client import BigQueryClient
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False

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
FUNCTIONS_BASE_URL = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'bq_client' not in st.session_state:
    st.session_state.bq_client = None

# Initialize BigQuery client if available
if BQ_AVAILABLE and st.session_state.bq_client is None:
    try:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info("Initializing BigQuery client...")
        st.session_state.bq_client = BigQueryClient()
        logger.info("BigQuery client initialized successfully")
    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        st.session_state.bq_client = None
        # Store error message for display
        st.session_state.bq_error = error_details
        import logging
        logging.error(f"BigQuery client initialization failed: {error_details}")

# Helper functions
def get_function_url(function_name: str) -> str:
    """Get Cloud Function URL."""
    return f"{FUNCTIONS_BASE_URL}/{function_name}"

def call_function(function_name: str, data: Dict = None, method: str = "POST") -> Dict:
    """Call a Cloud Function with improved error handling."""
    url = get_function_url(function_name)
    try:
        if method == "GET":
            response = requests.get(url, timeout=60)
        else:
            response = requests.post(url, json=data or {}, timeout=60)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        if e.response.status_code == 404:
            return {
                "error": f"Cloud Function '{function_name}' is not deployed yet. Please deploy it using the deployment scripts.",
                "error_type": "not_deployed",
                "suggestion": f"Deploy using: ./scripts/deploy_phase2_functions.sh"
            }
        else:
            return {
                "error": f"HTTP {e.response.status_code}: {str(e)}",
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
        # Don't show error for missing client, it's handled at call site
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

# Sidebar navigation with professional styling
st.sidebar.markdown("""
<div style='text-align: center; padding: 2rem 1rem 1.5rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem;'>
    <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📊</div>
    <h1 style='color: white; font-size: 1.5rem; font-weight: 700; margin: 0; letter-spacing: -0.02em;'>
        Sales Intelligence
    </h1>
    <p style='color: #94a3b8; font-size: 0.875rem; margin: 0.5rem 0 0 0; font-weight: 400;'>
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
        # In production, implement full OAuth flow with redirect
        # For now, fall back to simple email auth
    
    # Simple email authentication (fallback)
    user_email = st.sidebar.text_input("Email", value="anand@maharaniweddings.com")
    if st.sidebar.button("Login"):
        if user_email and "@" in user_email:
            st.session_state.authenticated = True
            st.session_state.user_email = user_email
            st.rerun()
        else:
            st.sidebar.error("Please enter a valid email address")
else:
    st.sidebar.markdown(f"""
    <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem;'>
        <div style='color: #cbd5e1; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>
            Logged in as
        </div>
        <div style='color: white; font-weight: 600; font-size: 0.9375rem; word-break: break-all;'>
            {st.session_state.user_email}
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()

if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align: center; padding: 6rem 2rem; max-width: 600px; margin: 0 auto;'>
        <div style='font-size: 5rem; margin-bottom: 1.5rem;'>📊</div>
        <h1 class='text-gradient' style='margin-bottom: 1rem; font-size: 3rem;'>
            Sales Intelligence
        </h1>
        <p style='font-size: 1.25rem; color: var(--text-secondary); margin-bottom: 3rem; line-height: 1.6;'>
            AI-Powered Sales Intelligence & Automation Platform
        </p>
        <div style='background: var(--bg-primary); padding: 2rem; border-radius: var(--radius-xl); box-shadow: var(--shadow-lg); border: 1px solid var(--border);'>
            <h3 style='color: var(--text-primary); margin-bottom: 1rem;'>Welcome Back</h3>
            <p style='color: var(--text-secondary); margin-bottom: 2rem;'>
                Please log in using the sidebar to access your dashboard
            </p>
            <div style='display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-top: 2rem;'>
                <div style='flex: 1; min-width: 150px; padding: 1rem; background: var(--bg-secondary); border-radius: var(--radius-md);'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📈</div>
                    <strong style='color: var(--text-primary); font-size: 0.875rem;'>Real-time Analytics</strong>
                </div>
                <div style='flex: 1; min-width: 150px; padding: 1rem; background: var(--bg-secondary); border-radius: var(--radius-md);'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🤖</div>
                    <strong style='color: var(--text-primary); font-size: 0.875rem;'>AI-Powered Insights</strong>
                </div>
                <div style='flex: 1; min-width: 150px; padding: 1rem; background: var(--bg-secondary); border-radius: var(--radius-md);'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>⚡</div>
                    <strong style='color: var(--text-primary); font-size: 0.875rem;'>Smart Automation</strong>
                </div>
            </div>
        </div>
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
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>📊 Sales Intelligence Dashboard</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            Real-time insights and metrics for your sales pipeline
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get metrics from BigQuery
    if st.session_state.bq_client:
        try:
            total_accounts_query = f"""
            SELECT COUNT(DISTINCT account_id) as count
            FROM `{PROJECT_ID}.sales_intelligence.sf_accounts`
            """
            total_accounts = query_bigquery(total_accounts_query)
            total_accounts_count = total_accounts[0]['count'] if total_accounts else 0
            
            high_priority_query = f"""
            SELECT COUNT(DISTINCT account_id) as count
            FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
            WHERE score_date = CURRENT_DATE()
            AND priority_score >= 70
            """
            high_priority = query_bigquery(high_priority_query)
            high_priority_count = high_priority[0]['count'] if high_priority else 0
            
            unmatched_query = f"""
            SELECT COUNT(DISTINCT p.participant_id) as count
            FROM `{PROJECT_ID}.sales_intelligence.gmail_participants` p
            WHERE p.sf_contact_id IS NULL
            AND p.role = 'from'
            AND EXISTS (
                SELECT 1 FROM `{PROJECT_ID}.sales_intelligence.gmail_messages` m
                WHERE m.message_id = p.message_id
                AND m.sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
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
            error_msg = f"\n\n**Error Details:** `{st.session_state.bq_error}`"
        
        st.markdown(f"""
        <div class='content-card fade-in' style='background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid var(--warning);'>
            <div style='display: flex; align-items: start; gap: 1rem;'>
                <div style='font-size: 2rem;'>⚠️</div>
                <div style='flex: 1;'>
                    <h3 style='margin-top: 0; color: var(--text-primary); margin-bottom: 0.75rem;'>
                        BigQuery Client Not Available
                    </h3>
                    <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
                        The app is running in demo mode. To enable full functionality:
                    </p>
                    <ol style='color: var(--text-secondary); margin-left: 1.5rem; line-height: 2;'>
                        <li>Set up GCP credentials: <code style='background: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.875rem;'>gcloud auth application-default login</code></li>
                        <li>Ensure the service account has BigQuery access</li>
                        <li>Restart the application</li>
                    </ol>
                    {f'<div style="margin-top: 1rem; padding: 1rem; background: white; border-radius: var(--radius-md); border-left: 3px solid var(--error);"><strong style="color: var(--error);">Error Details:</strong><pre style="margin: 0.5rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary); overflow-x: auto;">{error_msg[:500]}</pre></div>' if error_msg else ''}
                    <p style='color: var(--text-secondary); margin-top: 1rem; margin-bottom: 0; font-size: 0.875rem;'>
                        You can still explore the interface, but data will show as 0 until BigQuery is connected.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        total_accounts_count = high_priority_count = unmatched_count = opportunities_count = 0
    
    # Professional metric cards with icons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card fade-in'>
            <div class='metric-label'>
                <span class='metric-icon'>🏢</span>
                <span>Total Accounts</span>
            </div>
            <div class='metric-value'>{total_accounts_count:,}</div>
            <div style='font-size: 0.875rem; color: var(--text-tertiary); margin-top: 0.5rem;'>
                Active accounts in system
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card success fade-in'>
            <div class='metric-label'>
                <span class='metric-icon'>🎯</span>
                <span>High Priority</span>
            </div>
            <div class='metric-value' style='color: var(--success);'>{high_priority_count:,}</div>
            <div style='font-size: 0.875rem; color: var(--text-tertiary); margin-top: 0.5rem;'>
                Score ≥ 70 • Today
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card warning fade-in'>
            <div class='metric-label'>
                <span class='metric-icon'>📧</span>
                <span>Unmatched Emails</span>
            </div>
            <div class='metric-value' style='color: var(--warning);'>{unmatched_count:,}</div>
            <div style='font-size: 0.875rem; color: var(--text-tertiary); margin-top: 0.5rem;'>
                Last 90 days
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card info fade-in'>
            <div class='metric-label'>
                <span class='metric-icon'>💼</span>
                <span>Open Opportunities</span>
            </div>
            <div class='metric-value' style='color: var(--info);'>{opportunities_count:,}</div>
            <div style='font-size: 0.875rem; color: var(--text-tertiary); margin-top: 0.5rem;'>
                Active in pipeline
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
    
    # Top priority accounts section
    st.markdown("""
    <div class='section-header'>
        <div>
            <h2 style='margin: 0;'>🎯 Top Priority Accounts</h2>
            <p style='color: var(--text-secondary); margin: 0.5rem 0 0 0; font-size: 0.9375rem;'>
                Accounts requiring immediate attention today
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Refresh Account Scores"):
        with st.spinner("Refreshing account scores..."):
            result = call_function("account-scoring", {})
            if "error" in result:
                error_type = result.get("error_type", "unknown")
                if error_type == "not_deployed":
                    st.warning(f"⚠️ {result['error']}")
                    with st.expander("How to deploy Cloud Functions"):
                        st.code("""
# Deploy Phase 2 Functions including account-scoring:
./scripts/deploy_phase2_functions.sh

# Or deploy individually:
gcloud functions deploy account-scoring \\
  --gen2 --runtime=python311 --region=us-central1 \\
  --source=./intelligence/scoring \\
  --entry-point=account_scoring \\
  --trigger-http \\
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \\
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
            WHERE r.score_date = CURRENT_DATE()
            ORDER BY r.priority_score DESC
            LIMIT 20
            """
            top_accounts = query_bigquery(top_accounts_query)
            if top_accounts:
                df = pd.DataFrame(top_accounts)
                st.markdown("""
                <div class='content-card fade-in'>
                """, unsafe_allow_html=True)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "priority_score": st.column_config.NumberColumn(
                            "Priority Score",
                            help="Account priority score (0-100)",
                            format="%.1f",
                            min_value=0,
                            max_value=100,
                        ),
                        "budget_likelihood": st.column_config.NumberColumn(
                            "Budget Likelihood",
                            help="Likelihood of budget availability (0-100)",
                            format="%.1f",
                            min_value=0,
                            max_value=100,
                        ),
                        "engagement_score": st.column_config.NumberColumn(
                            "Engagement",
                            help="Recent engagement score (0-100)",
                            format="%.1f",
                            min_value=0,
                            max_value=100,
                        ),
                    }
                )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='content-card fade-in' style='text-align: center; padding: 3rem 2rem;'>
                    <div style='font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;'>📊</div>
                    <h3 style='color: var(--text-primary); margin-bottom: 0.5rem;'>No Account Scores Available</h3>
                    <p style='color: var(--text-secondary); margin-bottom: 1.5rem;'>
                        Account scores are generated daily. Click the button above to refresh scores.
                    </p>
                </div>
                """, unsafe_allow_html=True)
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
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>🎯 Account Scoring</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            AI-powered account prioritization and scoring
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='content-card fade-in' style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-left: 4px solid var(--info); margin-bottom: 2rem;'>
        <h3 style='margin-top: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;'>
            <span>📈</span>
            <span>Account Scoring Methodology</span>
        </h3>
        <p style='margin-bottom: 1rem; color: var(--text-secondary);'>
            Account scores are generated daily using AI analysis of:
        </p>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;'>
            <div style='padding: 0.75rem; background: white; border-radius: var(--radius-md);'>
                <strong style='color: var(--text-primary);'>📧 Email Engagement</strong>
                <p style='margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);'>
                    Response rates and interaction patterns
                </p>
            </div>
            <div style='padding: 0.75rem; background: white; border-radius: var(--radius-md);'>
                <strong style='color: var(--text-primary);'>📞 Call Activity</strong>
                <p style='margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);'>
                    Call frequency and sentiment analysis
                </p>
            </div>
            <div style='padding: 0.75rem; background: white; border-radius: var(--radius-md);'>
                <strong style='color: var(--text-primary);'>💼 Opportunities</strong>
                <p style='margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);'>
                    Pipeline health and deal progression
                </p>
            </div>
            <div style='padding: 0.75rem; background: white; border-radius: var(--radius-md);'>
                <strong style='color: var(--text-primary);'>⚡ Activity Level</strong>
                <p style='margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);'>
                    Overall account activity and touchpoints
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
                WHERE score_date = CURRENT_DATE()
                GROUP BY score_range
                ORDER BY score_range
                """
                dist_data = query_bigquery(dist_query)
                if dist_data:
                    df_dist = pd.DataFrame(dist_data)
                    st.bar_chart(df_dist.set_index('score_range'))
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
                WHERE score_date = CURRENT_DATE()
                GROUP BY likelihood_range
                ORDER BY likelihood_range
                """
                budget_data = query_bigquery(budget_query)
                if budget_data:
                    df_budget = pd.DataFrame(budget_data)
                    st.bar_chart(df_budget.set_index('likelihood_range'))
            except Exception as e:
                st.info("No budget likelihood data available")
        
        # Account list
        st.subheader("All Account Scores")
        try:
            all_scores_query = f"""
            SELECT 
                a.account_name,
                r.priority_score,
                r.budget_likelihood,
                r.engagement_score,
                r.reasoning,
                r.recommended_action,
                r.key_signals,
                r.last_interaction_date
            FROM `{PROJECT_ID}.sales_intelligence.account_recommendations` r
            JOIN `{PROJECT_ID}.sales_intelligence.sf_accounts` a
                ON r.account_id = a.account_id
            WHERE r.score_date = CURRENT_DATE()
            ORDER BY r.priority_score DESC
            """
            all_scores = query_bigquery(all_scores_query, max_results=100)
            if all_scores:
                df = pd.DataFrame(all_scores)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No scores available. Run account scoring first.")
        except Exception as e:
            st.error(f"Error loading scores: {str(e)}")

# Natural Language Query Page
elif page == "Natural Language Query":
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>💬 Natural Language Query</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            Ask questions about your sales data in plain English
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='content-card fade-in' style='background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); margin-bottom: 2rem;'>
        <h3 style='margin-top: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;'>
            <span>💡</span>
            <span>How It Works</span>
        </h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Ask questions about your sales data in plain English. The AI will convert your question into SQL and execute it.
        </p>
        <div style='background: white; padding: 1.25rem; border-radius: var(--radius-md); border-left: 3px solid var(--primary);'>
            <strong style='color: var(--text-primary); display: block; margin-bottom: 0.75rem;'>Example Queries:</strong>
            <ul style='margin: 0; padding-left: 1.5rem; color: var(--text-secondary); line-height: 2;'>
                <li>"Show me accounts with high engagement in the last week"</li>
                <li>"Which accounts are discussing budget for 2026?"</li>
                <li>"Find contacts who haven't been called in 30 days"</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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

# Semantic Search Page (NEW)
elif page == "Semantic Search":
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>🔍 Semantic Search</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            AI-powered intent-based search across all communications
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='content-card fade-in' style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-left: 4px solid var(--info); margin-bottom: 2rem;'>
        <h3 style='margin-top: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;'>
            <span>🔍</span>
            <span>AI-Powered Semantic Search</span>
        </h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Find accounts, emails, or calls by intent using advanced vector search technology. Search by meaning, not just keywords.
        </p>
        <div style='background: white; padding: 1.25rem; border-radius: var(--radius-md); border-left: 3px solid var(--info);'>
            <strong style='color: var(--text-primary); display: block; margin-bottom: 0.75rem;'>Example Searches:</strong>
            <ul style='margin: 0; padding-left: 1.5rem; color: var(--text-secondary); line-height: 2;'>
                <li><strong>"budget discussions for 2026"</strong> - Find budget-related conversations</li>
                <li><strong>"renewal concerns"</strong> - Discover accounts worried about renewals</li>
                <li><strong>"pricing negotiations"</strong> - Locate pricing discussion threads</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>📧 Unmatched Emails</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            Create leads from emails with unknown contacts
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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
                    AND m.sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
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
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>🏢 Account Details</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            Complete account information and interaction history
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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
                # Simplified query
                account_query = f"""
                SELECT *
                FROM `{PROJECT_ID}.sales_intelligence.sf_accounts`
                WHERE account_id = '{account_search}' OR account_name LIKE '%{account_search}%'
                LIMIT 1
                """
                accounts = query_bigquery(account_query)
                
                if accounts:
                    account = accounts[0]
                    account_id = account['account_id']
                    
                    st.subheader(f"Account: {account.get('account_name', 'Unknown')}")
                    
                    # Tabs for different views
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "Overview", "Emails", "Calls", "Opportunities", "Scores"
                    ])
                    
                    with tab1:
                        st.json(account)
                        
                        # Get latest score
                        score_query = f"""
                        SELECT *
                        FROM `{PROJECT_ID}.sales_intelligence.account_recommendations`
                        WHERE account_id = '{account_id}'
                        ORDER BY score_date DESC
                        LIMIT 1
                        """
                        scores = query_bigquery(score_query)
                        if scores:
                            st.subheader("Latest Account Score")
                            st.json(scores[0])
                    
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
                        WHERE p.sf_account_id = '{account_id}'
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
                        WHERE matched_account_id = '{account_id}'
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
                        WHERE account_id = '{account_id}'
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
                        WHERE account_id = '{account_id}'
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
    st.markdown("""
    <div class='fade-in' style='margin-bottom: 3rem;'>
        <h1>📬 Email Threads</h1>
        <p style='color: var(--text-secondary); font-size: 1.125rem; margin-top: 0.5rem; font-weight: 400;'>
            View conversations and generate AI-powered replies
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    thread_search = st.text_input("Enter Thread ID or Email Address:")
    
    if thread_search:
        if st.session_state.bq_client:
            try:
                # Get thread
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
                WHERE thread_id = '{thread_search}' OR from_email = '{thread_search}'
                ORDER BY sent_at ASC
                """
                thread_emails = query_bigquery(thread_query)
                
                if thread_emails:
                    st.subheader(f"Thread: {thread_emails[0].get('subject', 'No subject')}")
                    
                    # Display thread
                    for email in thread_emails:
                        with st.expander(f"{email.get('from_email')} - {email.get('sent_at')}"):
                            st.write(email.get('body_text', ''))
                    
                    # AI Reply Generation
                    st.subheader("🤖 Generate AI Reply")
                    
                    message_id = st.selectbox(
                        "Select message to reply to:",
                        [e['message_id'] for e in thread_emails]
                    )
                    
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

# Professional Footer
st.sidebar.markdown("""
<div style='position: fixed; bottom: 0; left: 0; right: 0; padding: 1.5rem 1rem; background: rgba(15, 23, 42, 0.5); border-top: 1px solid rgba(255,255,255,0.1);'>
    <div style='text-align: center; color: #94a3b8;'>
        <p style='font-weight: 600; margin-bottom: 0.25rem; color: #cbd5e1; font-size: 0.875rem;'>
            Sales Intelligence System
        </p>
        <p style='font-size: 0.75rem; margin: 0;'>Version 2.0 • Phase 2 & 3</p>
    </div>
</div>
""", unsafe_allow_html=True)

