# Grid Utilities Migration Guide

## Overview

This document details the process of migrating from deprecated grid template and table functions to the new, enhanced grid utilities. This migration was completed as part of the deprecated functions migration plan.

## Migration Process

The migration was completed in three phases:

### Phase 1: Simple Import Updates

- Updated import statements in files using deprecated functions
- Changed `from ui.grid_templates import ...` to `from ui.grid_utils import ...`
- This was a low-risk first step that allowed code to start using newer utility modules

### Phase 2: Function Implementation Updates

- Updated the implementation of `create_statistics_data_card` in `ui/cards.py`
- Directly implemented enhanced versions of the table utility functions
- Added mobile responsive features and better styling options
- Maintained backward compatibility while improving functionality

### Phase 3: Standardization and Documentation

- Enhanced the deprecation warnings in `ui/grid_templates.py`
- Created a unified approach to grid and layout functionality
- Added clear documentation and migration guidelines

## Technical Implementation Details

### Table Components Migration

The primary challenge in this migration was handling the table-related functions (`create_aligned_datatable` and `create_data_table`), as these were not available in the newer `ui.grid_utils` module.

Instead of trying to add these functions to `ui.grid_utils`, we chose to directly implement enhanced versions within the components that needed them:

1. Created local implementations within the `create_statistics_data_card` function in `ui/cards.py`
2. Added several improvements to the table functionality:
   - Better mobile responsiveness with automatic column hiding
   - Enhanced styling for touch devices
   - Visual feedback for editable cells and better focus indicators
   - Improved accessibility features

This approach provides several advantages:

- Makes components more self-contained
- Allows for targeted optimization for specific use cases
- Reduces dependencies between modules
- Makes component behavior more predictable

### Deprecation Warning Enhancement

The `ui/grid_templates.py` module was enhanced with:

1. A more visible deprecation notice at the module level
2. A decorator to consistently apply deprecation warnings to all deprecated functions
3. Clear migration instructions in the module docstring
4. Parameter-by-parameter mapping to new function signatures

```python
def _deprecation_warning(func):
    """
    Decorator to add deprecation warnings to functions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"Function {func.__name__} is deprecated and will be removed in a future release. "
            f"Use equivalent functions from ui.grid_utils instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)
    return wrapper
```

## Benefits of the Migration

1. **Better responsiveness**: The new implementations provide better mobile responsiveness with automatic column adaptation.
2. **Enhanced styling**: Visual feedback for interactive elements and better focus indicators.
3. **More maintainable code**: Components are more self-contained with local implementations.
4. **Improved documentation**: Clear deprecation warnings and migration guidelines.
5. **Future-proofing**: Preparation for eventual removal of deprecated functions.

## Future Considerations

1. **Complete Direct Implementation**: Consider moving all table-related code to each component that needs it, making components more self-contained.
2. **Standardized Table Components**: Create a dedicated module for table components that builds on top of grid utilities.
3. **Complete Removal**: In a future release, completely remove the deprecated grid template functions once all usages have been migrated.

## Testing Guidelines

After any future changes to table components, ensure:

1. Tables render correctly on mobile devices
2. Sorting, filtering, and pagination work as expected
3. Interactive elements (editable cells, buttons) have proper visual feedback
4. Accessibility features are maintained

## References

1. [Import Organization Conventions](../conventions/imports.md)
2. [Deprecated Functions Migration Plan](../../todo.md)
