# Terraform configuration for Sales Intelligence System
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "sales-intelligence-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "dataset_id" {
  description = "BigQuery Dataset ID"
  type        = string
  default     = "sales_intelligence"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
}

# BigQuery Dataset
resource "google_bigquery_dataset" "sales_intelligence" {
  dataset_id    = var.dataset_id
  friendly_name = "Sales Intelligence Dataset"
  description   = "Data warehouse for sales intelligence and automation system"
  location      = var.region

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  # Access controls
  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "WRITER"
    special_group = "projectWriters"
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }
}

# Service Account for Cloud Functions
resource "google_service_account" "cloud_functions" {
  account_id   = "sales-intelligence-functions"
  display_name = "Sales Intelligence Cloud Functions Service Account"
  description  = "Service account for Cloud Functions execution"
}

# IAM roles for service account
resource "google_project_iam_member" "bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.cloud_functions.email}"
}

resource "google_project_iam_member" "secret_manager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_functions.email}"
}

resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_functions.email}"
}

resource "google_project_iam_member" "monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloud_functions.email}"
}

# Cloud Storage bucket for function source code
resource "google_storage_bucket" "function_source" {
  name          = "${var.project_id}-function-source"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Outputs
output "project_id" {
  value = var.project_id
}

output "dataset_id" {
  value = google_bigquery_dataset.sales_intelligence.dataset_id
}

output "service_account_email" {
  value = google_service_account.cloud_functions.email
}

output "function_source_bucket" {
  value = google_storage_bucket.function_source.name
}

