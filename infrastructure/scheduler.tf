# Cloud Scheduler Jobs for Data Ingestion Automation

# Note: Cloud Scheduler API is enabled in main.tf via google_project_service.required_apis

# Gmail Incremental Sync Job (runs every hour)
resource "google_cloud_scheduler_job" "gmail_incremental_sync" {
  name             = "gmail-incremental-sync"
  description      = "Incremental Gmail sync - runs every hour"
  schedule         = "0 * * * *" # Every hour
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/gmail-sync"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      sync_type = "incremental"
      # If mailbox_email is not specified, all configured mailboxes will be synced
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 3
    max_retry_duration = "600s"
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

# Gmail Full Sync Job (runs daily at 2 AM)
resource "google_cloud_scheduler_job" "gmail_full_sync" {
  name             = "gmail-full-sync"
  description      = "Full Gmail sync - runs daily at 2 AM"
  schedule         = "0 2 * * *" # Daily at 2 AM
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/gmail-sync"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      sync_type = "full"
      # If mailbox_email is not specified, all configured mailboxes will be synced
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 2
    max_retry_duration = "1800s"
    min_backoff_duration = "10s"
    max_backoff_duration = "3600s"
    max_doublings = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

# Salesforce Incremental Sync Job (runs every 6 hours)
resource "google_cloud_scheduler_job" "salesforce_incremental_sync" {
  name             = "salesforce-incremental-sync"
  description      = "Incremental Salesforce sync - runs every 6 hours"
  schedule         = "0 */6 * * *" # Every 6 hours
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/salesforce-sync"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      sync_type = "incremental"
      object_type = "Account" # Will sync all objects in sequence
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 3
    max_retry_duration = "600s"
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

# Salesforce Full Sync Job (runs weekly on Sunday at 3 AM)
resource "google_cloud_scheduler_job" "salesforce_full_sync" {
  name             = "salesforce-full-sync"
  description      = "Full Salesforce sync - runs weekly on Sunday at 3 AM"
  schedule         = "0 3 * * 0" # Weekly on Sunday at 3 AM
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/salesforce-sync"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      sync_type = "full"
      object_type = "Account"
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 2
    max_retry_duration = "1800s"
    min_backoff_duration = "10s"
    max_backoff_duration = "3600s"
    max_doublings = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

# Dialpad Sync Job (runs daily at 1 AM)
resource "google_cloud_scheduler_job" "dialpad_sync" {
  name             = "dialpad-sync"
  description      = "Dialpad call logs and transcripts sync - runs daily at 1 AM"
  schedule         = "0 1 * * *" # Daily at 1 AM
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/dialpad-sync"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      sync_type = "incremental"
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 3
    max_retry_duration = "600s"
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

# HubSpot Sync Job (runs daily at 4 AM)
resource "google_cloud_scheduler_job" "hubspot_sync" {
  name             = "hubspot-sync"
  description      = "HubSpot sequences metadata sync - runs daily at 4 AM"
  schedule         = "0 4 * * *" # Daily at 4 AM
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/hubspot-sync"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      sync_type = "incremental"
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 3
    max_retry_duration = "600s"
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

# Entity Resolution Job (runs every 4 hours)
resource "google_cloud_scheduler_job" "entity_resolution" {
  name             = "entity-resolution"
  description      = "Entity resolution batch processing - runs every 4 hours"
  schedule         = "0 */4 * * *" # Every 4 hours
  time_zone        = "America/New_York"
  region           = var.region
  project          = var.project_id
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/entity-resolution"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      batch_size = 1000
    }))
    
    oidc_token {
      service_account_email = data.google_service_account.existing_sa.email
    }
  }
  
  retry_config {
    retry_count = 2
    max_retry_duration = "300s"
    min_backoff_duration = "5s"
    max_backoff_duration = "600s"
    max_doublings = 3
  }
  
  depends_on = [google_project_service.required_apis]
}

