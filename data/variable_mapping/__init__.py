"""Variable mapping system for flexible JIRA field extraction.

This package provides a rule-based variable mapping system that allows metrics
to extract data from JIRA issues using multiple sources with priority ordering,
conditional filters, and changelog analysis.

Key Components:
- models.py: Pydantic data models for variable mappings
- extractor.py: Variable extraction engine with source evaluation
- validator.py: Validation logic for mappings and extracted values

Usage:
    from data.variable_mapping import VariableExtractor, VariableMapping

    extractor = VariableExtractor(variable_mappings)
    value = extractor.extract_value("deployment_timestamp", issue, changelog)
"""

from data.variable_mapping.models import (
    VariableMapping,
    SourceRule,
    MappingFilter,
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogEventSource,
    ChangelogTimestampSource,
    FixVersionSource,
    CalculatedSource,
)

__all__ = [
    "VariableMapping",
    "SourceRule",
    "MappingFilter",
    "FieldValueSource",
    "FieldValueMatchSource",
    "ChangelogEventSource",
    "ChangelogTimestampSource",
    "FixVersionSource",
    "CalculatedSource",
]
