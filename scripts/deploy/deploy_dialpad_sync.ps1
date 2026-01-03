# Deploy Dialpad Sync Function
# Dynamic configuration script for client deployment

param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = $env:GCP_REGION,
    [string]$SourcePath = ".",
    [string]$FunctionName = "dialpad-sync",
    [string]$EntryPoint = "dialpad_sync",
    [string]$Runtime = "python311"
)

# Error handling
$ErrorActionPreference = "Stop"

# Function to display colored output
function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

Write-Info "=========================================="
Write-Info "Deploy Dialpad Sync Cloud Function"
Write-Info "=========================================="
Write-Host ""

# Get project ID (prompt if not set)
if (-not $ProjectId) {
    $ProjectId = Read-Host "Enter GCP Project ID"
    if (-not $ProjectId) {
        Write-Error "ERROR: Project ID is required"
        exit 1
    }
}

# Get region (prompt if not set)
if (-not $Region) {
    $Region = Read-Host "Enter GCP Region (default: us-central1)"
    if (-not $Region) {
        $Region = "us-central1"
    }
}

# Verify gcloud is authenticated
Write-Info "Checking gcloud authentication..."
try {
    $currentProject = gcloud config get-value project 2>$null
    if (-not $currentProject) {
        Write-Warning "No gcloud project set. Setting to $ProjectId..."
        gcloud config set project $ProjectId
    } elseif ($currentProject -ne $ProjectId) {
        Write-Warning "Current project is $currentProject. Switching to $ProjectId..."
        gcloud config set project $ProjectId
    }
    
    # Verify authentication
    gcloud auth print-access-token | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "ERROR: Not authenticated. Please run: gcloud auth login"
        exit 1
    }
} catch {
    Write-Error "ERROR: gcloud not found or not authenticated"
    Write-Info "Please install gcloud CLI and run: gcloud auth login"
    exit 1
}

# Verify source path exists
if (-not (Test-Path $SourcePath)) {
    Write-Error "ERROR: Source path does not exist: $SourcePath"
    Write-Info "Current directory: $(Get-Location)"
    Write-Info "Please ensure you're in the project root directory or specify --SourcePath"
    exit 1
}

Write-Info ""
Write-Info "Deployment Configuration:"
Write-Host "  Project ID: $ProjectId" -ForegroundColor White
Write-Host "  Region: $Region" -ForegroundColor White
Write-Host "  Function: $FunctionName" -ForegroundColor White
Write-Host "  Entry Point: $EntryPoint" -ForegroundColor White
Write-Host "  Runtime: $Runtime" -ForegroundColor White
Write-Host "  Source Path: $SourcePath" -ForegroundColor White
Write-Host ""

# Confirm deployment
$confirm = Read-Host "Continue with deployment? (Y/n)"
if ($confirm -eq "n" -or $confirm -eq "N") {
    Write-Info "Deployment cancelled."
    exit 0
}

# Check for existing deployments
Write-Info "Checking for existing function..."
$existingFunction = gcloud functions describe $FunctionName --gen2 --region=$Region --project=$ProjectId 2>$null
if ($existingFunction) {
    Write-Warning "Function already exists. This will update it."
    Write-Info "Waiting for any in-progress operations to complete..."
    
    # Wait for operations to complete
    $maxWait = 300 # 5 minutes
    $waitTime = 0
    while ($waitTime -lt $maxWait) {
        $operations = gcloud functions operations list --region=$Region --project=$ProjectId --filter="metadata.target.name=$FunctionName AND done=false" 2>$null
        if (-not $operations) {
            break
        }
        Write-Host "  Waiting for operations to complete... ($waitTime/$maxWait seconds)" -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        $waitTime += 10
    }
}

# Deploy function
Write-Info ""
Write-Info "Deploying function... (this may take 5-10 minutes)"
Write-Host ""

try {
    $deployCmd = @(
        "gcloud", "functions", "deploy", $FunctionName,
        "--gen2",
        "--region=$Region",
        "--project=$ProjectId",
        "--source=$SourcePath",
        "--entry-point=$EntryPoint",
        "--runtime=$Runtime",
        "--trigger-http",
        "--allow-unauthenticated"
    )
    
    & $deployCmd[0] $deployCmd[1..($deployCmd.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success ""
        Write-Success "=========================================="
        Write-Success "Deployment Successful!"
        Write-Success "=========================================="
        
        # Get function URL
        $functionUrl = gcloud functions describe $FunctionName --gen2 --region=$Region --project=$ProjectId --format="value(serviceConfig.uri)" 2>$null
        if ($functionUrl) {
            Write-Info ""
            Write-Info "Function URL: $functionUrl"
        }
        
        Write-Info ""
        Write-Info "Test the function with:"
        Write-Host "  gcloud functions call $FunctionName --region=$Region --project=$ProjectId --data='{\"user_id\":\"YOUR_USER_ID\",\"sync_type\":\"full\"}'" -ForegroundColor White
        
    } else {
        Write-Error ""
        Write-Error "=========================================="
        Write-Error "Deployment Failed!"
        Write-Error "=========================================="
        Write-Error "Exit code: $LASTEXITCODE"
        exit 1
    }
    
} catch {
    Write-Error ""
    Write-Error "=========================================="
    Write-Error "Deployment Error!"
    Write-Error "=========================================="
    Write-Error $_.Exception.Message
    exit 1
}

