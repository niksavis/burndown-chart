# Metrics Snapshot Storage System

## Overview

The snapshot storage system provides historical tracking for metrics that cannot be reconstructed from JIRA data alone. It stores weekly snapshots in a JSON file that grows over time.

## Primary Use Case: Flow Load (WIP)

**Problem**: Flow Load measures current Work In Progress, but JIRA only tells us the current status of issues. To show historical WIP trends, we'd need to reconstruct what status every issue was in at every historical point - which is computationally expensive.

**Solution**: Every time Flow metrics are calculated, we save the current WIP count as a snapshot for the current week. Over time, this builds historical data.

## Architecture

### Storage File

**Location**: `metrics_snapshots.json` (root directory, `.gitignore`d)

**Format**:
```json
{
  "2025-44": {
    "flow_load": {
      "wip_count": 12,
      "by_status": {
        "In Progress": 10,
        "In Review": 2
      },
      "by_issue_type": {
        "Bug": 5,
        "Task": 6,
        "Story": 1
      },
      "timestamp": "2025-10-31T17:00:00Z"
    }
  },
  "2025-43": {
    "flow_load": {
      "wip_count": 15,
      "by_status": {
        "In Progress": 12,
        "In Review": 3
      },
      "timestamp": "2025-10-24T16:30:00Z"
    }
  }
}
```

### Module: `data/metrics_snapshots.py`

**Key Functions**:

```python
# Save a metric snapshot
save_metric_snapshot(
    week_label="2025-44",
    metric_name="flow_load",
    metric_data={"wip_count": 12, "by_status": {...}}
)

# Get weekly values for sparklines
flow_load_values = get_metric_weekly_values(
    week_labels=["2025-43", "2025-44"],
    metric_name="flow_load",
    value_key="wip_count"
)
# Returns: [15, 12]

# Load all snapshots
snapshots = load_snapshots()

# Cleanup old data (keeps last 52 weeks by default)
cleanup_old_snapshots(weeks_to_keep=52)

# Get statistics
stats = get_snapshot_stats()
# Returns: {
#     "total_weeks": 16,
#     "metrics": ["flow_load"],
#     "oldest_week": "2025-29",
#     "newest_week": "2025-44",
#     "file_size_kb": 12.5
# }
```

## How It Works

### 1. Automatic Snapshot Saving

Every time Flow metrics are calculated (when user navigates to Flow Metrics tab or clicks "Update Data"):

```python
# In callbacks/dora_flow_metrics.py
load = calculate_flow_load_v2(all_issues, wip_statuses)

# Save snapshot for current week
save_metric_snapshot(
    week_label=current_week_label,  # e.g., "2025-44"
    metric_name="flow_load",
    metric_data={
        "wip_count": load["wip_count"],
        "by_status": load["by_status"],
        "by_issue_type": load["by_issue_type"]
    }
)
```

### 2. Loading Historical Data

When displaying Flow Load card with sparkline:

```python
# Get historical WIP values for last 16 weeks
flow_load_values = get_metric_weekly_values(
    week_labels=["2025-29", "2025-30", ..., "2025-44"],
    metric_name="flow_load",
    value_key="wip_count"
)
# Returns: [0, 0, 0, ..., 15, 12]  (zeros for weeks with no data yet)

# Add to metrics_data for sparkline rendering
metrics_data["flow_load"]["weekly_values"] = flow_load_values
```

### 3. Building Historical Data Over Time

**Initial State**: Empty file, all sparkline values are 0
**After 1 week**: 1 data point
**After 4 weeks**: 4 data points
**After 16 weeks**: Full sparkline

This is **intentional** - the system builds reliable historical data organically rather than trying to reconstruct it.

## Extensibility

The system is designed to support any metric, not just Flow Load:

```python
# Example: Save custom deployment frequency snapshot
save_metric_snapshot(
    week_label="2025-44",
    metric_name="deployment_frequency",
    metric_data={
        "deployments": 42,
        "by_environment": {
            "production": 40,
            "staging": 2
        }
    }
)

# Retrieve it later
deploy_values = get_metric_weekly_values(
    week_labels=week_labels,
    metric_name="deployment_frequency",
    value_key="deployments"
)
```

## Data Retention

**Default**: Keep last 52 weeks (1 year) of snapshots

**Manual Cleanup**:
```python
from data.metrics_snapshots import cleanup_old_snapshots

# Keep only last 26 weeks
cleanup_old_snapshots(weeks_to_keep=26)
```

**Automatic Cleanup**: Could be added to "Update Data" operation if needed.

## File Size Considerations

**Typical File Size**:
- 1 week of Flow Load: ~200 bytes
- 52 weeks: ~10 KB
- 1 year with multiple metrics: ~50-100 KB

**Conclusion**: File size is negligible, no compression needed.

## Backup Strategy

The snapshot file is `.gitignore`d but should be backed up alongside other configuration files:

```powershell
# Backup snapshot file
Copy-Item metrics_snapshots.json config-backups/customer-name/metrics_snapshots_$(Get-Date -Format 'yyyy-MM-dd').json
```

## Future Enhancements

### 1. More Metrics

Could extend to track:
- Daily deployment counts (instead of weekly)
- Team velocity trends
- Bug resolution rates
- Custom business metrics

### 2. Aggregation Levels

Currently: Weekly snapshots  
Could add: Daily, monthly, quarterly snapshots

### 3. Automatic Cleanup

Add to "Update Data" operation to automatically prune old snapshots.

### 4. Export/Import

Add UI to export/import snapshot data for analysis or backup.

## Troubleshooting

### No Sparkline Data Shows

**Symptom**: Flow Load sparkline shows all zeros  
**Cause**: No snapshot data yet  
**Solution**: Navigate to Flow Metrics tab to save first snapshot, then check again next week

### File Corrupted

**Symptom**: Errors loading `metrics_snapshots.json`  
**Solution**: 
1. Check file syntax with JSON validator
2. Restore from backup if available
3. Delete file to start fresh (loses historical data)

### Performance Issues

**Symptom**: Slow dashboard loading  
**Cause**: Snapshot file too large (unlikely with current design)  
**Solution**: Run `cleanup_old_snapshots(weeks_to_keep=26)` to reduce size

## Testing

```python
# Manual testing in Python REPL
from data.metrics_snapshots import *

# Save test snapshot
save_metric_snapshot("2025-44", "test_metric", {"value": 42})

# Verify it saved
snapshot = get_metric_snapshot("2025-44", "test_metric")
print(snapshot)  # Should show {"value": 42, "timestamp": "..."}

# Get stats
stats = get_snapshot_stats()
print(stats)

# Cleanup test data
snapshots = load_snapshots()
del snapshots["2025-44"]
save_snapshots(snapshots)
```

## Summary

The snapshot storage system provides a simple, extensible solution for tracking point-in-time metrics over time. It:

- ✅ Requires no changelog queries (performance-friendly)
- ✅ Builds data organically over time
- ✅ Supports any metric with minimal code
- ✅ Has negligible storage overhead
- ✅ Is easy to backup and restore
- ✅ Self-documenting JSON format

The trade-off is that historical data is only available from the point of implementation forward, which is acceptable for most use cases.
