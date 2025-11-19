#!/bin/bash
# Quick script to create BigQuery tables from SQL file
# Run this from project root

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
DATASET_ID="${BIGQUERY_DATASET:-sales_intelligence}"
REGION="${GCP_REGION:-us-central1}"

echo "========================================"
echo "Creating BigQuery Tables"
echo "========================================"
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET_ID"
echo ""

# Step 1: Create dataset if it doesn't exist
echo "Step 1: Creating BigQuery dataset..."
bq mk --dataset --location=US --project_id=$PROJECT_ID $DATASET_ID 2>/dev/null || echo "  Dataset already exists"

# Step 2: Prepare SQL file (replace project_id placeholder)
echo ""
echo "Step 2: Preparing SQL file..."
SQL_FILE="bigquery/schemas/create_tables.sql"
TEMP_SQL="/tmp/create_tables_${PROJECT_ID}.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "ERROR: SQL file not found at $SQL_FILE"
    exit 1
fi

sed "s/{project_id}/$PROJECT_ID/g" "$SQL_FILE" > "$TEMP_SQL"
echo "  ✓ SQL file prepared"

# Step 3: Create tables
echo ""
echo "Step 3: Creating tables from SQL file..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID < "$TEMP_SQL"

if [ $? -eq 0 ]; then
    echo "  ✓ Tables created successfully"
else
    echo "  ✗ Error creating tables"
    rm -f "$TEMP_SQL"
    exit 1
fi

# Step 4: Verify tables
echo ""
echo "Step 4: Verifying tables..."
bq ls --project_id=$PROJECT_ID:$DATASET_ID

# Cleanup
rm -f "$TEMP_SQL"

echo ""
echo "========================================"
echo "✓ BigQuery setup completed!"
echo "========================================"

