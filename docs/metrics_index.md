# Metrics Documentation Index

**Audience**: Project managers, team leads, and stakeholders who want to understand project metrics and calculations

This is your starting point for understanding how the application measures project performance. The documentation is organized into focused guides, each covering a specific category of metrics.

**🚀 New User?** Start with the **[Quickstart Guide](quickstart_guide.md)** for complete first-time setup instructions (15 minutes).

---

## 📚 Documentation Structure

The application tracks four categories of metrics, each documented in its own focused guide:

### 1. [Project Dashboard Metrics](./dashboard_metrics.md) ⭐ **START HERE**
**Best for**: Project managers, stakeholders tracking delivery progress

Covers the **Project Dashboard** tab metrics:
- **[Project Health Score](./health_formula.md)** - Comprehensive multi-dimensional assessment using 20+ signals
- **Completion Forecast** - When the project will finish based on current velocity
- **Current Velocity** - Team throughput (items/week or points/week)
- **Remaining Work** - Outstanding items and story points
- **PERT Timeline** - Optimistic/most likely/pessimistic completion scenarios
- **Dashboard Insights** - Automated alerts for schedule variance, velocity trends, milestones

**Also includes**: Statistical Limitations section documenting calculation issues and fixes.

---

### 2. [DORA Metrics](./dora_metrics.md)
**Best for**: Engineering teams optimizing deployment and incident response

Covers the **DORA & Flow Metrics** tab - DORA section:
- **Deployment Frequency** - How often you ship to production
- **Lead Time for Changes** - Time from code ready to deployed
- **Change Failure Rate** - Percentage of deployments that fail
- **Mean Time to Recovery (MTTR)** - Time to recover from production incidents

**DORA = DevOps Research and Assessment** - Industry-standard software delivery performance metrics researched by Google.

---

### 3. [Flow Metrics](./flow_metrics.md)
**Best for**: Teams optimizing work process and managing WIP

Covers the **DORA & Flow Metrics** tab - Flow section:
- **Flow Velocity** - Work completed per week (by type: Feature/Defect/Tech Debt/Risk)
- **Flow Time** - Cycle time from start to completion
- **Flow Efficiency** - Active work time vs. waiting time percentage
- **Flow Load (WIP)** - Work in progress with healthy thresholds
- **Flow Distribution** - Balance of work types with recommended ranges

**Flow Framework** - Process metrics from Mik Kersten's "Project to Product" methodology.

---

### 4. [Budget Metrics](./budget_metrics.md)
**Best for**: Project managers and finance stakeholders tracking project costs

Covers financial tracking and budget management:
- **Total Budget** - Project financial envelope
- **Budget Consumed** - Spending based on completed work
- **Burn Rate** - Average weekly spending rate
- **Runway** - Weeks remaining at current burn rate
- **Cost per Item** - Velocity-driven cost per work item
- **Cost per Point** - Velocity-driven cost per story point

**Lean/Agile Budgeting** - Adaptive financial management using velocity-driven metrics rather than fixed estimates.

---

### 5. [Metrics Correlation Guide](./metrics_correlation_guide.md)
**Best for**: Teams validating metric configurations and understanding relationships

Covers metric relationships and validation:
- **Expected Correlations** - Lead Time vs Flow Time, MTTR vs Lead Time, etc.
- **Little's Law** - WIP, Velocity, and Flow Time mathematical relationship
- **Validation Rules** - How to verify your metrics are configured correctly
- **Timeline Diagrams** - Visual explanation of measurement points
- **Common Issues** - Troubleshooting guide for metric configuration problems

**Use this guide to verify your field mappings are producing reliable, consistent metrics.**

---

## 🚀 Quick Start

**New to metrics?** Follow this progression:

### Week 1: Establish Baselines
1. Read [Dashboard Metrics](./dashboard_metrics.md) to understand project forecasting
2. Track **Current Velocity** and **Remaining Work** for 2+ weeks
3. Focus on consistency over optimization

### Week 2-4: Add Process Insights
4. Read [Flow Metrics](./flow_metrics.md) to understand work process
5. Track **Flow Load (WIP)** - single biggest lever for speed improvements
6. Measure **Flow Time** to establish cycle time baseline

### Beyond Week 4: Optimize Delivery
7. Read [DORA Metrics](./dora_metrics.md) to measure deployment maturity
8. Start with **Deployment Frequency** and **Change Failure Rate**
9. Add **Lead Time** and **MTTR** as deployment process matures

