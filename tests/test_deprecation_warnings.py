import sys
import unittest
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))


class TestDeprecationRemoval(unittest.TestCase):
    def test_grid_templates_removed(self):
        with self.assertRaises(ImportError):
            import_module("ui.grid_templates")

    def test_no_grid_templates_references(self):
        import re

        root_dir = Path(__file__).parent.parent

        pattern = re.compile(
            r"from\s+ui\.grid_templates\s+import|import\s+ui\.grid_templates"
        )

        files_with_refs = []

        exclude_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules"}

        for path in root_dir.glob("**/*.py"):
            if any(x in str(path) for x in exclude_dirs):
                continue

            try:
                content = path.read_text(encoding="utf-8")
                if pattern.search(content):
                    files_with_refs.append(str(path))
            except UnicodeDecodeError:
                continue

        self.assertEqual(
            len(files_with_refs),
            0,
            f"Found references to grid_templates in: {', '.join(files_with_refs)}",
        )


if __name__ == "__main__":
    unittest.main()
