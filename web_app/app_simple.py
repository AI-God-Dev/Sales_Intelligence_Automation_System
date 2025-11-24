"""
Sales Intelligence & Automation System - Web Application
Streamlit-based web interface for Phase 3
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
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

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

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# Helper functions
def get_function_url(function_name: str) -> str:
    """Get Cloud Function URL."""
    return f"{FUNCTIONS_BASE_URL}/{function_name}"

def call_function(function_name: str, data: Dict = None, method: str = "POST") -> Dict:
    """Call a Cloud Function."""
    url = get_function_url(function_name)
    try:
        if method == "GET":
            response = requests.get(url, timeout=60)
        else:
            response = requests.post(url, json=data or {}, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error calling {function_name}: {str(e)}")
        return {"error": str(e)}

# Sidebar navigation
st.sidebar.title("📊 Sales Intelligence")
st.sidebar.markdown("---")

# Simple authentication (in production, use Google OAuth)
if not st.session_state.authenticated:
    st.sidebar.subheader("Login")
    user_email = st.sidebar.text_input("Email", value="anand@maharaniweddings.com")
    if st.sidebar.button("Login"):
        st.session_state.authenticated = True
        st.session_state.user_email = user_email
        st.rerun()
else:
    st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()

if not st.session_state.authenticated:
    st.title("Sales Intelligence & Automation System")
    st.info("Please log in to access the dashboard.")
    st.stop()

# Navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Account Scoring", "Natural Language Query", "Unmatched Emails", "Account Details", "Email Threads"]
)

# Dashboard Page
if page == "Dashboard":
    st.title("📊 Sales Intelligence Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Accounts", "Loading...")
    with col2:
        st.metric("High Priority", "Loading...")
    with col3:
        st.metric("Unmatched Emails", "Loading...")
    with col4:
        st.metric("Open Opportunities", "Loading...")
    
    st.markdown("---")
    
    # Top priority accounts
    st.subheader("🎯 Top Priority Accounts (Today)")
    
    # Call account scoring or get from BigQuery
    if st.button("Refresh Account Scores"):
        with st.spinner("Refreshing account scores..."):
            result = call_function("account-scoring", {})
            if "error" not in result:
                st.success(f"Scored {result.get('accounts_scored', 0)} accounts")
            else:
                st.error("Failed to refresh scores")
    
    # Display top accounts (would query BigQuery in production)
    st.info("Account scores are generated daily at 7 AM. Click 'Refresh Account Scores' to generate new scores.")

# Account Scoring Page
elif page == "Account Scoring":
    st.title("🎯 Account Scoring")
    
    st.markdown("""
    Account scores are generated daily using AI analysis of:
    - Recent email engagement
    - Call activity and sentiment
    - Open opportunities
    - Recent activities
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Priority Score Distribution")
        st.info("Chart would show distribution of priority scores")
    
    with col2:
        st.subheader("Budget Likelihood")
        st.info("Chart would show accounts with high budget likelihood")
    
    # Account list
    st.subheader("All Account Scores")
    st.info("Table would show all accounts with their scores, reasoning, and recommended actions")

# Natural Language Query Page
elif page == "Natural Language Query":
    st.title("💬 Natural Language Query")
    
    st.markdown("""
    Ask questions about your sales data in plain English. Examples:
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

# Unmatched Emails Page
elif page == "Unmatched Emails":
    st.title("📧 Unmatched Emails")
    
    st.markdown("""
    Emails from contacts not yet in Salesforce. Create leads from these emails.
    """)
    
    limit = st.slider("Number of emails to show", 10, 100, 20)
    
    if st.button("Load Unmatched Emails"):
        st.info("Would query BigQuery for unmatched emails")
        # In production, query BigQuery directly or via Cloud Function
    
    st.subheader("Create Leads")
    st.markdown("Select emails to create leads from:")
    
    # Example email list (would come from BigQuery)
    sample_emails = [
        {"email": "john@example.com", "subject": "Inquiry about services", "date": "2025-11-20"},
        {"email": "jane@company.com", "subject": "Budget discussion", "date": "2025-11-19"},
    ]
    
    selected_emails = []
    for email_data in sample_emails:
        if st.checkbox(f"{email_data['email']} - {email_data['subject']}", key=email_data['email']):
            selected_emails.append(email_data)
    
    if st.button("Create Leads from Selected"):
        if selected_emails:
            with st.spinner("Creating leads..."):
                result = call_function("create-leads", {
                    "limit": len(selected_emails),
                    "emails": [e["email"] for e in selected_emails]
                })
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"Created {result.get('created', 0)} leads")
        else:
            st.warning("Please select at least one email.")

# Account Details Page
elif page == "Account Details":
    st.title("🏢 Account Details")
    
    account_id = st.text_input("Enter Account ID or Name:")
    
    if account_id:
        st.info("Would display account details, recent emails, calls, opportunities, and activities")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Emails", "Calls", "Opportunities"])
        
        with tab1:
            st.subheader("Account Overview")
            st.info("Account information, scores, and recommended actions")
        
        with tab2:
            st.subheader("Recent Emails")
            st.info("Email thread with this account")
        
        with tab3:
            st.subheader("Call History")
            st.info("Call logs and transcripts")
        
        with tab4:
            st.subheader("Opportunities")
            st.info("Open and closed opportunities")

# Email Threads Page
elif page == "Email Threads":
    st.title("📬 Email Threads")
    
    thread_id = st.text_input("Enter Thread ID or Email Address:")
    
    if thread_id:
        st.info("Would display email thread with AI reply generation")
        
        # Show thread
        st.subheader("Email Thread")
        st.info("Thread messages would be displayed here")
        
        # AI Reply Generation
        st.subheader("🤖 Generate AI Reply")
        
        message_id = st.text_input("Message ID to reply to:")
        
        if st.button("Generate Reply"):
            if message_id:
                with st.spinner("Generating AI reply..."):
                    result = call_function("generate-email-reply", {
                        "thread_id": thread_id,
                        "message_id": message_id,
                        "reply_to_email": thread_id,  # Would extract from thread
                        "send": False
                    })
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    elif "reply_text" in result:
                        st.text_area("Generated Reply:", result["reply_text"], height=200)
                        
                        if st.button("Send Reply"):
                            st.info("Would send via Gmail API (requires OAuth token)")
                    else:
                        st.error("Failed to generate reply")
            else:
                st.warning("Please enter a message ID")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Sales Intelligence System**")
st.sidebar.markdown("Version 2.0 - Phase 2 & 3 Complete")