**Progressive Approach**: Don't try to optimize all metrics at once. Master 2-3 metrics, establish baselines, then expand.

---

## 📖 Shared Concepts

### Metric Relationships
All metrics interconnect - improving one often improves others:

```
Reduce WIP (Flow Load) 
  → Faster Flow Time 
  → Faster Lead Time (DORA)
  → More Deployment Frequency (DORA)
  → Better project forecasts (Dashboard)
```

**Key insight**: Flow Load (WIP) is your primary control lever.

### Performance Tiers
Most metrics use tier-based performance indicators:

- **Elite** (Green): Top 10% of teams (DORA research)
- **High** (Blue): Top 25% of teams
- **Medium** (Yellow): Top 50% of teams  
- **Low** (Red): Bottom 50%, needs improvement

### Weekly Calculations
All metrics are calculated weekly (Monday-Sunday, ISO 8601 standard) and cached for performance.

**Aggregation Methods**: Metrics displayed on cards use different statistical methods:
- **Median of weekly medians**: Lead Time, MTTR, Flow Time (robust to outliers)
- **Average**: Deployment Frequency, Velocity, Efficiency (natural for rates)
- **Overall rate**: Change Failure Rate (true percentage across all deployments)
- **Current snapshot**: Flow Load/WIP (point-in-time, not historical)

See card footers for aggregation method and time period (e.g., "Median of weekly medians • 1,234 issues • 12 weeks").

### Common Pitfalls
- ❌ Gaming metrics (e.g., deploying tiny changes to boost frequency)
- ❌ Comparing across teams (context matters)
- ❌ Setting arbitrary targets without business rationale
- ❌ Reacting to week-to-week noise (look for 4+ week trends)

Full details in each metric guide.

---

## 🔍 Finding Specific Information

### "How do I calculate...?"
- Dashboard forecasts → [Dashboard Metrics](./dashboard_metrics.md) - Calculation Details sections
- DORA metrics → [DORA Metrics](./dora_metrics.md) - individual metric sections
- Flow metrics → [Flow Metrics](./flow_metrics.md) - individual metric sections

### "What does this number mean?"
- Health scores & colors → [Dashboard Metrics](./dashboard_metrics.md) - Project Health Score
- Performance tiers (Elite/High/etc.) → [DORA Metrics](./dora_metrics.md) - Performance Tier Thresholds
- WIP health zones → [Flow Metrics](./flow_metrics.md) - Flow Load (WIP)

### "How do I improve...?"
- Project completion date → [Dashboard Metrics](./dashboard_metrics.md) - Action Guides
- Deployment frequency → [DORA Metrics](./dora_metrics.md) - Deployment Frequency - Common Issues
- Cycle time → [Flow Metrics](./flow_metrics.md) - Flow Time - Action Guides

### "Something seems wrong..."
- Statistical limitations → [Dashboard Metrics](./dashboard_metrics.md) - Statistical Limitations section
- Edge cases → Check "Gotchas" sections in each guide
- Calculation verification → "Documentation Verification" sections show code verification dates

---

## 📝 Document Navigation Tips

Each guide includes:
- **Table of Contents** - Jump to specific metrics
- **Quick Reference** - Summary tables for fast lookups
- **Calculation Details** - Mathematical formulas with examples
- **Action Guides** - What to do when metrics are good/bad
- **Common Issues** - Troubleshooting and gotchas
- **Practical Examples** - Real-world UI scenarios

**Recommendation**: Bookmark the index and one guide you use most frequently.

---

## 🔄 Document Maintenance

**Last Major Update**: November 2025 (split from monolithic 2,000-line file)

**Verification Status**:
- ✅ **Dashboard Metrics**: Verified against code, velocity calculation fix documented
- ✅ **DORA Metrics**: Verified against `data/dora_calculator.py` implementations
- ✅ **Flow Metrics**: Verified against `data/flow_calculator.py` implementations
- ✅ **Budget Metrics**: Verified against `data/budget_calculator.py` implementations

**See**: "Documentation Verification Status" sections in each guide for detailed verification results.

---

## 📧 Questions or Issues?

If you find discrepancies between documentation and actual behavior:
1. Check "Statistical Limitations" section in [Dashboard Metrics](./dashboard_metrics.md)
2. Check "Documentation Verification Status" in relevant guide
3. File an issue with: metric name, expected behavior, actual behavior, screenshot

**Known Limitations**: See Dashboard Metrics guide for transparent documentation of calculation issues and fixes.

---

*Document Version: 2.0 | Last Updated: January 2026*
