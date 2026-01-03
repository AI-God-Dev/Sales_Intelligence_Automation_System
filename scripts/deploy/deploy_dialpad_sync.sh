#!/bin/bash
# Deploy Dialpad Sync Function
# Dynamic configuration script for client deployment

set -e

# Default values (can be overridden by environment variables or parameters)
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SOURCE_PATH="${SOURCE_PATH:-.}"
FUNCTION_NAME="${FUNCTION_NAME:-dialpad-sync}"
ENTRY_POINT="${ENTRY_POINT:-dialpad_sync}"
RUNTIME="${RUNTIME:-python311}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --source)
            SOURCE_PATH="$2"
            shift 2
            ;;
        --function-name)
            FUNCTION_NAME="$2"
            shift 2
            ;;
        --entry-point)
            ENTRY_POINT="$2"
            shift 2
            ;;
        --runtime)
            RUNTIME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project-id PROJECT_ID    GCP Project ID"
            echo "  --region REGION           GCP Region (default: us-central1)"
            echo "  --source SOURCE_PATH      Source directory (default: .)"
            echo "  --function-name NAME      Function name (default: dialpad-sync)"
            echo "  --entry-point ENTRY       Entry point function (default: dialpad_sync)"
            echo "  --runtime RUNTIME         Runtime (default: python311)"
            echo ""
            echo "Environment Variables:"
            echo "  GCP_PROJECT_ID           GCP Project ID"
            echo "  GCP_REGION               GCP Region"
            echo "  SOURCE_PATH              Source directory"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display colored output
info() {
    echo -e "${CYAN}$1${NC}"
}

success() {
    echo -e "${GREEN}$1${NC}"
}

error() {
    echo -e "${RED}$1${NC}"
}

warning() {
    echo -e "${YELLOW}$1${NC}"
}

info "=========================================="
info "Deploy Dialpad Sync Cloud Function"
info "=========================================="
echo ""

# Get project ID (prompt if not set)
if [ -z "$PROJECT_ID" ]; then
    read -p "Enter GCP Project ID: " PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        error "ERROR: Project ID is required"
        exit 1
    fi
fi

# Get region (prompt if not set or use default)
if [ -z "$REGION" ]; then
    read -p "Enter GCP Region (default: us-central1): " REGION
    REGION="${REGION:-us-central1}"
fi

# Verify gcloud is installed and authenticated
info "Checking gcloud authentication..."
if ! command -v gcloud &> /dev/null; then
    error "ERROR: gcloud CLI not found"
    info "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
current_project=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$current_project" ] || [ "$current_project" != "$PROJECT_ID" ]; then
    warning "Setting gcloud project to $PROJECT_ID..."
    gcloud config set project "$PROJECT_ID"
fi

# Verify authentication
if ! gcloud auth print-access-token &> /dev/null; then
    error "ERROR: Not authenticated. Please run: gcloud auth login"
    exit 1
fi

# Verify source path exists
if [ ! -d "$SOURCE_PATH" ]; then
    error "ERROR: Source path does not exist: $SOURCE_PATH"
    info "Current directory: $(pwd)"
    info "Please ensure you're in the project root directory or specify --source"
    exit 1
fi

info ""
info "Deployment Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Function: $FUNCTION_NAME"
echo "  Entry Point: $ENTRY_POINT"
echo "  Runtime: $RUNTIME"
echo "  Source Path: $SOURCE_PATH"
echo ""

# Confirm deployment
read -p "Continue with deployment? (Y/n): " confirm
if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
    info "Deployment cancelled."
    exit 0
fi

# Check for existing deployments
info "Checking for existing function..."
if gcloud functions describe "$FUNCTION_NAME" --gen2 --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
    warning "Function already exists. This will update it."
    info "Waiting for any in-progress operations to complete..."
    
    # Wait for operations to complete (max 5 minutes)
    max_wait=300
    wait_time=0
    while [ $wait_time -lt $max_wait ]; do
        operations=$(gcloud functions operations list --region="$REGION" --project="$PROJECT_ID" \
            --filter="metadata.target.name=$FUNCTION_NAME AND done=false" 2>/dev/null || echo "")
        if [ -z "$operations" ]; then
            break
        fi
        echo "  Waiting for operations to complete... ($wait_time/$max_wait seconds)"
        sleep 10
        wait_time=$((wait_time + 10))
    done
fi

# Deploy function
info ""
info "Deploying function... (this may take 5-10 minutes)"
echo ""

if gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --source="$SOURCE_PATH" \
    --entry-point="$ENTRY_POINT" \
    --runtime="$RUNTIME" \
    --trigger-http \
    --allow-unauthenticated; then
    
    success ""
    success "=========================================="
    success "Deployment Successful!"
    success "=========================================="
    
    # Get function URL
    function_url=$(gcloud functions describe "$FUNCTION_NAME" --gen2 --region="$REGION" --project="$PROJECT_ID" \
        --format="value(serviceConfig.uri)" 2>/dev/null || echo "")
    if [ -n "$function_url" ]; then
        info ""
        info "Function URL: $function_url"
    fi
    
    info ""
    info "Test the function with:"
    echo "  gcloud functions call $FUNCTION_NAME --region=$REGION --project=$PROJECT_ID --data='{\"user_id\":\"YOUR_USER_ID\",\"sync_type\":\"full\"}'"
    
else
    error ""
    error "=========================================="
    error "Deployment Failed!"
    error "=========================================="
    exit 1
fi

