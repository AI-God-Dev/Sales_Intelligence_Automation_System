-- Sales Intelligence System - BigQuery Schema Creation
-- Run this script to create all required tables in BigQuery

-- Dataset should be created separately with appropriate location
-- CREATE SCHEMA IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence`
-- OPTIONS(location="us-central1");

-- 1. Gmail Messages Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.gmail_messages` (
  message_id STRING NOT NULL OPTIONS(description="Gmail message ID (primary key)"),
  thread_id STRING OPTIONS(description="Gmail thread ID for grouping"),
  mailbox_email STRING NOT NULL OPTIONS(description="Which of the 3 mailboxes this came from"),
  from_email STRING OPTIONS(description="Sender email (normalized lowercase)"),
  to_emails ARRAY<STRING> OPTIONS(description="Recipient emails"),
  cc_emails ARRAY<STRING> OPTIONS(description="CC'd emails"),
  subject STRING OPTIONS(description="Email subject"),
  body_text STRING OPTIONS(description="Plain text body"),
  body_html STRING OPTIONS(description="HTML body"),
  sent_at TIMESTAMP OPTIONS(description="When email was sent"),
  labels ARRAY<STRING> OPTIONS(description="Gmail labels"),
  embedding ARRAY<FLOAT64> OPTIONS(description="Vector embedding for semantic search"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
PARTITION BY DATE(sent_at)
CLUSTER BY mailbox_email, from_email
OPTIONS(description="All emails from 3 Gmail mailboxes");

-- 2. Gmail Participants Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.gmail_participants` (
  participant_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  message_id STRING NOT NULL OPTIONS(description="Foreign key to gmail_messages"),
  email_address STRING NOT NULL OPTIONS(description="Normalized email address"),
  role STRING NOT NULL OPTIONS(description="'from', 'to', 'cc', or 'bcc'"),
  sf_contact_id STRING OPTIONS(description="Matched Salesforce Contact ID (NULL if unmatched)"),
  sf_account_id STRING OPTIONS(description="Resolved Account ID"),
  match_confidence STRING OPTIONS(description="'exact', 'fuzzy', or 'manual'")
)
CLUSTER BY email_address, sf_contact_id
OPTIONS(description="Extracted email addresses from messages for entity resolution");

-- 3. Salesforce Accounts Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.sf_accounts` (
  account_id STRING NOT NULL OPTIONS(description="Salesforce Account ID (primary key)"),
  account_name STRING OPTIONS(description="Company name"),
  website STRING OPTIONS(description="Company website"),
  domain STRING OPTIONS(description="Email domain extracted from website"),
  industry STRING OPTIONS(description="Industry category"),
  annual_revenue FLOAT64 OPTIONS(description="Annual revenue"),
  owner_id STRING OPTIONS(description="Salesforce User ID of account owner"),
  created_date TIMESTAMP OPTIONS(description="When created in Salesforce"),
  last_modified_date TIMESTAMP OPTIONS(description="Last modification"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
CLUSTER BY owner_id, account_name
OPTIONS(description="Salesforce Account records");

-- 4. Salesforce Contacts Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.sf_contacts` (
  contact_id STRING NOT NULL OPTIONS(description="Salesforce Contact ID (primary key)"),
  account_id STRING OPTIONS(description="Foreign key to sf_accounts"),
  first_name STRING OPTIONS(description="Contact first name"),
  last_name STRING OPTIONS(description="Contact last name"),
  email STRING OPTIONS(description="Primary email (normalized lowercase)"),
  phone STRING OPTIONS(description="Primary phone (E.164 format)"),
  mobile_phone STRING OPTIONS(description="Mobile phone"),
  title STRING OPTIONS(description="Job title"),
  is_primary BOOLEAN OPTIONS(description="Primary contact for account"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
CLUSTER BY email, account_id
OPTIONS(description="Salesforce Contact records");

-- 5. Salesforce Leads Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.sf_leads` (
  lead_id STRING NOT NULL OPTIONS(description="Salesforce Lead ID (primary key)"),
  first_name STRING OPTIONS(description="Lead first name"),
  last_name STRING OPTIONS(description="Lead last name"),
  email STRING OPTIONS(description="Email address"),
  company STRING OPTIONS(description="Company name"),
  phone STRING OPTIONS(description="Phone number"),
  title STRING OPTIONS(description="Job title"),
  lead_source STRING OPTIONS(description="Source (e.g., 'AI Inbound Email')"),
  status STRING OPTIONS(description="Lead status"),
  owner_id STRING OPTIONS(description="Salesforce User ID"),
  created_by_system BOOLEAN OPTIONS(description="TRUE if created by automation"),
  source_message_id STRING OPTIONS(description="Gmail message that triggered lead creation"),
  created_date TIMESTAMP OPTIONS(description="When created"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
CLUSTER BY email, owner_id
OPTIONS(description="Salesforce Lead records (including system-created leads)");

-- 6. Salesforce Opportunities Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.sf_opportunities` (
  opportunity_id STRING NOT NULL OPTIONS(description="Salesforce Opportunity ID (primary key)"),
  account_id STRING OPTIONS(description="Foreign key to sf_accounts"),
  name STRING OPTIONS(description="Opportunity name"),
  stage STRING OPTIONS(description="Current sales stage"),
  amount FLOAT64 OPTIONS(description="Deal amount"),
  close_date DATE OPTIONS(description="Expected close date"),
  probability FLOAT64 OPTIONS(description="Win probability (0-100)"),
  owner_id STRING OPTIONS(description="Salesforce User ID"),
  is_closed BOOLEAN OPTIONS(description="Whether closed"),
  is_won BOOLEAN OPTIONS(description="Whether won"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
CLUSTER BY account_id, owner_id, stage
OPTIONS(description="Salesforce Opportunity records");

-- 7. Salesforce Activities Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.sf_activities` (
  activity_id STRING NOT NULL OPTIONS(description="Salesforce Activity ID (primary key)"),
  activity_type STRING OPTIONS(description="'Task', 'Event', 'Call', 'Meeting'"),
  what_id STRING OPTIONS(description="Related Account/Opportunity ID"),
  who_id STRING OPTIONS(description="Related Contact/Lead ID"),
  subject STRING OPTIONS(description="Activity subject"),
  description STRING OPTIONS(description="Activity notes"),
  activity_date TIMESTAMP OPTIONS(description="When activity occurred/scheduled"),
  owner_id STRING OPTIONS(description="Salesforce User ID"),
  matched_account_id STRING OPTIONS(description="Resolved Account ID"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
PARTITION BY DATE(activity_date)
CLUSTER BY what_id, who_id, owner_id
OPTIONS(description="Salesforce Tasks, Events, and other activities");

-- 7b. Salesforce Email Messages Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.sf_email_messages` (
  email_message_id STRING NOT NULL OPTIONS(description="Salesforce EmailMessage ID (primary key)"),
  from_address STRING OPTIONS(description="Sender email address (normalized)"),
  to_address STRING OPTIONS(description="Recipient email address (normalized)"),
  cc_address STRING OPTIONS(description="CC email addresses (normalized)"),
  bcc_address STRING OPTIONS(description="BCC email addresses (normalized)"),
  subject STRING OPTIONS(description="Email subject"),
  text_body STRING OPTIONS(description="Plain text body"),
  html_body STRING OPTIONS(description="HTML body"),
  message_date TIMESTAMP OPTIONS(description="When email was sent"),
  related_to_id STRING OPTIONS(description="Related Case/Contact/Lead ID"),
  created_date TIMESTAMP OPTIONS(description="When created in Salesforce"),
  last_modified_date TIMESTAMP OPTIONS(description="Last modification"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
PARTITION BY DATE(message_date)
CLUSTER BY from_address, related_to_id
OPTIONS(description="Salesforce EmailMessage records");

-- 8. Dialpad Calls Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.dialpad_calls` (
  call_id STRING NOT NULL OPTIONS(description="Dialpad call ID (primary key)"),
  direction STRING OPTIONS(description="'inbound' or 'outbound'"),
  from_number STRING OPTIONS(description="Caller phone (E.164)"),
  to_number STRING OPTIONS(description="Recipient phone"),
  duration_seconds INTEGER OPTIONS(description="Call duration"),
  transcript_text STRING OPTIONS(description="Full transcript if available"),
  sentiment_score FLOAT64 OPTIONS(description="Dialpad AI sentiment (-1 to 1)"),
  call_time TIMESTAMP OPTIONS(description="When call occurred"),
  user_id STRING OPTIONS(description="Dialpad user who made/received call"),
  matched_contact_id STRING OPTIONS(description="Matched Salesforce Contact ID"),
  matched_account_id STRING OPTIONS(description="Resolved Account ID"),
  embedding ARRAY<FLOAT64> OPTIONS(description="Vector embedding"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
PARTITION BY DATE(call_time)
CLUSTER BY user_id, matched_account_id
OPTIONS(description="Call logs and transcripts from Dialpad");

-- 8b. Dialpad Transcripts Table (separate table for detailed transcript data)
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.dialpad_transcripts` (
  transcript_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  call_id STRING NOT NULL OPTIONS(description="Foreign key to dialpad_calls"),
  speaker STRING OPTIONS(description="Speaker identifier"),
  text_segment STRING OPTIONS(description="Transcript text segment"),
  start_time_seconds FLOAT64 OPTIONS(description="Start time in call (seconds)"),
  end_time_seconds FLOAT64 OPTIONS(description="End time in call (seconds)"),
  segment_index INTEGER OPTIONS(description="Order of segment in transcript"),
  created_at TIMESTAMP OPTIONS(description="When transcript was created")
)
CLUSTER BY call_id, segment_index
OPTIONS(description="Detailed call transcript segments from Dialpad");

-- 9. Account Recommendations Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.account_recommendations` (
  recommendation_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  account_id STRING NOT NULL OPTIONS(description="Foreign key to sf_accounts"),
  score_date DATE NOT NULL OPTIONS(description="Date score was generated"),
  priority_score INTEGER OPTIONS(description="Overall priority (0-100)"),
  budget_likelihood INTEGER OPTIONS(description="Likelihood discussing 2026 budget (0-100)"),
  engagement_score INTEGER OPTIONS(description="Recent engagement level (0-100)"),
  reasoning STRING OPTIONS(description="LLM explanation of score"),
  recommended_action STRING OPTIONS(description="Suggested next step"),
  key_signals ARRAY<STRING> OPTIONS(description="Detected buying signals"),
  last_interaction_date DATE OPTIONS(description="Most recent email/call/activity"),
  created_at TIMESTAMP OPTIONS(description="When score was computed")
)
PARTITION BY score_date
CLUSTER BY account_id, priority_score
OPTIONS(description="Daily AI-generated account scoring and prioritization");

-- 10. HubSpot Sequences Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.hubspot_sequences` (
  sequence_id STRING NOT NULL OPTIONS(description="HubSpot sequence ID (primary key)"),
  sequence_name STRING OPTIONS(description="Display name"),
  is_active BOOLEAN OPTIONS(description="Whether sequence is active"),
  enrollment_count INTEGER OPTIONS(description="Number of contacts enrolled"),
  last_synced TIMESTAMP OPTIONS(description="Last sync from HubSpot")
)
OPTIONS(description="Available HubSpot sequences for enrollment");

-- 10b. HubSpot Enrollments Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.hubspot_enrollments` (
  enrollment_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  sequence_id STRING NOT NULL OPTIONS(description="Foreign key to hubspot_sequences"),
  contact_email STRING NOT NULL OPTIONS(description="Contact email address enrolled"),
  sf_contact_id STRING OPTIONS(description="Matched Salesforce Contact ID"),
  enrolled_at TIMESTAMP OPTIONS(description="When enrollment occurred"),
  status STRING OPTIONS(description="'active', 'paused', 'completed', 'unsubscribed'"),
  created_at TIMESTAMP OPTIONS(description="When record was created"),
  updated_at TIMESTAMP OPTIONS(description="Last update timestamp")
)
CLUSTER BY sequence_id, contact_email
OPTIONS(description="HubSpot sequence enrollments tracking");

-- 11. ETL Runs Table
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.etl_runs` (
  run_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  source_system STRING NOT NULL OPTIONS(description="'gmail', 'salesforce', 'dialpad', 'hubspot'"),
  job_type STRING OPTIONS(description="'full', 'incremental', 'reconciliation'"),
  started_at TIMESTAMP OPTIONS(description="Job start time"),
  completed_at TIMESTAMP OPTIONS(description="Job completion time"),
  rows_processed INTEGER OPTIONS(description="Number of rows processed"),
  rows_failed INTEGER OPTIONS(description="Number of rows that failed"),
  status STRING OPTIONS(description="'success', 'partial', 'failed'"),
  error_message STRING OPTIONS(description="Error details if failed"),
  watermark TIMESTAMP OPTIONS(description="LastModifiedDate for incremental syncs")
)
PARTITION BY DATE(started_at)
CLUSTER BY source_system, status
OPTIONS(description="Track ETL job execution and data quality");

-- 12. Manual Mappings Table (for entity resolution overrides)
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.manual_mappings` (
  mapping_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  email_address STRING OPTIONS(description="Email to map"),
  phone_number STRING OPTIONS(description="Phone to map"),
  sf_contact_id STRING OPTIONS(description="Mapped Salesforce Contact ID"),
  sf_account_id STRING OPTIONS(description="Mapped Salesforce Account ID"),
  created_by STRING OPTIONS(description="User who created mapping"),
  created_at TIMESTAMP OPTIONS(description="When mapping was created"),
  is_active BOOLEAN OPTIONS(description="Whether mapping is active")
)
CLUSTER BY email_address, phone_number
OPTIONS(description="Manual overrides for entity resolution");

-- 12b. Entity Resolution Emails Table (dedicated table for email matching results)
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.entity_resolution_emails` (
  resolution_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  email_address STRING NOT NULL OPTIONS(description="Normalized email address"),
  sf_contact_id STRING OPTIONS(description="Matched Salesforce Contact ID"),
  sf_account_id STRING OPTIONS(description="Resolved Account ID"),
  match_confidence STRING OPTIONS(description="'exact', 'fuzzy', 'manual', or 'unmatched'"),
  match_method STRING OPTIONS(description="'exact_match', 'domain_match', 'fuzzy_match', 'manual'"),
  confidence_score FLOAT64 OPTIONS(description="Match confidence score (0-1)"),
  resolved_at TIMESTAMP OPTIONS(description="When resolution was performed"),
  last_verified_at TIMESTAMP OPTIONS(description="Last time resolution was verified"),
  is_active BOOLEAN OPTIONS(description="Whether resolution is still active")
)
CLUSTER BY email_address, sf_contact_id
OPTIONS(description="Email entity resolution results and matching history");

-- 12c. Entity Resolution Phones Table (dedicated table for phone matching results)
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.entity_resolution_phones` (
  resolution_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  phone_number STRING NOT NULL OPTIONS(description="Normalized phone number (E.164)"),
  sf_contact_id STRING OPTIONS(description="Matched Salesforce Contact ID"),
  sf_account_id STRING OPTIONS(description="Resolved Account ID"),
  match_confidence STRING OPTIONS(description="'exact', 'fuzzy', 'manual', or 'unmatched'"),
  match_method STRING OPTIONS(description="'exact_match', 'partial_match', 'fuzzy_match', 'manual'"),
  confidence_score FLOAT64 OPTIONS(description="Match confidence score (0-1)"),
  resolved_at TIMESTAMP OPTIONS(description="When resolution was performed"),
  last_verified_at TIMESTAMP OPTIONS(description="Last time resolution was verified"),
  is_active BOOLEAN OPTIONS(description="Whether resolution is still active")
)
CLUSTER BY phone_number, sf_contact_id
OPTIONS(description="Phone entity resolution results and matching history");

-- Create indexes for common queries
-- Note: BigQuery uses clustering instead of indexes, but we can create views for optimization

-- 13. Gmail Sync State Table (for incremental sync tracking)
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.gmail_sync_state` (
  mailbox_email STRING NOT NULL OPTIONS(description="Email address of mailbox"),
  last_history_id STRING OPTIONS(description="Last processed Gmail history ID"),
  last_sync_at TIMESTAMP OPTIONS(description="Last successful sync timestamp"),
  sync_type STRING OPTIONS(description="'full' or 'incremental'"),
  updated_at TIMESTAMP OPTIONS(description="When this record was last updated")
)
CLUSTER BY mailbox_email
OPTIONS(description="Tracks sync state for each Gmail mailbox");

-- 14. Semantic Embeddings Table (optional centralized storage for embeddings)
-- Note: Embeddings are also stored in gmail_messages.embedding and dialpad_calls.embedding
-- This table provides a centralized view and can be used for cross-content semantic search
CREATE TABLE IF NOT EXISTS `maharani-sales-hub-11-2025.sales_intelligence.semantic_embeddings` (
  embedding_id STRING NOT NULL OPTIONS(description="UUID primary key"),
  content_type STRING NOT NULL OPTIONS(description="'email', 'call', 'activity', 'opportunity'"),
  content_id STRING NOT NULL OPTIONS(description="ID of the source content (message_id, call_id, etc.)"),
  text_content STRING OPTIONS(description="Original text that was embedded"),
  embedding ARRAY<FLOAT64> NOT NULL OPTIONS(description="Vector embedding"),
  embedding_model STRING OPTIONS(description="Model used to generate embedding"),
  embedding_dimensions INTEGER OPTIONS(description="Dimensionality of embedding"),
  created_at TIMESTAMP OPTIONS(description="When embedding was generated"),
  updated_at TIMESTAMP OPTIONS(description="Last update timestamp")
)
CLUSTER BY content_type, content_id
OPTIONS(description="Centralized semantic embeddings for all content types");

-- Create indexes for common queries
-- Note: BigQuery uses clustering instead of indexes, but we can create views for optimization

-- View: Unmatched Email Participants
CREATE OR REPLACE VIEW `maharani-sales-hub-11-2025.sales_intelligence.v_unmatched_emails` AS
SELECT 
  p.participant_id,
  p.email_address,
  p.message_id,
  m.subject,
  m.sent_at,
  m.mailbox_email,
  m.from_email
FROM `maharani-sales-hub-11-2025.sales_intelligence.gmail_participants` p
JOIN `maharani-sales-hub-11-2025.sales_intelligence.gmail_messages` m ON p.message_id = m.message_id
WHERE p.sf_contact_id IS NULL
  AND p.role = 'from'
  AND m.sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY m.sent_at DESC;

