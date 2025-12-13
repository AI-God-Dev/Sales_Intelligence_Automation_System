# Sales Intelligence Automation System  
## Team Usage & Operational Guidelines

This document explains **how to use the Sales Intelligence Automation System** as a product, not as a development project.

The system is already deployed, stable, and running in production.  
This guide focuses on **how sales teams, managers, and internal stakeholders should use it** day to day.

---

## 1. What This System Is

The Sales Intelligence Automation System is an **internal sales enablement tool** that:

- Aggregates sales communication data (Gmail, Salesforce, Dialpad, HubSpot)
- Centralizes everything into BigQuery
- Uses AI (Vertex AI) to surface insights and prioritization
- Exposes a simple web application for sales teams via Cloud Run

This is **not a developer tool** and **not a general analytics platform**.  
It is designed to answer one core question:

> **“Who should I focus on today, and what should I do next?”**

---

## 2. System Architecture (High Level)

The system has three layers:

### A. Data & Automation Layer (Background)
- Cloud Functions ingest data automatically
- BigQuery stores the data
- Entity resolution links emails and calls to accounts and contacts

👉 No manual interaction required.

---

### B. Intelligence Layer (Background)
- Vertex AI generates:
  - Semantic embeddings
  - Account insights
  - Priority scoring
- Results are written back to BigQuery

👉 Runs automatically or on schedule.

---

### C. Web Application Layer (User Interface)
- Streamlit app deployed on Cloud Run
- Always running
- Read-only access to data
- Primary interface for sales teams

👉 This is what humans use.

---

## 3. Who Uses the System (Roles)

### 1. Sales Representatives
Primary daily users.

### 2. Sales Managers
Use the system for visibility and coaching.

### 3. Admin / Owner (Anand)
Owns infrastructure and access control.

### 4. Engineers / Analysts
Use the data safely for analysis and improvements (not daily sales work).

---

## 4. Daily Usage for Sales Representatives (Most Important Section)

Sales reps should follow a **simple, repeatable daily habit**.

### Morning Routine (5–10 minutes)

1. Open the **Sales Intelligence Web App**
2. Go to the **Dashboard / Priority View**
3. Review:
   - Top prioritized accounts
   - New inbound or recent activity
4. Click into 1–2 accounts:
   - Read the AI-generated summary
   - Review recommended next action
5. Take action in email, CRM, or sequence enrollment

👉 This replaces manually scanning inboxes and CRM lists.

---

### During the Day (As Needed)

- Use **Semantic Search**:
  - “accounts discussing budget”
  - “accounts mentioning 2026”
  - “accounts showing buying signals”
- Review surfaced conversations and accounts
- Take follow-up actions directly in Salesforce or HubSpot

---

### What Sales Reps Should NOT Do

- Do NOT trigger data ingestion jobs
- Do NOT access BigQuery
- Do NOT modify system settings
- Do NOT worry about how AI works internally

The system is designed to be **simple and action-oriented**.

---

## 5. Usage for Sales Managers

Sales managers use the system for **visibility and coaching**, not daily execution.

### Weekly Manager Workflow

- Open the dashboard
- Sort accounts by:
  - Priority score
  - Recent activity
- Review:
  - Why accounts are marked as high priority
  - Which accounts lack follow-up
- Use insights for:
  - Pipeline reviews
  - Deal coaching
  - Team prioritization discussions

👉 This replaces subjective or gut-based reviews.

---

## 6. Usage for Admin / Owner

The admin role is **not a daily user**.

### Responsibilities

- Manage access to the Cloud Run application
- Own the Google Cloud project and datasets
- Monitor system health occasionally
- Review costs (BigQuery, Vertex AI)

### Typical Admin Checks (Weekly or Less)

- Cloud Run service status
- BigQuery dataset freshness
- Ingestion job success (via logs or `etl_runs` table)

No regular intervention is required.

---

## 7. Usage for Engineers & Analysts

### Engineers

Engineers may:
- Run the web app locally for development
- Use the development dataset (`sales_intelligence_dev`)
- Improve documentation or propose enhancements

Engineers should NOT:
- Deploy to production without approval
- Modify production datasets
- Change IAM permissions

---

### Analysts / RevOps

- Query BigQuery directly
- Build dashboards or reports
- Use the system as a **data source**, not an interface

The system acts as a **centralized sales data warehouse**.

---

## 8. Access & Security Model

- Web app access is controlled via Cloud Run permissions
- Only authorized company users should access it
- The application is read-only
- Backend services use service accounts and IAM (no API keys)

This ensures:
- Security
- Auditability
- Safe team usage

---

## 9. Data Freshness & Trust

Users should understand:

- Data updates automatically
- Some sources update more frequently than others
- The dashboard reflects the most recent successful ingestion

If data appears stale:
- Notify the admin
- Do NOT attempt to fix it manually

---

## 10. What Makes This Tool Successful

This system succeeds when:

- Sales reps use it **daily**
- The dashboard tells them **what to do next**
- Managers use it for **coaching**
- Engineers keep it stable, not overbuilt

This is **not an exploration tool** — it is a **decision-support tool**.

---

## 11. What This Tool Is NOT

- Not a replacement for Salesforce
- Not a generic BI dashboard
- Not a free-form analytics platform
- Not an AI experiment playground

It is a **focused internal sales intelligence product**.

---

## 12. Support & Ownership

- Infrastructure & access: Admin (Anand)
- Day-to-day usage questions: Sales leadership
- Technical improvements: Engineering team

---

## 13. Final Note

If users are ever unsure how to use the system, the guiding question should always be:

> **“Who should I focus on today, and why?”**

If the system answers that clearly, it is doing its job.

---

**End of Document**
