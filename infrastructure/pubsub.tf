# Pub/Sub Topics for Ingestion Pipelines

# Note: Pub/Sub API is enabled in main.tf via google_project_service.required_apis

# Gmail Ingestion Topic
resource "google_pubsub_topic" "gmail_ingestion" {
  name    = "gmail-ingestion"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    source      = "gmail"
  }
  
  message_retention_duration = "604800s" # 7 days
  
  depends_on = [google_project_service.required_apis]
}

# Gmail Ingestion Subscription (for error handling)
resource "google_pubsub_subscription" "gmail_ingestion_errors" {
  name    = "gmail-ingestion-errors"
  topic   = google_pubsub_topic.gmail_ingestion.name
  project = var.project_id
  
  ack_deadline_seconds = 600
  retain_acked_messages = false
  
  expiration_policy {
    ttl = "604800s" # 7 days (must be >= topic message retention duration)
  }
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.gmail_ingestion_dlq.id
    max_delivery_attempts = 5
  }
}

# Gmail Dead Letter Queue
resource "google_pubsub_topic" "gmail_ingestion_dlq" {
  name    = "gmail-ingestion-dlq"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    type        = "dlq"
  }
}

# Salesforce Ingestion Topic
resource "google_pubsub_topic" "salesforce_ingestion" {
  name    = "salesforce-ingestion"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    source      = "salesforce"
  }
  
  message_retention_duration = "604800s" # 7 days
  
  depends_on = [google_project_service.required_apis]
}

# Salesforce Ingestion Subscription (for error handling)
resource "google_pubsub_subscription" "salesforce_ingestion_errors" {
  name    = "salesforce-ingestion-errors"
  topic   = google_pubsub_topic.salesforce_ingestion.name
  project = var.project_id
  
  ack_deadline_seconds = 600
  retain_acked_messages = false
  
  expiration_policy {
    ttl = "300000.5s"
  }
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.salesforce_ingestion_dlq.id
    max_delivery_attempts = 5
  }
}

# Salesforce Dead Letter Queue
resource "google_pubsub_topic" "salesforce_ingestion_dlq" {
  name    = "salesforce-ingestion-dlq"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    type        = "dlq"
  }
}

# Dialpad Ingestion Topic
resource "google_pubsub_topic" "dialpad_ingestion" {
  name    = "dialpad-ingestion"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    source      = "dialpad"
  }
  
  message_retention_duration = "604800s" # 7 days
  
  depends_on = [google_project_service.required_apis]
}

# Dialpad Ingestion Subscription (for error handling)
resource "google_pubsub_subscription" "dialpad_ingestion_errors" {
  name    = "dialpad-ingestion-errors"
  topic   = google_pubsub_topic.dialpad_ingestion.name
  project = var.project_id
  
  ack_deadline_seconds = 600
  retain_acked_messages = false
  
  expiration_policy {
    ttl = "300000.5s"
  }
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dialpad_ingestion_dlq.id
    max_delivery_attempts = 5
  }
}

# Dialpad Dead Letter Queue
resource "google_pubsub_topic" "dialpad_ingestion_dlq" {
  name    = "dialpad-ingestion-dlq"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    type        = "dlq"
  }
}

# HubSpot Ingestion Topic
resource "google_pubsub_topic" "hubspot_ingestion" {
  name    = "hubspot-ingestion"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    source      = "hubspot"
  }
  
  message_retention_duration = "604800s" # 7 days
  
  depends_on = [google_project_service.required_apis]
}

# HubSpot Ingestion Subscription (for error handling)
resource "google_pubsub_subscription" "hubspot_ingestion_errors" {
  name    = "hubspot-ingestion-errors"
  topic   = google_pubsub_topic.hubspot_ingestion.name
  project = var.project_id
  
  ack_deadline_seconds = 600
  retain_acked_messages = false
  
  expiration_policy {
    ttl = "300000.5s"
  }
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.hubspot_ingestion_dlq.id
    max_delivery_attempts = 5
  }
}

# HubSpot Dead Letter Queue
resource "google_pubsub_topic" "hubspot_ingestion_dlq" {
  name    = "hubspot-ingestion-dlq"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    type        = "dlq"
  }
}

# Error Notification Topic (for monitoring failures)
resource "google_pubsub_topic" "ingestion_errors" {
  name    = "ingestion-errors"
  project = var.project_id
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    type        = "monitoring"
  }
  
  message_retention_duration = "2592000s" # 30 days
  
  depends_on = [google_project_service.required_apis]
}

# Grant service account permissions to publish to topics
resource "google_pubsub_topic_iam_member" "gmail_publisher" {
  topic  = google_pubsub_topic.gmail_ingestion.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "salesforce_publisher" {
  topic  = google_pubsub_topic.salesforce_ingestion.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "dialpad_publisher" {
  topic  = google_pubsub_topic.dialpad_ingestion.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "hubspot_publisher" {
  topic  = google_pubsub_topic.hubspot_ingestion.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "error_notification_publisher" {
  topic  = google_pubsub_topic.ingestion_errors.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

# Grant service account permissions to subscribe
resource "google_pubsub_subscription_iam_member" "gmail_subscriber" {
  subscription = google_pubsub_subscription.gmail_ingestion_errors.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription_iam_member" "salesforce_subscriber" {
  subscription = google_pubsub_subscription.salesforce_ingestion_errors.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription_iam_member" "dialpad_subscriber" {
  subscription = google_pubsub_subscription.dialpad_ingestion_errors.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription_iam_member" "hubspot_subscriber" {
  subscription = google_pubsub_subscription.hubspot_ingestion_errors.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
}

