# Project Management Metrics: Definitions and Mathematical Formulas

## Overview

This comprehensive reference provides formal definitions and mathematical formulas for essential project management metrics. The metrics are organized by classification: traditional project management metrics, DORA metrics, and Flow metrics. All formulas accommodate a time window variable $W$, defined as one week (7 days, Monday to Sunday).

---

## Average Cycle Time

**Definition:** Average Cycle Time measures the mean duration from when work begins (moved to "In Progress") until completion (marked as "Done"). This metric isolates active processing time and team efficiency, excluding queue time and wait periods. It reveals how efficiently a team transforms work items from active development through delivery.

**Formula:**

$$\text{Avg Cycle Time}(W) = \frac{\sum_{i=1}^{n} (C_i - S_i)}{n}$$

Where:
- $C_i$ = completion time of work item $i$
- $S_i$ = start time of work item $i$
- $n$ = number of completed work items in time window $W$
- $W$ = 7 days (Monday to Sunday)

---

## DORA Metrics

The four DORA (DevOps Research and Assessment) metrics represent evidence-based key performance indicators that correlate with high-performing engineering organizations. These metrics balance speed and quality, with the first two measuring throughput and the latter two measuring stability.

### Deployment Frequency (DF)

**Definition:** Deployment Frequency measures how often a team successfully deploys code changes to production. Higher deployment frequency indicates a more efficient, responsive delivery process and reflects the team's ideal release rhythm. High-performing teams typically ship code one to three times per week.

**Formula:**

$$\text{Deployment Frequency}(W) = \frac{\text{Number of Successful Deployments}}{W}$$

Where:
- $W$ = 7 days
- Result is expressed as deployments per day or deployments per week

### Lead Time for Changes (LT)

**Definition:** Lead Time for Changes measures the time elapsed from code commit to successful deployment in production. This metric reflects the efficiency of the entire software delivery pipeline, from development through deployment.

**Formula:**

$$\text{Lead Time for Changes}(W) = \text{median}\left(\frac{\text{Deployment}_j - \text{Commit}_j}{1 \text{ day}}\right)$$

Where:
- $\text{Commit}_j$ = timestamp of code commit $j$
- $\text{Deployment}_j$ = timestamp of successful deployment for commit $j$
- The median is calculated over all commits deployed within time window $W$
- Result is expressed in days (or seconds/hours as appropriate)

### Change Failure Rate (CFR)

**Definition:** Change Failure Rate measures the percentage of deployments that result in failures, rollbacks, or hotfixes in production. A lower change failure rate indicates a more reliable delivery process and reflects code quality and test effectiveness.

**Formula:**

$$\text{Change Failure Rate}(W) = \frac{\text{Number of Failed Deployments}}{\text{Total Number of Deployments}} \times 100\%$$

Where:
- Failed deployments include those requiring rollbacks, hotfixes, or patches
- Calculated over time window $W$

### Mean Time to Recovery (MTTR) / Time to Restore Service (TTRS)

**Definition:** Mean Time to Recovery measures the average time required to restore service following a production failure or incident. Lower recovery times indicate a more resilient system and responsive incident response capability. MTTR is calculated as the median time an incident was open on a production environment.

**Formula:**

$$\text{MTTR}(W) = \text{median}\left(\frac{\sum_{i=1}^{m} (R_i - F_i)}{m}\right)$$

Where:
- $F_i$ = timestamp when failure $i$ was detected
- $R_i$ = timestamp when service was restored for failure $i$
- $m$ = number of failures during time window $W$
- Result is expressed in days (or hours as appropriate)

---

## Flow Metrics

Flow Metrics provide a comprehensive framework for measuring the efficiency, predictability, and health of software delivery workflows. These metrics are based on the Flow Framework created by Mik Kersten and are part of the SAFe (Scaled Agile Framework) methodology.

### Flow Velocity

**Definition:** Flow Velocity measures the rate at which work items are completed and delivered within a given time period, independent of size estimates. This metric answers "Is value delivery accelerating?" and provides historical data for future forecasting and capacity planning.

