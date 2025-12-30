# Monitoring and Alerting Configuration

# Notification Channel for Alerts
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Alerts"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
  
  project = var.project_id
}

# Alert: High Error Rate for Account Scoring
resource "google_monitoring_alert_policy" "account_scoring_high_error_rate" {
  display_name = "High Error Rate - Account Scoring"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_function\" AND resource.labels.function_name = \"account-scoring\" AND metric.type = \"cloudfunctions.googleapis.com/function/execution_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  project = var.project_id
}

# Alert: Account Scoring Function Timeout
resource "google_monitoring_alert_policy" "account_scoring_timeout" {
  display_name = "Account Scoring Timeout"
  combiner     = "OR"
  
  conditions {
    display_name = "Function execution time > 8 minutes"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_function\" AND resource.labels.function_name = \"account-scoring\" AND metric.type = \"cloudfunctions.googleapis.com/function/execution_times\""
      comparison      = "COMPARISON_GT"
      threshold_value = 480  # 8 minutes in seconds
      duration        = "60s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  project = var.project_id
}

# Alert: BigQuery Query Failures
resource "google_monitoring_alert_policy" "bigquery_query_failures" {
  display_name = "BigQuery Query Failures"
  combiner     = "OR"
  
  conditions {
    display_name = "Query failure rate > 1%"
    
    condition_threshold {
      filter          = "resource.type = \"bigquery_resource\" AND metric.type = \"bigquery.googleapis.com/job/num_failed_jobs\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.01
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  project = var.project_id
}

# Alert: Vertex AI API Errors
resource "google_monitoring_alert_policy" "vertex_ai_errors" {
  display_name = "Vertex AI API Errors"
  combiner     = "OR"
  
  conditions {
    display_name = "API error rate > 2%"
    
    condition_threshold {
      filter          = "resource.type = \"aiplatform.googleapis.com/Endpoint\" AND metric.type = \"aiplatform.googleapis.com/prediction/online_prediction_errors\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.02
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  project = var.project_id
}

# Dashboard for Account Scoring Metrics
resource "google_monitoring_dashboard" "account_scoring_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Account Scoring Dashboard"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Accounts Scored (Last 24h)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"cloud_function\" AND resource.labels.function_name = \"account-scoring\""
                    aggregation = {
                      alignmentPeriod = "3600s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "Error Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"cloud_function\" AND resource.labels.function_name = \"account-scoring\" AND metric.type = \"cloudfunctions.googleapis.com/function/execution_count\""
                    aggregation = {
                      alignmentPeriod = "300s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
  
  project = var.project_id
}

