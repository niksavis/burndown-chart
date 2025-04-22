# Import Organization Conventions

## Standard Import Order

All Python files in the project should follow this import order:

1. **Standard Library Imports**
   - Python's built-in modules
   - Grouped by functionality if there are many
   - Alphabetized within groups

2. **Third-Party Library Imports**
   - External dependencies (installed via pip)
   - Core packages first (dash, pandas, etc.)
   - Alphabetized within groups
   - Use explicit imports where practical (`from dash import html, dcc`)

3. **Application Imports**
   - Project modules and packages
   - Organized from most general to most specific
   - Configuration/settings imports first
   - Utility modules next
   - Feature-specific imports last

## Example

```python
#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import os
import sys
from datetime import datetime, timedelta
import json
import warnings

# Third-party library imports
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

# Application imports
from configuration import COLOR_PALETTE, SETTINGS
from ui.styles import get_color, SPACING, TYPOGRAPHY
from ui.icon_utils import create_icon, get_icon_class
from ui.button_utils import create_button
```

## Import Statement Formatting

- Separate the three sections with a blank line
- Within each section, group related imports together
- Sort imports alphabetically within groups
- Use explicit imports instead of wildcard imports (`from module import *`)
- Prefer using `from module import specific_thing` for frequently used components

## Import Section Header

For clarity, especially in larger files, use a comment header to mark the imports section:

```python
#######################################################################
# IMPORTS
#######################################################################
```

## Circular Imports

To avoid circular imports:

1. Use function-level imports for circular dependencies
2. Import only what is needed for type hinting at the module level
3. For utility functions that need to import from each other, consider consolidating them

## Deprecation Strategy

When refactoring imports:

1. Add deprecation warnings for relocated functions
2. Update imports in the module that defines the function first
3. Then update imports in modules that use the function

## Testing Imports

After refactoring imports, ensure:

1. No circular imports occur
2. All imports resolve correctly
3. The application runs without import errors