**Formula:**

$$\text{Flow Velocity}(W) = \frac{\text{Number of Completed Flow Items}}{W}$$

Where:
- Flow Items include features, defects, risks, and technical debt
- $W$ = 7 days
- Result is expressed as items per week or items per day

### Flow Time

**Definition:** Flow Time measures the total duration from when work begins (business approval) through completion, encompassing both active work and waiting periods. This metric reflects time-to-market and identifies where delays occur in the value stream.

**Formula (Little's Law):**

$$\text{Flow Time} = \frac{\text{Work In Progress}}{\text{Throughput}}$$

Or alternatively:

$$\text{Average Flow Time}(W) = \frac{\sum_{i=1}^{n} (C_i - S_i)}{n}$$

Where:
- $C_i$ = completion time of work item $i$
- $S_i$ = start time of work item $i$
- Throughput = rate of completed items per unit time
- Result is expressed in days

### Flow Efficiency

**Definition:** Flow Efficiency measures the proportion of time spent on active, value-adding work relative to total flow time. This metric identifies friction points such as unclear requirements, blocked reviews, or dependency issues that create waste in the system.

**Formula:**

$$\text{Flow Efficiency}(W) = \frac{\text{Active Time}}{\text{Total Flow Time}} \times 100\%$$

Where:
- Active Time = time spent actively working (excluding wait states)
- Total Flow Time = total elapsed time from start to completion
- Result is expressed as a percentage; higher percentages indicate less waste

### Flow Load

**Definition:** Flow Load measures the number of work items currently in progress (Work In Progress, or WIP). Monitoring Flow Load helps identify the optimal balance between capacity and demand, as high WIP often leads to context switching and reduced throughput.

**Formula:**

$$\text{Flow Load}(W) = \text{Number of Active Work Items at Time } W$$

Or for average over a period:

$$\text{Average Flow Load}(W) = \frac{\sum_{d=1}^{7} \text{WIP}(d)}{7}$$

Where:
- WIP = count of items in progress at any given moment
- $d$ = each day in the week
- Optimal Flow Load maximizes Flow Velocity while maintaining predictable Flow Time

### Flow Distribution

**Definition:** Flow Distribution measures the mix and proportion of different work types (features, defects, risks, technical debt) completed during a specific time period. This metric ensures balanced investment across value generation and business protection activities.

**Formula:**

$$\text{Flow Distribution}(W) = \frac{\text{Number of Completed Items of Type } j}{\text{Total Number of Completed Items}} \times 100\%$$

Where:
- Type $j$ represents each category: features, defects, risks, or technical debt
- Calculated for each work type over time window $W$
- Results sum to 100% across all work types

### Flow Predictability

**Definition:** Flow Predictability (also called Program Predictability Measure or PPM in SAFe) assesses the reliability of teams and Agile Release Trains (ARTs) in delivering against planned objectives. This metric measures alignment between planned and actual business value delivered, indicating forecast accuracy and planning realism. Reliable teams should operate in the 80-100% range.

**Formula:**

$$\text{Flow Predictability}(W) = \frac{\text{Actual Business Value Delivered}}{\text{Planned Business Value}} \times 100\%$$

Or alternatively, as Planned Completion Achievement:

$$\text{Flow Predictability}(W) = \frac{\text{Planned Items Completed}}{\text{Total Planned Items}} \times 100\%$$

Where:
- Calculated over program increment or specified time window $W$
- Target range for high-performing teams: 80-100%
- Values below 80% indicate unrealistic planning or organizational issues

---

## Velocity Consistency

**Definition:** Velocity Consistency measures the stability and predictability of team velocity over multiple time periods. This metric indicates whether a team's delivery rate remains stable or exhibits significant variation, which impacts forecasting reliability and planning accuracy.

**Formula:**

$$\text{Velocity Consistency}(W) = \frac{\sigma_V}{\bar{V}} \times 100\%$$

Where:
- $\sigma_V$ = standard deviation of velocity measured over rolling 3-5 sprint periods
- $\bar{V}$ = mean (average) velocity over the same periods
- Result is expressed as a coefficient of variation (percentage)

Alternatively, using velocity range:

$$\text{Velocity Range} = [\bar{V} - (1.5 \times \sigma_V), \bar{V} + (1.5 \times \sigma_V)]$$

Where:
- Lower consistency ratios (e.g., <10%) indicate more predictable velocity
- Higher ratios (>20%) suggest instability requiring investigation

---

## Trend Stability

**Definition:** Trend Stability measures how much forecasts or metrics change from one measurement cycle to the next. This metric quantifies instability—the greater the changes between cycles, the less stable the trend. Stable trends enable more reliable planning and forecasting.

**Formula:**

$$\text{Trend Stability}(W) = \frac{\text{Cycle-over-Cycle Change (COCC)}}{\text{Prior Period Value}} \times 100\%$$

Or more formally:

$$\text{COCC} = \frac{\sum_{t} \sum_{i} \left| M_t^{\text{current}} - M_t^{\text{prior}} \right|}{\sum_{t} M_t^{\text{prior}}}$$

Where:
- $M_t^{\text{current}}$ = metric value in current measurement cycle $t$
- $M_t^{\text{prior}}$ = metric value in prior measurement cycle $t$
- Applied over time window $W$
- Result expressed as percentage change; lower percentages indicate greater stability

Alternatively, for trend analysis over multiple cycles:

$$\text{Average Trend Stability}(W) = \frac{\sum_{c=1}^{n} \text{COCC}_c}{n}$$

Where $n$ represents multiple consecutive measurement cycles.

---

## Summary Table

| Metric | Category | Primary Focus | Time Window |
|--------|----------|---|---|
| Avg Cycle Time | Traditional | Efficiency | $W = 7$ days |
| Deployment Frequency | DORA | Velocity | $W = 7$ days |
| Lead Time for Changes | DORA | Velocity | $W = 7$ days |
| Change Failure Rate | DORA | Stability | $W = 7$ days |
| MTTR / Time to Restore Service | DORA | Stability | $W = 7$ days |
| Flow Velocity | Flow | Throughput | $W = 7$ days |
| Flow Time | Flow | Timeliness | $W = 7$ days |
| Flow Efficiency | Flow | Waste Reduction | $W = 7$ days |
| Flow Load | Flow | Capacity Balance | $W = 7$ days |
| Flow Distribution | Flow | Work Mix | $W = 7$ days |
| Flow Predictability | Flow | Reliability | $W = 7$ days |
| Velocity Consistency | Agile | Predictability | Multiple sprints |
| Trend Stability | Analysis | Stability | Multiple cycles |

---

## Notes

1. **Time Window Interpretation:** All formulas use $W = 7$ days (Monday to Sunday) as the standard measurement period unless otherwise specified in the metric definition.

2. **Little's Law Application:** Flow Time calculations leverage Little's Law from queuing theory, which states that the average number of items in a system equals the arrival rate multiplied by the average time in the system.

3. **Aggregation Methods:** 
   - Deployment Frequency uses **mean (average)**
   - Lead Time for Changes uses **median**
   - Time to Restore Service uses **median**
   - Change Failure Rate uses **daily median per period**

4. **High-Performing Benchmarks:**
   - Flow Predictability: 80-100%
   - Velocity Consistency: <10% for high predictability; >20% indicates instability
   - Deployment Frequency: 1-3 times per week or higher

5. **Data Collection:** All metrics require accurate timestamp data from project management tools, CI/CD pipelines, and incident management systems for precise calculation.

---

## References

- GitLab DORA Metrics Documentation (DevOps Research and Assessment)
- Scaled Agile Framework (SAFe) Flow Metrics Specification
- Flow Framework by Mik Kersten
- Little's Law in Queuing Theory
