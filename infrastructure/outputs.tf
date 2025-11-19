# Output definitions for Terraform

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "dataset_id" {
  description = "BigQuery Dataset ID"
  value       = google_bigquery_dataset.sales_intelligence.dataset_id
}

output "service_account_email" {
  description = "Service account email for Cloud Functions"
  value       = data.google_service_account.existing_sa.email
}

output "function_source_bucket" {
  description = "GCS bucket for function source code"
  value       = google_storage_bucket.function_source.name
}

