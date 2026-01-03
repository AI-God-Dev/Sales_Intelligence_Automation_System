#!/bin/bash
# Check Cloud Functions for common errors and fix IAM permissions
# Usage: ./scripts/check_function_errors.sh [function-name]

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="${SA_EMAIL:-sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check IAM permissions for a function
check_iam_permissions() {
    local func_name=$1
    print_info "Checking IAM permissions for $func_name..."
    
    # Check if service account has invoker role
    local has_permission=$(gcloud functions get-iam-policy "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(bindings[].members)" 2>/dev/null | grep -c "$SERVICE_ACCOUNT" || echo "0")
    
    if [ "$has_permission" -gt 0 ]; then
        print_success "Service account has invoker permission"
        return 0
    else
        print_warning "Service account may not have invoker permission"
        
        # Try to grant permission
        print_info "Attempting to grant invoker permission..."
        if gcloud functions add-iam-policy-binding "$func_name" \
            --gen2 \
            --region="$REGION" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/cloudfunctions.invoker" \
            --project="$PROJECT_ID" 2>/dev/null; then
            print_success "Granted invoker permission to service account"
            return 0
        else
            print_error "Failed to grant invoker permission"
            return 1
        fi
    fi
}

# Check function deployment status
check_function_status() {
    local func_name=$1
    print_info "Checking deployment status for $func_name..."
    
    local state=$(gcloud functions describe "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(state)" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$state" = "ACTIVE" ]; then
        print_success "$func_name is ACTIVE"
        
        # Check memory and timeout
        local memory=$(gcloud functions describe "$func_name" \
            --gen2 \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(serviceConfig.availableMemory)" 2>/dev/null || echo "unknown")
        local timeout=$(gcloud functions describe "$func_name" \
            --gen2 \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(serviceConfig.timeoutSeconds)" 2>/dev/null || echo "unknown")
        
        echo "  Memory: $memory"
        echo "  Timeout: ${timeout}s"
        return 0
    elif [ "$state" = "NOT_FOUND" ]; then
        print_error "$func_name is not deployed"
        return 1
    else
        print_warning "$func_name state is: $state"
        return 1
    fi
}

# Check recent error logs
check_error_logs() {
    local func_name=$1
    print_info "Checking recent error logs for $func_name..."
    
    # Get logs from last 10 minutes
    local logs=$(gcloud logging read \
        "resource.type=cloud_function AND resource.labels.function_name=$func_name AND resource.labels.region=$REGION AND severity>=ERROR AND timestamp>=\"$(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%SZ)\"" \
        --project="$PROJECT_ID" \
        --limit=10 \
        --format="table(timestamp,severity,textPayload,jsonPayload.message)" \
        2>/dev/null || echo "")
    
    if [ -n "$logs" ] && [ "$logs" != "" ]; then
        print_warning "Found recent errors:"
        echo "$logs"
        return 1
    else
        print_success "No recent errors found"
        return 0
    fi
}

# Check function configuration
check_function_config() {
    local func_name=$1
    print_info "Checking function configuration for $func_name..."
    
    # Check environment variables
    local env_vars=$(gcloud functions describe "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.environmentVariables)" 2>/dev/null || echo "")
    
    if [ -n "$env_vars" ]; then
        echo "  Environment variables: $env_vars"
        
        # Check for required env vars
        if echo "$env_vars" | grep -q "GCP_PROJECT_ID"; then
            print_success "GCP_PROJECT_ID is set"
        else
            print_warning "GCP_PROJECT_ID may not be set"
        fi
        
        if echo "$env_vars" | grep -q "BQ_DATASET_NAME"; then
            print_success "BQ_DATASET_NAME is set"
        else
            print_warning "BQ_DATASET_NAME may not be set"
        fi
    else
        print_warning "No environment variables found"
    fi
    
    # Check service account
    local sa=$(gcloud functions describe "$func_name" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.serviceAccountEmail)" 2>/dev/null || echo "")
    
    if [ -n "$sa" ]; then
        echo "  Service account: $sa"
        if [ "$sa" = "$SERVICE_ACCOUNT" ]; then
            print_success "Service account matches expected value"
        else
            print_warning "Service account differs from expected: $SERVICE_ACCOUNT"
        fi
    fi
}

# Main function to check a specific function
check_function() {
    local func_name=$1
    
    print_header "Checking $func_name"
    
    # Check deployment status
    if ! check_function_status "$func_name"; then
        print_error "Cannot proceed - function is not properly deployed"
        return 1
    fi
    
    # Check IAM permissions
    check_iam_permissions "$func_name"
    
    # Check configuration
    check_function_config "$func_name"
    
    # Check error logs
    check_error_logs "$func_name"
    
    echo ""
    return 0
}

# Main execution
main() {
    print_header "Cloud Functions Error Checker"
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service Account: $SERVICE_ACCOUNT"
    
    # Check if specific function provided
    if [ $# -eq 1 ]; then
        check_function "$1"
    else
        # Check all functions
        print_header "Checking All Functions"
        
        local functions=("gmail-sync" "salesforce-sync" "dialpad-sync" "hubspot-sync" "entity-resolution")
        
        for func in "${functions[@]}"; do
            check_function "$func"
            echo ""
        done
    fi
}

# Run main function
main "$@"

