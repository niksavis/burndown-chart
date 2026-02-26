# DORA & Flow Metrics Correlation Guide

**Audience**: Users validating metric configurations and understanding metric relationships
**Part of**: [Metrics Documentation Index](./metrics_index.md)

This guide explains the relationships between DORA and Flow metrics, helping you verify that your field mappings are correct and your metrics are reliable.

---

## Table of Contents

1. [Overview](#overview)
2. [DORA Metrics Summary](#dora-metrics-summary)
3. [Flow Metrics Summary](#flow-metrics-summary)
4. [Metric Relationships & Expected Correlations](#metric-relationships--expected-correlations)
5. [Validation Rules](#validation-rules)
6. [Timeline Diagrams](#timeline-diagrams)
7. [Common Configuration Issues](#common-configuration-issues)
8. [Little's Law & Flow Metrics](#littles-law--flow-metrics)

---

## Overview

### Key Insight from DORA Research

> **"Speed and stability are NOT tradeoffs. Top performers do well across all four metrics, and low performers do poorly across all four."**
> — DORA Research (Google Cloud)

This means correctly configured metrics should show **positive correlations** for high-performing teams. If your metrics show contradictory patterns, it may indicate a configuration issue.

### Why Correlations Matter

- **Validation**: Unexpected relationships may indicate incorrect field mappings
- **Insights**: Understanding correlations helps identify bottlenecks
- **Reliability**: Consistent metrics build trust in data-driven decisions

---

## DORA Metrics Summary

| Metric                    | Formula                                      | Unit             | Better When |
| ------------------------- | -------------------------------------------- | ---------------- | ----------- |
| **Deployment Frequency**  | Deployments ÷ Time Period                    | deployments/week | Higher      |
| **Lead Time for Changes** | Deployment Date − Work Start Date            | days             | Lower       |
| **Change Failure Rate**   | Failed Deployments ÷ Total Deployments × 100 | %                | Lower       |
| **Mean Time to Recovery** | Incident Resolved − Incident Detected        | hours/days       | Lower       |

### DORA Performance Tiers

| Tier       | Deployment Freq | Lead Time      | CFR    | MTTR     |
| ---------- | --------------- | -------------- | ------ | -------- |
| **Elite**  | Multiple/day    | <1 day         | 0-15%  | <1 hour  |
| **High**   | Daily-Weekly    | 1-7 days       | 16-30% | <1 day   |
| **Medium** | Weekly-Monthly  | 1 week-1 month | 31-45% | 1-7 days |
| **Low**    | <Monthly        | >1 month       | >45%   | >1 week  |

---

## Flow Metrics Summary

| Metric                | Formula                                       | Unit       | Better When      |
| --------------------- | --------------------------------------------- | ---------- | ---------------- |
| **Flow Velocity**     | Completed Items ÷ Time Period                 | items/week | Higher           |
| **Flow Time**         | Completion Date − Start Date (from changelog) | days       | Lower            |
| **Flow Efficiency**   | Active Time ÷ Total WIP Time × 100            | %          | Higher           |
| **Flow Load (WIP)**   | Count of items in WIP statuses                | items      | Lower (balanced) |
| **Flow Distribution** | Items by Type ÷ Total Items × 100             | %          | Balanced         |

### Flow Distribution Targets (Flow Framework)

| Work Type          | Target Range | Meaning                              |
| ------------------ | ------------ | ------------------------------------ |
| **Feature**        | 40-70%       | Product value delivery               |
| **Defect**         | <10%         | Quality issues (should be low)       |
| **Technical Debt** | 10-20%       | Sustainability investment            |
| **Risk**           | 10-20%       | Security, compliance, risk reduction |

---

## Metric Relationships & Expected Correlations

### 1. Lead Time ≥ Flow Time

**Rule**: Lead Time should always be **greater than or equal to** Flow Time for the same work items.

**Why**:

- **Flow Time** ends when work status changes to "Done"
- **Lead Time** ends when the fix is actually **deployed to production**
- There's always some wait time between "Done" and "Deployed"

```
Flow Time:     [In Progress] ─────────────────► [Done]
Lead Time:     [In Progress] ─────────────────► [Done] ───► [Deployed]
                                                            ↑
                                                  Deployment wait time
```

**⚠️ Warning**: If Lead Time < Flow Time, check:

- `code_commit_date` field mapping (should be work start, e.g., `status:In Progress.DateTime`)
- `deployment_date` field mapping (should be `fixVersions`)
- Whether changelog is being fetched correctly

---

### 2. MTTR ≥ Lead Time (for bugs)

**Rule**: MTTR should typically be **greater than or equal to** Lead Time for bug fixes.

**Why**:

- **MTTR** starts when bug is **created** (before any work begins)
- **Lead Time** starts when work **actually begins** (In Progress)
- MTTR includes triage, prioritization, and assignment time

```
MTTR:          [Created] ──► [Triaged] ──► [In Progress] ──► [Deployed]
               ↑                           ↑                  ↑
               MTTR starts                 Lead Time starts   Both end
```

**Exception**: If bugs are immediately worked on (no triage delay), MTTR ≈ Lead Time.

**⚠️ Warning**: If MTTR << Lead Time consistently:

- Check `incident_detected_at` is set to `created`
- Verify `incident_resolved_at` uses the same endpoint as Lead Time

---

### 3. Deployment Frequency ↔ Flow Velocity (Positive Correlation)

**Rule**: These metrics should be **positively correlated** but NOT equal.

**Why**:

- **Flow Velocity**: Items completed per week (individual tickets)
- **Deployment Frequency**: Releases per week (bundled deployments)
- Multiple completed items are often bundled into one release

**Healthy Patterns**:

- High Velocity + High Deployment Frequency = Continuous delivery ✅
- High Velocity + Low Deployment Frequency = Release bottleneck ⚠️
- Low Velocity + High Deployment Frequency = Deploying trivial changes ⚠️
- Low Velocity + Low Deployment Frequency = Slow team (expected correlation) ✅

**Typical Ratio**: 5-20 completed items per deployment (varies by team).

---

### 4. Flow Load (WIP) vs Flow Time (Little's Law)

**Rule**: Flow Time increases proportionally with WIP (at constant throughput).

**Formula (Little's Law)**:

```
Flow Time = WIP ÷ Throughput

Where:
- WIP = Flow Load (items in progress)
- Throughput = Flow Velocity (items completed per time unit)
```

**Example**:

```
WIP = 10 items
Velocity = 5 items/week

Expected Flow Time = 10 ÷ 5 = 2 weeks
```

**Implications**:

- To reduce Flow Time → Reduce WIP or increase Velocity
- If Flow Time doesn't follow this pattern → Check status mappings

---

### 5. CFR and MTTR (Independent but Related)

**Rule**: These measure different aspects of stability and should be tracked independently.

| Metric   | Measures                         | Focus          |
| -------- | -------------------------------- | -------------- |
| **CFR**  | Percentage of failed deployments | **Prevention** |
| **MTTR** | Time to recover from failures    | **Response**   |

**Team Performance Patterns**:

| CFR  | MTTR | Interpretation                                      |
| ---- | ---- | --------------------------------------------------- |
| Low  | Low  | Elite team - prevents failures AND recovers fast ✅ |
| Low  | High | Good prevention, poor incident response ⚠️          |
| High | Low  | Poor quality, but fast recovery 🔄                  |
| High | High | Critical problem - needs immediate attention ❌     |

---

### 6. Flow Efficiency Bounds

**Rule**: Flow Efficiency should always be **between 0% and 100%**.

**Typical Ranges**:

- **Elite teams**: 25-40%
- **Average teams**: 15-25%
- **Struggling teams**: <15%

**⚠️ Warning Signs**:

- **>100%**: Calculation error or status mapping issue
- **>50%**: Unusually high - verify active_statuses configuration
- **<5%**: Excessive wait time or blocked work

**Why Not 100%?**: Even the best teams have:

- Code review wait time
- Testing queue time
- Deployment scheduling delays

---

## Current Week Calculations

### Progressive Blending (Monday-Friday)

Metrics use **progressive blending** for the current week to eliminate Monday reliability drops:

**Affected Metrics**:

- Flow Velocity, Flow Time
- Deployment Frequency, Lead Time for Changes, MTTR

**How It Works**:

- **Formula**: `blended = (actual × weight) + (forecast × (1 - weight))`
- **Weights** (Linear Progression: weight = days_completed / 5): Monday=0%, Tuesday=20%, Wednesday=40%, Thursday=60%, Friday=80%, Saturday-Sunday=100%
- **Result**: Smooth progression from forecast (Monday) to actual (Saturday)

**Impact on Validation**:

- ✅ Correlations remain valid (blending doesn't change relationships)
- ✅ Monday-Friday show blended values with 📊 indicator
- ✅ Saturday-Sunday show pure actual values
- ⚠️ When comparing current week to historical weeks, note that Mon-Fri use blending

**See Also**: [Flow Metrics Guide](./flow_metrics.md) or [DORA Metrics Guide](./dora_metrics.md) for complete algorithm details.

---

## Validation Rules

Use these rules to verify your metrics are correctly configured:

### Must Be True

| Rule | Condition              | If Violated                           |
| ---- | ---------------------- | ------------------------------------- |
| 1    | Lead Time ≥ 0          | Check date field mappings             |
| 2    | MTTR ≥ 0               | Check incident date fields            |
| 3    | Flow Efficiency ≤ 100% | Check active_statuses vs wip_statuses |
| 4    | CFR ≤ 100%             | Calculation error                     |
| 5    | Flow Velocity ≥ 0      | Data issue                            |

### Should Be True (Soft Rules)

| Rule | Condition                          | If Violated                |
| ---- | ---------------------------------- | -------------------------- |
| 1    | Lead Time ≥ Flow Time              | Check deployment endpoint  |
| 2    | MTTR ≥ Lead Time (bugs)            | Check incident_detected_at |
| 3    | Flow Load × Velocity⁻¹ ≈ Flow Time | Check status mappings      |
| 4    | Flow Efficiency < 50%              | Verify active_statuses     |

### Sanity Checks

```
✓ Deployment Frequency > 0 implies completed deployments exist
✓ Lead Time > 0 implies issues have both start and deployment dates
✓ MTTR > 0 implies bugs have both creation and resolution dates
✓ Flow Velocity > 0 implies completed items exist
✓ Flow Time > 0 implies items have status transitions in changelog
```

---

## Timeline Diagrams

### Development Issue Lifecycle

```
                    JIRA Issue Timeline
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Created    In Progress    In Review    Testing    Done    Deployed
       │            │             │           │         │         │
       ▼            ▼             ▼           ▼         ▼         ▼
    ───●────────────●─────────────●───────────●─────────●─────────●───►
       │            │                                   │         │
       │            │◄─────────── Flow Time ──────────►│         │
       │            │                                             │
       │            │◄─────────────── Lead Time ─────────────────►│
       │                                                          │
       │◄──────────────────────── MTTR (for bugs) ───────────────►│

    Legend:
    ● = Status transition timestamp (from changelog)
    ─ = Time passing
```

### Metric Calculation Points

| Metric              | Start Point                            | End Point                                    | Source                       |
| ------------------- | -------------------------------------- | -------------------------------------------- | ---------------------------- |
| **Lead Time**       | First `flow_start_statuses` transition | `fixVersion.releaseDate`                     | Changelog + Operational Task |
| **Flow Time**       | First `flow_start_statuses` transition | First `flow_end_statuses` transition         | Changelog only               |
| **MTTR**            | `created` field                        | `fixVersion.releaseDate` or `resolutiondate` | Fields + Operational Task    |
| **Flow Efficiency** | Time in `active_statuses`              | Time in `wip_statuses`                       | Changelog transitions        |

---

## Common Configuration Issues

### Issue 1: Lead Time Shows "No Data"

**Symptoms**: Lead Time metric shows error or 0
**Likely Causes**:

1. `code_commit_date` not mapped to changelog field (e.g., `status:In Progress.DateTime`)
2. Issues don't have changelog (missing `expand=changelog` in JIRA query)
3. Issues never transitioned to the configured start status

**Fix**: Verify:

```json
"code_commit_date": "status:In Progress.DateTime"
```

### Issue 2: MTTR Shows "No Data" Despite Having Bugs

**Symptoms**: MTTR shows no data but you know bugs exist
**Likely Causes**:

1. `affected_environment` filter not matching (e.g., `=PROD` but bugs have `=Production`)
2. `incident_resolved_at` set to `fixVersions` but bugs don't have fixVersions
3. Bug types not configured in `bug_types` list

**Fix**: Check exact field values in JIRA and match case-sensitively.

### Issue 3: Flow Time > Lead Time

**Symptoms**: Flow Time is greater than Lead Time
**Likely Causes**:

1. Different issues being measured (Flow uses all issues, Lead Time uses deployed only)
2. `flow_end_statuses` doesn't match actual "Done" status names
3. Changelog missing for some issues

**Fix**: Ensure both metrics use same status lists and all issues have changelog.

### Issue 4: Flow Efficiency > 100%

**Symptoms**: Efficiency shows impossible percentage
**Likely Causes**:

1. `active_statuses` contains statuses not in `wip_statuses`
2. Status names don't match exactly (case sensitivity)
3. Duplicate status transitions in changelog

**Fix**: Ensure `active_statuses` is a **subset** of `wip_statuses`.

### Issue 5: CFR Always 0%

**Symptoms**: Change Failure Rate is always 0%
**Likely Causes**:

1. `change_failure` field not mapped correctly
2. Field value filter doesn't match (e.g., `=Yes` but field has `=TRUE`)
3. No operational tasks have the failure flag set

**Fix**: Verify exact field ID and value in JIRA.

---

## Little's Law & Flow Metrics

### The Formula

```
                    WIP
Flow Time = ─────────────────
              Throughput

Where:
- WIP (Work in Progress) = Flow Load
- Throughput = Flow Velocity
- Flow Time = Median cycle time
```

### Practical Application

**Given your metrics, you can validate consistency:**

```
Example:
- Flow Load (WIP): 15 items
- Flow Velocity: 10 items/week

Expected Flow Time = 15 ÷ 10 = 1.5 weeks ≈ 10-11 days

If your actual Flow Time shows 25 days, investigate:
- Are there blocked items inflating WIP?
- Are status transitions being captured correctly?
- Are there "zombie" items stuck in WIP statuses?
```

### Using Little's Law for Planning

| If You Want To...     | Then...                            |
| --------------------- | ---------------------------------- |
| Reduce Flow Time      | Reduce WIP or increase Velocity    |
| Increase Velocity     | Need more capacity or efficiency   |
| Predict delivery time | Flow Time = Current WIP ÷ Velocity |
| Set WIP limits        | WIP = Target Flow Time × Velocity  |

---

## Quick Reference Card

### Field Mapping Requirements

| Metric                   | Required Fields                                                        |
| ------------------------ | ---------------------------------------------------------------------- |
| **Deployment Frequency** | `fixVersions` with `releaseDate`, `devops_task_types`                  |
| **Lead Time**            | `code_commit_date` (changelog), `fixVersions`                          |
| **CFR**                  | `change_failure` (with =Value filter), `fixVersions`                   |
| **MTTR**                 | `incident_detected_at`, `incident_resolved_at`, `affected_environment` |
| **Flow Velocity**        | `completed_date` or `flow_end_statuses`                                |
| **Flow Time**            | `flow_start_statuses`, `flow_end_statuses` (changelog)                 |
| **Flow Efficiency**      | `active_statuses`, `wip_statuses` (changelog)                          |
| **Flow Load**            | `wip_statuses`                                                         |
| **Flow Distribution**    | `flow_item_type`, `flow_type_mappings`                                 |

### Status List Relationships

```
active_statuses ⊆ wip_statuses ⊆ all_statuses

Example:
- flow_end_statuses: [Done, Resolved, Closed, Canceled]
- flow_start_statuses: [In Progress, In Review]
- active_statuses: [In Progress, In Review, Testing]
- wip_statuses: [In Progress, In Review, Testing, Ready for Testing, In Deployment]
```

### Correlation Summary

| Relationship                | Expected                | If Violated                |
| --------------------------- | ----------------------- | -------------------------- |
| Lead Time vs Flow Time      | Lead Time ≥ Flow Time   | Check deployment endpoint  |
| MTTR vs Lead Time           | MTTR ≥ Lead Time (bugs) | Check incident start field |
| Velocity vs Deployment Freq | Positively correlated   | Check release bundling     |
| WIP vs Flow Time            | Little's Law applies    | Check status mappings      |
| Flow Efficiency             | 15-40% typical          | Check active/wip statuses  |

---

## See Also

- [DORA Metrics Documentation](./dora_metrics.md)
- [Flow Metrics Documentation](./flow_metrics.md)
- [Field Mapping Syntax](./namespace_syntax.md)
- [Metrics Index](./metrics_index.md)

---

_Document Version: 1.0 | Last Updated: December 2025_
