"""
Simple script to run unittest directly, bypassing VS Code test discovery issues.
"""

import unittest
import sys
from pathlib import Path

# Find all tests in the tests directory
test_dir = Path(__file__).parent.parent / "tests"
test_loader = unittest.TestLoader()
test_suite = test_loader.discover(str(test_dir), pattern="test_*.py")

# Run the tests
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(test_suite)

# Return non-zero exit code on failure for CI integration
sys.exit(0 if result.wasSuccessful() else 1)
