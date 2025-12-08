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
    
    # Invoke function with timeout
    response=$(timeout 600 gcloud functions call "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --data="$payload" 2>&1) || exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ] || [ -z "$exit_code" ]; then
        print_success "$func_name responded in ${duration}s"
        echo "  Response: $response"
        return 0
    elif [ $exit_code -eq 124 ]; then
        print_error "$func_name timed out after 600 seconds"
        return 1
    else
        print_error "$func_name invocation failed (exit code: $exit_code)"
        echo "  Error: $response"
        return 1
    fi
}

# Function to check logs
check_logs() {
    local func_name=$1
    print_info "Checking recent logs for $func_name..."
    
    local logs=$(gcloud functions logs read "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --limit=10 2>/dev/null || echo "")
    
    if [ -n "$logs" ]; then
        echo "$logs" | head -5
        echo ""
        
        # Check for errors
        local errors=$(echo "$logs" | grep -iE "error|failed|exception" || true)
        if [ -n "$errors" ]; then
            print_warning "Found errors in logs:"
            echo "$errors" | head -3
        else
            print_success "No errors in recent logs"
        fi
    else
        print_warning "No logs found (function may not have run yet)"
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