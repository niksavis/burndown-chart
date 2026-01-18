# Burndown Chart 🔥 - Documentation

## 📚 Documentation Overview

This documentation is organized into two main sections:

- **[User Documentation](#-user-documentation)** - Understanding metrics, calculations, and using the application
- **[Developer Documentation](#-developer-documentation)** - Implementation details, architecture, and extending the system

---

## 👤 User Documentation

Documentation for project managers, team leads, and users who want to understand how metrics work and interpret results.

### Getting Started

- **[Metrics Index](metrics_index.md)** ⭐ **START HERE** - Navigation hub with quick start guide and progressive learning path

### Understanding Metrics

**Dashboard Metrics** (Project Tracking):
- **[Dashboard Metrics Guide](dashboard_metrics.md)** - Health score, completion forecast, velocity, remaining work
- **[Project Health Formula](health_formula.md)** - Comprehensive 6-dimensional health assessment (20+ signals)

**Process Performance Metrics**:
- **[DORA Metrics Guide](dora_metrics.md)** - DevOps performance: deployment frequency, lead time, change failure rate, MTTR
- **[Flow Metrics Guide](flow_metrics.md)** - Work process health: velocity, flow time, efficiency, WIP, distribution
- **[Budget Metrics Guide](budget_metrics.md)** - Financial tracking: budget consumption, burn rate, runway, cost per item

**Advanced Topics**:
- **[Metrics Correlation Guide](metrics_correlation_guide.md)** - How metrics relate to each other and validation rules

---

## 👨‍💻 Developer Documentation

Documentation for developers extending the application, implementing new metrics, or understanding the technical architecture.

### Configuration & Integration

- **[Namespace Syntax](namespace_syntax.md)** - JIRA field mapping syntax for implementing custom metrics
- **[Caching System](caching_system.md)** - Database architecture and caching strategy

### Code Standards & Practices

- **[Logging Standards](logging_standards.md)** - Logging conventions, levels, and security practices
- **[Defensive Refactoring Guide](defensive_refactoring_guide.md)** - Safely removing unused code and dependencies

### Build & Release

- **[Release Process](release_process.md)** - Build workflow, executable packaging, and release automation
- **[Updater Architecture](updater_architecture.md)** - Self-updating mechanism, crash recovery, and troubleshooting

### Architecture Reference

For detailed implementation guides, see:
- **Field mapping implementation**: `data/field_mapper.py`, `data/field_detector.py`
- **Metrics calculators**: `data/dora_calculator.py`, `data/flow_calculator.py`, `data/health_calculator.py`
- **Database schema**: `data/database.py` (12 tables: profiles, queries, jira_issues, project_statistics, etc.)

---

## 📖 Quick Navigation

| I want to...                  | Go to                                                         |
| ----------------------------- | ------------------------------------------------------------- |
| Learn metrics basics          | [Metrics Index](metrics_index.md)                             |
| Understand health score       | [Project Health Formula](health_formula.md)                   |
| Configure DORA metrics        | [DORA Metrics Guide - Field Configuration](dora_metrics.md)   |
| Configure Flow metrics        | [Flow Metrics Guide - Field Configuration](flow_metrics.md)   |
| Validate metric relationships | [Metrics Correlation Guide](metrics_correlation_guide.md)     |
| Map custom JIRA fields        | [Namespace Syntax](namespace_syntax.md)                       |
| Understand caching behavior   | [Caching System](caching_system.md)                           |
| Add logging to new features   | [Logging Standards](LOGGING_STANDARDS.md)                     |
| Remove unused code safely     | [Defensive Refactoring Guide](defensive_refactoring_guide.md) |
| Build standalone executable   | [Release Process](release_process.md)                         |
| Understand update mechanism   | [Updater Architecture](updater_architecture.md)               |

---

*Document Version: 2.0 | Last Updated: January 2026*
