# Web App Testing Checklist

## Status: Testing in Progress

### Authentication & Setup
- [x] BigQuery client initialization
- [x] Cloud Function URL retrieval
- [x] Identity token authentication for Cloud Run services
- [x] Permission granted for account-scoring function

### Deployed Functions
- [x] `account-scoring` - ACTIVE (permission granted by Anand)
- [x] `dialpad-sync` - ACTIVE
- [x] `entity-resolution` - ACTIVE
- [x] `gmail-sync` - ACTIVE
- [x] `hubspot-sync` - ACTIVE
- [x] `salesforce-sync` - ACTIVE
- [ ] `generate-embeddings` - Needs deployment
- [ ] `nlp-query` - Needs deployment
- [ ] `semantic-search` - Needs deployment
- [ ] `create-leads` - Needs deployment
- [ ] `enroll-hubspot` - Needs deployment
- [ ] `get-hubspot-sequences` - Needs deployment
- [ ] `generate-email-reply` - Needs deployment

### Features to Test

#### 1. Dashboard Page
- [ ] Load dashboard metrics (Total Accounts, High Priority, Unmatched Emails, Open Opportunities)
- [ ] Display top priority accounts table
- [ ] "Refresh Account Scores" button functionality
- [ ] Error handling for missing data

#### 2. Account Scoring Page
- [ ] Display account scores from BigQuery
- [ ] Priority Score Distribution chart
- [ ] Budget Likelihood chart
- [ ] All Account Scores table
- [ ] "Refresh Account Scores" button (calls account-scoring function)
- [ ] Verify scores are generated and stored in BigQuery

#### 3. Natural Language Query Page
- [ ] Enter natural language query
- [ ] Execute query (calls nlp-query function)
- [ ] Display generated SQL
- [ ] Display query results
- [ ] Error handling for invalid queries

#### 4. Semantic Search Page
- [ ] Search by accounts
- [ ] Search by emails
- [ ] Search by calls
- [ ] Display search results
- [ ] Error handling

#### 5. Unmatched Emails Page
- [ ] Load unmatched emails from BigQuery
- [ ] Display email list with details
- [ ] Create leads functionality (calls create-leads function)
- [ ] Error handling

#### 6. Account Details Page
- [ ] Search account by ID or name
- [ ] Display account information
- [ ] Display latest account score
- [ ] Display associated emails
- [ ] Display associated calls
- [ ] Display opportunities
- [ ] Display score history

#### 7. Email Threads Page
- [ ] Load email threads from BigQuery
- [ ] Display thread list
- [ ] Search/filter threads
- [ ] Generate email reply (calls generate-email-reply function)
- [ ] Error handling

### Testing Notes

#### Current Status
- ✅ Authentication code updated to use identity tokens for Cloud Run
- ✅ account-scoring function has run.invoker permission granted (by Anand)
- ✅ Web app is running on http://localhost:8501
- ✅ All ingestion functions are deployed and active (dialpad-sync, entity-resolution, gmail-sync, hubspot-sync, salesforce-sync)
- ✅ Ready to test account-scoring feature with real data

#### Next Steps
1. Test "Refresh Account Scores" button - should now work with permission granted
2. Verify account scores are generated and stored in BigQuery
3. Deploy remaining Phase 2 functions as needed
4. Test each feature with real data from BigQuery
5. Fix any issues found during testing

#### Known Issues
- None currently - ready for testing

#### Deployment Commands (Reference)
```bash
gcloud functions deploy FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=FUNCTION_ENTRY \
  --trigger-http \
  --no-allow-unauthenticated \
  --timeout=540s \
  --memory=512MB \
  --max-instances=1 \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --project=maharani-sales-hub-11-2025
```

#### Permission Granting (Anand)
After deploying each function, Anand needs to grant run.invoker permission:
```bash
gcloud run services add-iam-policy-binding FUNCTION_NAME \
  --region=us-central1 \
  --member='user:atajanbaratov360@gmail.com' \
  --role='roles/run.invoker' \
  --project=maharani-sales-hub-11-2025
```

