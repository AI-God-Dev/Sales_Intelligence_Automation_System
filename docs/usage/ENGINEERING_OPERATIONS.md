# Sales Intelligence Automation System  
## Engineering & Operations Guide

This document explains how engineers and operators should interact with the system **without disrupting production usage**.

---

## System Status
- All ingestion pipelines are deployed
- Web app is deployed on Cloud Run
- BigQuery is the system of record
- Vertex AI is used for intelligence
- Codebase is considered **stable**

---

## Environment Model

### Production
- Dataset: `sales_intelligence`
- Used by sales and managers
- Must remain stable

### Development / Staging
- Dataset: `sales_intelligence_dev`
- Used for testing and validation
- Safe for experimentation

---

## Rules for Engineers

### Allowed
- Query BigQuery (read-only)
- Run the web app locally
- Improve documentation
- Add tests
- Propose enhancements via PR

### Not Allowed
- Deploy to production without approval
- Modify production datasets
- Change IAM roles
- Trigger production ingestion manually

---

## Local Development (Safe Mode)
- Use LOCAL_MODE / MOCK_MODE
- Use `sales_intelligence_dev`
- Never point local runs to production datasets

---

## Deployment Ownership
- Cloud Functions: Admin owned
- Cloud Run: Admin owned
- IAM & billing: Admin owned

Engineers do NOT deploy directly to prod.

---

## Monitoring & Health Checks
Operators should occasionally check:
- Cloud Run service status
- Cloud Function logs
- BigQuery ingestion freshness
- Vertex AI usage

No daily intervention required.

---

## Incident Handling
If something breaks:
1. Identify the impacted layer (Ingestion / AI / Web)
2. Notify admin
3. Roll back or pause if needed
4. Document the issue

Do NOT hot-fix production without review.

---

## When to Change Code
Code changes should happen only if:
- Data is incorrect
- The app becomes unreliable
- A clearly defined new business requirement exists

Avoid changes for “nice to have” ideas.

---

## Engineering Goal
Keep the system:
- Stable
- Predictable
- Trusted by sales

---

**End of Engineering Operations Guide**
