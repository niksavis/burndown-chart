# Bug Analysis Metrics Guide

**Audience**: Project managers, team leads, and quality-focused stakeholders
**Part of**: [Metrics Documentation Index](metrics_index.md)

## Overview

Bug Analysis provides a dedicated view of quality signals based on issue types mapped as defects. The tab surfaces bug volume, trends, and investment to help teams prioritize quality work.

## Core Metrics

### Bug Counts

- Total bugs in the selected time range.
- Open bugs vs closed bugs.
- Resolution rate as a percentage of total bugs.

### Bug Trends

- Weekly creation and closure counts.
- Visual emphasis when creation exceeds closure for sustained periods.

### Bug Investment

- Story points invested in bugs when points are available.
- Item counts are always shown; points are optional.

## Quality Insights

Insights provide guidance when patterns indicate quality risk. Examples include:

- Sustained creation exceeding closure.
- Low resolution rate.
- Upward trend in new defects.

## Forecast Behavior

When enough historical closure data exists, the dashboard can forecast completion timing for open defects. If closure rate is not positive, forecasts are suppressed.

## Configuration Dependencies

- Issue type mapping must categorize bugs correctly.
- Field mappings must include status and resolution details.

## Related Documentation

- [Flow Metrics Guide](flow_metrics.md)
- [DORA Metrics Guide](dora_metrics.md)
