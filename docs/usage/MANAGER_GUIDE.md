# Manager's Guide: Visibility & Coaching

Use Sales Intelligence for team performance visibility, coaching opportunities, and strategic insights.

## Daily Check-In (5 minutes)

### Team Priority Overview

1. Open **Dashboard**
2. Review aggregate metrics:
   - Total accounts in pipeline
   - High priority accounts count
   - Unmatched emails (leads waiting)

3. Check **Account Scoring**:
   - Are high-priority accounts being worked?
   - Any accounts dropping in engagement?

### Quick Health Indicators

| Metric | Good | Needs Attention |
|--------|------|-----------------|
| Unmatched emails | < 20 | > 50 |
| High priority accounts contacted | > 80% | < 60% |
| Average engagement score | > 60 | < 40 |

---

## Weekly Team Review (30 minutes)

### 1. Account Coverage Analysis

Use **Natural Language Query**:

```
"Show accounts with priority score above 70 and no activity in 7 days"
```

**What to look for**:
- Hot accounts not being worked
- Reps with too many high-priority accounts
- Accounts needing reassignment

### 2. Engagement Trends

Query examples:
```
"Show average engagement score by account owner"
"Which accounts had the biggest score drop this week?"
"Show accounts with budget likelihood above 80"
```

### 3. Pipeline Quality

```
"Show opportunities with no email activity in 14 days"
"Which accounts have opportunities but low engagement scores?"
```

---

## Coaching Opportunities

### Finding Coaching Moments

1. **Low engagement on hot accounts**
   - Query: "Show high priority accounts with engagement below 50"
   - Review why engagement dropped
   - Discuss outreach strategy

2. **Stalled conversations**
   - Use **Semantic Search**: "no response" or "waiting to hear back"
   - Review email/call history with rep
   - Suggest new approaches

3. **Missed signals**
   - Search: "budget approved" or "ready to move forward"
   - Check if rep followed up appropriately

### Account Review Sessions

For 1:1s, pull up specific accounts:

1. Go to **Account Details**
2. Review together:
   - **Emails**: Quality of communication
   - **Calls**: Discussion points
   - **Scores**: AI assessment

**Coaching questions**:
- "What's your plan for this account?"
- "The AI flagged budget discussions - what's the timeline?"
- "Engagement dropped - what happened?"

---

## Strategic Insights

### Market Signals

Use **Semantic Search** to find patterns:

| Search Query | Strategic Insight |
|--------------|-------------------|
| "competitor mentioned" | Competitive landscape |
| "budget freeze" | Market conditions |
| "looking at alternatives" | At-risk accounts |
| "expanding team" | Growth signals |
| "new initiative" | Buying triggers |

### Account Prioritization

For territory planning:

```
"Show accounts by industry with average engagement score"
"Which segments have highest budget likelihood?"
"Show accounts with engagement above 70 and no opportunity"
```

---

## Performance Metrics

### What the Scores Mean

**Priority Score**:
- Based on recency, frequency, and quality of engagement
- Higher = more sales-ready
- Compare across time, not just absolute values

**Budget Likelihood**:
- Derived from budget-related conversations
- Time-sensitive (reflects current discussions)

**Engagement Score**:
- Measures responsiveness
- Low score = may need different approach

### Tracking Over Time

Weekly tracking questions:
```
"Show count of accounts by priority score range"
"What's the average budget likelihood this week vs last week?"
"How many accounts moved from medium to high priority?"
```

---

## Team Visibility

### Workload Distribution

```
"Show count of high priority accounts by owner"
"Which reps have the most unmatched emails?"
```

### Activity Levels

Review via **Account Details** for specific reps:
- Email frequency
- Call volume
- Response times

---

## Red Flags to Watch

| Signal | Where to Find | Action |
|--------|---------------|--------|
| Hot accounts ignored | NL Query | Reassign or coach |
| Score drops | Account Scoring | Review account |
| Backlog of leads | Unmatched Emails | Process leads |
| Stale opportunities | Account Details | Pipeline review |
| Low engagement trend | Scoring page | Adjust strategy |

---

## Monthly Reviews

### Territory Analysis

```
"Show accounts by region with average scores"
"Which territories have highest budget likelihood?"
"Show account count by industry and priority level"
```

### Forecasting Input

Use scores to inform forecasts:
- High priority + High budget likelihood = Likely to close
- Review AI recommendations for timing insights

---

## Best Practices

1. **Check scores before forecasting** - AI provides unbiased view
2. **Use semantic search for patterns** - Find market signals
3. **Coach with data** - Review accounts together
4. **Track trends** - Single points don't tell the story
5. **Trust but verify** - Scores inform, don't replace judgment

---

## Quick Reference

| Task | Query/Action | Frequency |
|------|--------------|-----------|
| Team health check | Dashboard | Daily |
| Coverage gaps | NL Query for gaps | Weekly |
| Coaching prep | Account Details | Before 1:1s |
| Strategic patterns | Semantic Search | Weekly |
| Performance tracking | Scoring comparisons | Weekly |

---

For technical details, see [Operations Runbook](../operations/RUNBOOK.md).

