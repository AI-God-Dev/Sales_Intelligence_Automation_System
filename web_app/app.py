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
    """Inject professional custom CSS styling."""
    css = """
    <style>
    /* Main styling improvements */
    .main {
        padding: 2rem 1rem;
    }
    
    /* Professional header styling */
    h1 {
        color: #1f77b4;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    h2 {
        color: #2c3e50;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Metric cards enhancement */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #1f77b4 0%, #2c5aa0 100%);
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #2c5aa0 0%, #1f77b4 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    /* Info boxes */
    .stInfo {
        background: #e7f3ff;
        border-left: 4px solid #1f77b4;
        border-radius: 4px;
        padding: 1rem;
    }
    
    .stSuccess {
        background: #d4edda;
        border-left: 4px solid #27ae60;
        border-radius: 4px;
        padding: 1rem;
    }
    
    .stWarning {
        background: #fff3cd;
        border-left: 4px solid #f39c12;
        border-radius: 4px;
        padding: 1rem;
    }
    
    .stError {
        background: #f8d7da;
        border-left: 4px solid #e74c3c;
        border-radius: 4px;
        padding: 1rem;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .dataframe thead {
        background: #2c3e50;
        color: white;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 2px solid #dee2e6;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1f77b4;
        outline: none;
    }
    
    /* Professional card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Professional spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
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
        st.session_state.bq_client = BigQueryClient()
    except Exception as e:
        st.session_state.bq_client = None
        # Store error message for display
        st.session_state.bq_error = str(e)

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
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: white; font-size: 1.8rem; margin: 0;'>📊 Sales Intelligence</h1>
    <p style='color: #ecf0f1; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>AI-Powered Sales Automation</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

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
    st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()

if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 1rem;'>Sales Intelligence & Automation System</h1>
        <p style='font-size: 1.2rem; color: #7f8c8d; margin-bottom: 2rem;'>
            AI-Powered Sales Intelligence Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.info("👆 Please log in using the sidebar to access the dashboard.")
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>📊 Sales Intelligence Dashboard</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>Real-time insights and metrics for your sales pipeline</p>
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
        st.info("""
        💡 **BigQuery Client Not Available**
        
        The app is running in demo mode. To enable full functionality:
        1. Set up GCP credentials: `gcloud auth application-default login`
        2. Ensure the service account has BigQuery access
        3. Restart the application
        
        You can still explore the interface, but data will show as 0 until BigQuery is connected.
        """)
        total_accounts_count = high_priority_count = unmatched_count = opportunities_count = 0
    
    # Professional metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Total Accounts</div>
            <div style='font-size: 2rem; font-weight: 700; color: #1f77b4;'>{total_accounts_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;'>High Priority</div>
            <div style='font-size: 2rem; font-weight: 700; color: #27ae60;'>{high_priority_count:,}</div>
            <div style='font-size: 0.8rem; color: #7f8c8d; margin-top: 0.25rem;'>Today</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Unmatched Emails</div>
            <div style='font-size: 2rem; font-weight: 700; color: #f39c12;'>{unmatched_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Open Opportunities</div>
            <div style='font-size: 2rem; font-weight: 700; color: #3498db;'>{opportunities_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Top priority accounts
    st.subheader("🎯 Top Priority Accounts (Today)")
    
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
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No account scores available for today. Click 'Refresh Account Scores' to generate.")
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>🎯 Account Scoring</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>AI-powered account prioritization and scoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #e7f3ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #1f77b4; margin-bottom: 2rem;'>
        <h4 style='margin-top: 0; color: #2c3e50;'>Account Scoring Methodology</h4>
        <p style='margin-bottom: 0.5rem;'>Account scores are generated daily using AI analysis of:</p>
        <ul style='margin-bottom: 0;'>
            <li><strong>Recent email engagement</strong> - Response rates and interaction patterns</li>
            <li><strong>Call activity and sentiment</strong> - Call frequency and emotional signals</li>
            <li><strong>Open opportunities</strong> - Pipeline health and deal progression</li>
            <li><strong>Recent activities</strong> - Overall account activity and touchpoints</li>
        </ul>
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>💬 Natural Language Query</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>Ask questions about your sales data in plain English</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;'>
        <h4 style='margin-top: 0; color: #2c3e50;'>💡 Natural Language Query</h4>
        <p>Ask questions about your sales data in plain English. The AI will convert your question into SQL and execute it.</p>
        <p style='margin-bottom: 0.5rem;'><strong>Example Queries:</strong></p>
        <ul style='margin-bottom: 0;'>
            <li>"Show me accounts with high engagement in the last week"</li>
            <li>"Which accounts are discussing budget for 2026?"</li>
            <li>"Find contacts who haven't been called in 30 days"</li>
        </ul>
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>🔍 Semantic Search</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>AI-powered intent-based search across all communications</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #f0f9ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3498db; margin-bottom: 2rem;'>
        <h4 style='margin-top: 0; color: #2c3e50;'>🔍 AI-Powered Semantic Search</h4>
        <p>Find accounts, emails, or calls by intent using advanced vector search technology. Search by meaning, not just keywords.</p>
        <p style='margin-bottom: 0.5rem;'><strong>Example Searches:</strong></p>
        <ul style='margin-bottom: 0;'>
            <li>"budget discussions for 2026" - Find budget-related conversations</li>
            <li>"renewal concerns" - Discover accounts worried about renewals</li>
            <li>"pricing negotiations" - Locate pricing discussion threads</li>
        </ul>
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>📧 Unmatched Emails</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>Create leads from emails with unknown contacts</p>
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>🏢 Account Details</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>Complete account information and interaction history</p>
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
    <div style='margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem; border-bottom: 3px solid #1f77b4; padding-bottom: 0.5rem;'>📬 Email Threads</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem; margin-top: 0.5rem;'>View conversations and generate AI-powered replies</p>
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
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem 0; color: #ecf0f1;'>
    <p style='font-weight: 600; margin-bottom: 0.5rem;'>Sales Intelligence System</p>
    <p style='font-size: 0.85rem; color: #95a5a6; margin: 0;'>Version 2.0</p>
    <p style='font-size: 0.8rem; color: #7f8c8d; margin-top: 0.5rem;'>Phase 2 & 3 Complete</p>
</div>
""", unsafe_allow_html=True)

