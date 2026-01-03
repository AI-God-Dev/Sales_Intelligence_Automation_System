#!/bin/bash
# Test and verify Cloud Functions after deployment
# Usage: ./scripts/test_functions.sh [function-name]
#   If no function name provided, tests all functions

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-${BIGQUERY_DATASET:-sales_intelligence}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check deployment status
check_deployment() {
    local func_name=$1
    print_info "Checking deployment status for $func_name..."
    
    if gcloud functions describe "$func_name" --gen2 --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        local memory=$(gcloud functions describe "$func_name" --gen2 --region="$REGION" --project="$PROJECT_ID" \
            --format="value(serviceConfig.availableMemory)" 2>/dev/null || echo "unknown")
        local timeout=$(gcloud functions describe "$func_name" --gen2 --region="$REGION" --project="$PROJECT_ID" \
            --format="value(serviceConfig.timeoutSeconds)" 2>/dev/null || echo "unknown")
        local state=$(gcloud functions describe "$func_name" --gen2 --region="$REGION" --project="$PROJECT_ID" \
            --format="value(state)" 2>/dev/null || echo "unknown")
        
        echo "  Status: $state"
        echo "  Memory: $memory"
        echo "  Timeout: ${timeout}s"
        
        if [ "$state" = "ACTIVE" ]; then
            print_success "$func_name is deployed and active"
            return 0
        else
            print_warning "$func_name state is: $state"
            return 1
        fi
    else
        print_error "$func_name is not deployed"
        return 1
    fi
}

# Function to invoke a Cloud Function
invoke_function() {
    local func_name=$1
    local payload=$2
    
    print_info "Invoking $func_name..."
    echo "  Payload: $payload"
    
    local start_time=$(date +%s)
    local response
    local exit_code=0
    
    # Check if function requires authentication
    local auth_required=$(gcloud functions describe "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.invokerConfig.allowedIngress)" 2>/dev/null || echo "ALL_TRAFFIC")
    
    # Invoke function
    # Note: gcloud functions call doesn't support --async or --timeout flags
    # The function timeout is configured during deployment, not during invocation
    # For long-running functions, we use the timeout command to limit how long we wait
    if [ "$func_name" = "gmail-sync" ]; then
        print_info "Invoking gmail-sync (this may take several minutes)..."
        # Use timeout command to limit wait time (600 seconds = 10 minutes)
        # The function itself has a 540s timeout configured during deployment
        response=$(timeout 600 gcloud functions call "$func_name" \
            --gen2 \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --data="$payload" 2>&1) || exit_code=$?
        
        # Check if timeout command killed the process
        if [ $exit_code -eq 124 ]; then
            print_error "Invocation timed out after 600 seconds (function may still be running)"
            return 1
        fi
    else
        # For other functions, use regular invocation with timeout wrapper
        # Use timeout command to limit wait time (600 seconds = 10 minutes)
        response=$(timeout 600 gcloud functions call "$func_name" \
            --gen2 \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --data="$payload" 2>&1) || exit_code=$?
        
        # Check if timeout command killed the process
        if [ $exit_code -eq 124 ]; then
            print_error "Invocation timed out after 600 seconds (function may still be running)"
            return 1
        fi
    fi
    
    # Check for specific error patterns
    if echo "$response" | grep -qi "403\|Forbidden"; then
        print_error "Authentication failed (403 Forbidden). Check IAM permissions."
        echo "  Error: $response"
        return 1
    elif echo "$response" | grep -qi "500\|Internal Server Error"; then
        print_error "Function returned 500 Internal Server Error"
        echo "  Error: $response"
        return 1
    elif echo "$response" | grep -qi "ReadTimeout\|read timeout"; then
        print_error "Function timed out (read timeout)"
        echo "  Error: $response"
        return 1
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        print_success "$func_name responded in ${duration}s"
        if [ -n "$response" ]; then
            echo "  Response: $response" | head -20
        fi
        return 0
    elif [ $exit_code -eq 124 ]; then
        print_error "$func_name timed out after 600 seconds"
        return 1
    else
        print_error "$func_name invocation failed (exit code: $exit_code)"
        if [ -n "$response" ]; then
            echo "  Error: $response" | head -30
        fi
        return 1
    fi
}

