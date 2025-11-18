$projectId = "maharani-sales-hub-11-2025"
$saEmail = "sales-intel-poc-sa@$projectId.iam.gserviceaccount.com"

$secrets = @(
    "salesforce-client-id",
    "salesforce-client-secret",
    "salesforce-username",
    "salesforce-password",
    "salesforce-security-token",
    "salesforce-refresh-token",
    "dialpad-api-key",
    "hubspot-api-key",
    "gmail-oauth-client-id",
    "gmail-oauth-client-secret"
)

Write-Host "Creating and initializing secrets in project $projectId"
foreach ($secret in $secrets) {
    $exists = gcloud secrets describe $secret --project $projectId 2>$null
    if (-not $?) {
        Write-Host "Creating secret: $secret"
        "PLACEHOLDER" | Out-String | gcloud secrets create $secret `
            --replication-policy=automatic `
            --project $projectId `
            --data-file=-
    } else {
        Write-Host "Secret $secret already exists."
    }

    Write-Host "Granting $saEmail access to $secret"
    gcloud secrets add-iam-policy-binding $secret `
        --member="serviceAccount:$saEmail" `
        --role="roles/secretmanager.secretAccessor" `
        --project $projectId | Out-Null

    $value = Read-Host "Enter value for $secret (leave empty to skip updating)"
    if ($value) {
        $tempFile = New-TemporaryFile
        $value | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
        gcloud secrets versions add $secret --data-file=$tempFile --project $projectId
        Remove-Item $tempFile
        Write-Host "$secret updated."
    } else {
        Write-Host "Skipped updating $secret."
    }
}

Write-Host "`nAll secrets created and permissions granted!"

