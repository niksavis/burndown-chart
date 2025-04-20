# Icon Usage Audit

## Overview

This document tracks the current usage of icons throughout the Burndown Chart application to ensure consistency and identify areas for improvement.

## Icon Inventory

### Components Module (`ui/components.py`)

| Component                 | Current Icon Class          | Context                 | Recommendation                                                     |
| ------------------------- | --------------------------- | ----------------------- | ------------------------------------------------------------------ |
| create_info_tooltip       | fas fa-info-circle          | Information tooltip     | Switch to semantic icon "info"                                     |
| create_help_modal         | fas fa-project-diagram      | Project overview title  | Switch to semantic icon "data"                                     |
| create_help_modal         | fas fa-exclamation-triangle | Warning/notice section  | Switch to semantic icon "warning"                                  |
| create_help_modal         | fas fa-info-circle          | Information section     | Already matches semantic icon "info"                               |
| create_help_modal         | fas fa-tasks                | Items in chart legend   | Already matches semantic icon "items"                              |
| create_help_modal         | fas fa-chart-line           | Points in chart legend  | Already matches semantic icon "points"                             |
| create_pert_info_table    | fas fa-project-diagram      | Project overview header | Switch to semantic icon "data"                                     |
| create_pert_info_table    | fas fa-calendar-day         | Deadline section        | Already matches semantic icon "calendar"                           |
| create_pert_info_table    | fas fa-tasks                | Items section heading   | Already matches semantic icon "items"                              |
| create_pert_info_table    | fas fa-chart-bar            | Chart section heading   | Already matches semantic icon "chart"                              |
| create_pert_info_table    | fas fa-arrow-up/down/equals | Trend indicators        | Switch to semantic icons "trend_up", "trend_down", "trend_neutral" |
| create_pert_info_table    | fas fa-info-circle          | Info text               | Already matches semantic icon "info"                               |
| create_trend_indicator    | fas fa-arrow-up/down/alt-h  | Trend direction         | Switch to semantic icons "trend_up", "trend_down", "trend_neutral" |
| create_export_buttons     | fas fa-file-csv             | CSV export button       | Add semantic icon "export"                                         |
| create_export_buttons     | fas fa-file-image           | Image export button     | Add semantic icon "export"                                         |
| create_export_buttons     | fas fa-file-export          | Statistics export       | Already matches semantic icon "export"                             |
| create_validation_message | fas fa-check-circle         | Valid feedback          | Already matches semantic icon "success"                            |
| create_validation_message | fas fa-exclamation-triangle | Warning feedback        | Already matches semantic icon "warning"                            |
| create_validation_message | fas fa-times-circle         | Invalid feedback        | Add semantic icon "danger"                                         |

### Layout Module (`ui/layout.py`)

Icons in layout components should be audited and updated to use the new semantic icon system as part of the Phase 4 layout standardization.

### Tabs Module (`ui/tabs.py`)

Tab navigation icons should be standardized as part of the Phase 5.1 tab navigation improvements.

## Alignment Issues

The following components have inconsistent icon alignment:

1. In `create_pert_info_table`, trend indicators have inconsistent vertical alignment with text
2. In `create_help_modal`, the icon spacing is inconsistent between sections
3. In `create_export_buttons`, icons have varying spacing relative to the button text

## Recommendations

1. Refactor existing direct icon usage to use the new semantic icon system
2. Convert all icon+text combinations to use the `create_icon_text()` utility function
3. Ensure all icon-only buttons have tooltips for accessibility
4. Standardize icon sizes based on hierarchy:
   - Section headers: "lg" or "xl" size
   - Button icons: "md" size
   - Indicator icons: "md" size  
   - Inline text icons: "sm" size

## Implementation Plan

1. Update all components with direct icon usage
2. Create a PR template that includes an icon usage check
3. Add icon guidelines to the developer documentation
4. Set up linting rules to enforce proper icon usage patterns