# Function to check logs
check_logs() {
    local func_name=$1
    local show_errors_only=${2:-false}
    
    if [ "$show_errors_only" = "true" ]; then
        print_info "Checking recent error logs for $func_name..."
    else
        print_info "Checking recent logs for $func_name..."
    fi
    
    # Wait a moment for logs to appear
    sleep 2
    
    local logs=$(gcloud logging read \
        "resource.type=cloud_function AND resource.labels.function_name=$func_name AND resource.labels.region=$REGION" \
        --project="$PROJECT_ID" \
        --limit=20 \
        --format="table(timestamp,severity,textPayload,jsonPayload.message)" \
        2>/dev/null || echo "")
    
    # Fallback to functions logs read if logging read fails
    if [ -z "$logs" ] || [ "$logs" = "" ]; then
        logs=$(gcloud functions logs read "$func_name" \
            --gen2 \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --limit=20 2>/dev/null || echo "")
    fi
    
    if [ -n "$logs" ] && [ "$logs" != "" ]; then
        if [ "$show_errors_only" = "true" ]; then
            # Show only errors
            local error_logs=$(echo "$logs" | grep -iE "ERROR|CRITICAL|Exception|Traceback|Failed|error" || true)
            if [ -n "$error_logs" ]; then
                echo "$error_logs" | head -15
            else
                print_warning "No error logs found (function may have failed before logging)"
            fi
        else
            echo "$logs" | head -10
            echo ""
            
            # Check for errors
            local errors=$(echo "$logs" | grep -iE "ERROR|CRITICAL|Exception|Traceback|Failed|error" || true)
            if [ -n "$errors" ]; then
                print_warning "Found errors in logs:"
                echo "$errors" | head -5
            else
                print_success "No errors in recent logs"
            fi
        fi
    else
        print_warning "No logs found (function may not have run yet or logs are delayed)"
    fi
}

# Function to check BigQuery data
check_bigquery() {
    local source_system=$1
    print_info "Checking BigQuery data for $source_system..."
    
    # Check ETL runs
    local etl_query="SELECT run_id, status, rows_processed, rows_failed, started_at, completed_at
                     FROM \`$PROJECT_ID.$DATASET_NAME.etl_runs\`
                     WHERE source_system = '$source_system'
                     ORDER BY started_at DESC
                     LIMIT 1"
    
    local etl_result=$(bq query --use_legacy_sql=false --format=json "$etl_query" 2>/dev/null || echo "[]")
    
    if [ "$etl_result" != "[]" ] && [ -n "$etl_result" ]; then
        print_success "ETL run found in BigQuery"
        echo "$etl_result" | python3 -m json.tool 2>/dev/null || echo "$etl_result"
    else
        print_warning "No ETL runs found for $source_system"
    fi
}

# Test specific function
test_function() {
    local func_name=$1
    
    print_header "Testing $func_name"
    
    # Check deployment
    if ! check_deployment "$func_name"; then
        print_error "Cannot test $func_name - deployment check failed"
        return 1
    fi
    
    # Determine payload based on function
    local payload="{}"
    case "$func_name" in
        "gmail-sync")
            payload='{"sync_type":"incremental"}'
            ;;
        "salesforce-sync")
            payload='{"sync_type":"incremental"}'
            ;;
        "dialpad-sync")
            payload='{"sync_type":"incremental"}'
            ;;
        "hubspot-sync")
            payload='{}'
            ;;
        "entity-resolution")
            payload='{}'
            ;;
    esac
    
    # Invoke function
    if invoke_function "$func_name" "$payload"; then
        # Wait a moment for logs to appear
        sleep 3
        
        # Check logs
        check_logs "$func_name"
        
        # Check BigQuery (for sync functions)
        case "$func_name" in
            "gmail-sync")
                check_bigquery "gmail"
                ;;
            "salesforce-sync")
                check_bigquery "salesforce"
                ;;
            "dialpad-sync")
                check_bigquery "dialpad"
                ;;
            "hubspot-sync")
                check_bigquery "hubspot"
                ;;
            "entity-resolution")
                check_bigquery "entity_resolution"
                ;;
        esac
        
        print_success "$func_name test completed"
        return 0
    else
        print_error "$func_name test failed"
        
        # Immediately check error logs for debugging
        echo ""
        print_info "Checking error logs for debugging..."
        check_logs "$func_name" "true"
        
        # Provide troubleshooting tips
        echo ""
        print_warning "Troubleshooting tips:"
        echo "  1. Check IAM permissions: gcloud functions get-iam-policy $func_name --region=$REGION --project=$PROJECT_ID"
        echo "  2. View detailed logs: gcloud functions logs read $func_name --gen2 --region=$REGION --project=$PROJECT_ID --limit=50"
        echo "  3. Check function status: gcloud functions describe $func_name --gen2 --region=$REGION --project=$PROJECT_ID"
        
        return 1
    fi
}

# Main execution
main() {
    print_header "Cloud Functions Test Script"
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Dataset: $DATASET_NAME"
    
    # Check if specific function provided
    if [ $# -eq 1 ]; then
        test_function "$1"
    else
        # Test all functions
        print_header "Testing All Functions"
        
        local functions=("gmail-sync" "salesforce-sync" "dialpad-sync" "hubspot-sync" "entity-resolution")
        local results=()
        
        for func in "${functions[@]}"; do
            if test_function "$func"; then
                results+=("$func: SUCCESS")
            else
                results+=("$func: FAILED")
            fi
            echo ""
        done
        
        # Summary
        print_header "Test Summary"
        for result in "${results[@]}"; do
            if [[ "$result" == *"SUCCESS"* ]]; then
                print_success "$result"
            else
                print_error "$result"
            fi
        done
    fi
}

# Run main function
main "$@"