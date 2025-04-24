"""
Test script to verify the removal of deprecated code.

The grid_templates module has been completely removed, and this
test now verifies it doesn't exist anymore.
"""

import os
import sys
import importlib
import unittest
from pathlib import Path

# This ensures the tests can find the application modules
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))


class TestDeprecationRemoval(unittest.TestCase):
    """Tests to verify deprecated code has been removed."""
    
    def test_grid_templates_removed(self):
        """Test that grid_templates module no longer exists."""
        try:
            from ui import grid_templates
            self.fail("grid_templates.py should have been removed")
        except ImportError:
            # Expected behavior - module should be gone
            pass

    def test_no_grid_templates_references(self):
        """Test that there are no references to grid_templates in the codebase."""
        import re
        
        # Root directory of the project
        root_dir = Path(__file__).parent.parent
        
        # Pattern to search for
        pattern = re.compile(r'from\s+ui\.grid_templates\s+import|import\s+ui\.grid_templates')
        
        # Files with references to grid_templates
        files_with_refs = []
        
        # Directories to exclude
        exclude_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules'}
        
        # Search through all Python files
        for path in root_dir.glob('**/*.py'):
            # Skip excluded directories
            if any(x in str(path) for x in exclude_dirs):
                continue
                
            # Read file content
            try:
                content = path.read_text(encoding='utf-8')
                if pattern.search(content):
                    files_with_refs.append(str(path))
            except UnicodeDecodeError:
                continue
        
        # Assert no files have references
        self.assertEqual(len(files_with_refs), 0, 
                        f"Found references to grid_templates in: {', '.join(files_with_refs)}")


if __name__ == "__main__":
    unittest.main()