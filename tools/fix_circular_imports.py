"""
Circular Import Fixer

This script helps implement suggested fixes for circular imports by:
1. Identifying function-level imports that can be converted to runtime imports
2. Creating extraction candidates for common functionality
"""

import os
import re
import sys
from pathlib import Path
import ast


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to find import statements."""

    def __init__(self):
        self.imports = []
        self.runtime_import_candidates = []

    def visit_Import(self, node):
        """Visit import statements."""
        for name in node.names:
            self.imports.append((name.name, node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Visit from...import statements."""
        for name in node.names:
            self.imports.append((f"{node.module}.{name.name}", node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        for child in node.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                if isinstance(child, ast.Import):
                    for name in child.names:
                        self.runtime_import_candidates.append(
                            {
                                "function": node.name,
                                "import": name.name,
                                "line": child.lineno,
                            }
                        )
                else:
                    for name in child.names:
                        self.runtime_import_candidates.append(
                            {
                                "function": node.name,
                                "import": f"{child.module}.{name.name}",
                                "line": child.lineno,
                            }
                        )
        self.generic_visit(node)


def find_circular_dependencies(module1, module2):
    """
    Check if two modules have circular dependencies by examining their imports.

    Args:
        module1: Path to first module
        module2: Path to second module

    Returns:
        Tuple of (is_circular, details)
    """
    # Parse module 1
    with open(module1, "r", encoding="utf-8") as f:
        module1_content = f.read()

    module1_ast = ast.parse(module1_content)
    visitor1 = ImportVisitor()
    visitor1.visit(module1_ast)

    # Parse module 2
    with open(module2, "r", encoding="utf-8") as f:
        module2_content = f.read()

    module2_ast = ast.parse(module2_content)
    visitor2 = ImportVisitor()
    visitor2.visit(module2_ast)

    # Check if module1 imports module2
    module2_name = Path(module2).stem
    module1_imports_module2 = any(module2_name in imp for imp, _ in visitor1.imports)

    # Check if module2 imports module1
    module1_name = Path(module1).stem
    module2_imports_module1 = any(module1_name in imp for imp, _ in visitor2.imports)

    # If both import each other, it's circular
    is_circular = module1_imports_module2 and module2_imports_module1

    details = {
        "module1": {
            "name": module1_name,
            "imports": visitor1.imports,
            "runtime_candidates": visitor1.runtime_import_candidates,
        },
        "module2": {
            "name": module2_name,
            "imports": visitor2.imports,
            "runtime_candidates": visitor2.runtime_import_candidates,
        },
    }

    return is_circular, details


def suggest_function_level_imports(module_path):
    """
    Analyze a module and suggest imports that could be moved to function level.

    Args:
        module_path: Path to the module file

    Returns:
        List of suggestions for moving imports
    """
    with open(module_path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    visitor = ImportVisitor()
    visitor.visit(tree)

    # Identify import statements and their usages
    import_usages = {}

    class ImportUsageVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                name = node.id
                for imp, _ in visitor.imports:
                    # Check if this name corresponds to an import
                    if name == imp or name == imp.split(".")[-1]:
                        if imp not in import_usages:
                            import_usages[imp] = []
                        import_usages[imp].append(node.lineno)
            self.generic_visit(node)

    usage_visitor = ImportUsageVisitor()
    usage_visitor.visit(tree)

    # Identify imports that are only used within certain functions
    function_imports = {}

    class FunctionDefVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            # Get the line number range of this function
            start_line = node.lineno
            end_line = max(
                child.lineno for child in ast.walk(node) if hasattr(child, "lineno")
            )

            # Check which imports are used only within this function
            for imp, usages in import_usages.items():
                if all(start_line <= usage <= end_line for usage in usages):
                    if node.name not in function_imports:
                        function_imports[node.name] = []
                    function_imports[node.name].append(imp)

            self.generic_visit(node)

    func_visitor = FunctionDefVisitor()
    func_visitor.visit(tree)

    # Generate suggestions
    suggestions = []
    for func_name, imports in function_imports.items():
        for imp in imports:
            suggestions.append(
                f"Move import '{imp}' to function level in '{func_name}'"
            )

    return suggestions


def find_common_functionality(module1, module2):
    """
    Analyze two modules to find potential common functionality that could be extracted.

    Args:
        module1: Path to first module
        module2: Path to second module

    Returns:
        List of suggestions for extracting common functionality
    """
    # Parse modules
    with open(module1, "r", encoding="utf-8") as f:
        module1_content = f.read()

    with open(module2, "r", encoding="utf-8") as f:
        module2_content = f.read()

    module1_tree = ast.parse(module1_content)
    module2_tree = ast.parse(module2_content)

    # Get function and class names
    module1_functions = [
        node.name for node in module1_tree.body if isinstance(node, ast.FunctionDef)
    ]
    module1_classes = [
        node.name for node in module1_tree.body if isinstance(node, ast.ClassDef)
    ]

    module2_functions = [
        node.name for node in module2_tree.body if isinstance(node, ast.FunctionDef)
    ]
    module2_classes = [
        node.name for node in module2_tree.body if isinstance(node, ast.ClassDef)
    ]

    # Find similar names
    similar_functions = []
    for func1 in module1_functions:
        for func2 in module2_functions:
            similarity = len(set(func1.lower()) & set(func2.lower())) / max(
                len(func1), len(func2)
            )
            if similarity > 0.7:  # 70% similarity threshold
                similar_functions.append((func1, func2))

    similar_classes = []
    for class1 in module1_classes:
        for class2 in module2_classes:
            similarity = len(set(class1.lower()) & set(class2.lower())) / max(
                len(class1), len(class2)
            )
            if similarity > 0.7:  # 70% similarity threshold
                similar_classes.append((class1, class2))

    # Generate suggestions
    suggestions = []

    if similar_functions:
        suggestions.append(
            "Consider extracting these similar functions to a common module:"
        )
        for func1, func2 in similar_functions:
            suggestions.append(
                f"  - {func1} from {Path(module1).name} and {func2} from {Path(module2).name}"
            )

    if similar_classes:
        suggestions.append(
            "Consider extracting these similar classes to a common module:"
        )
        for class1, class2 in similar_classes:
            suggestions.append(
                f"  - {class1} from {Path(module1).name} and {class2} from {Path(module2).name}"
            )

    return suggestions


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python fix_circular_imports.py function-imports <module_path>")
        print(
            "  python fix_circular_imports.py extract-common <module1_path> <module2_path>"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "function-imports":
        module_path = sys.argv[2]
        suggestions = suggest_function_level_imports(module_path)

        if suggestions:
            print(f"Suggestions for {module_path}:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        else:
            print(f"No function-level import suggestions for {module_path}")

    elif command == "extract-common":
        if len(sys.argv) < 4:
            print("Error: Two module paths required for extract-common")
            sys.exit(1)

        module1 = sys.argv[2]
        module2 = sys.argv[3]

        is_circular, details = find_circular_dependencies(module1, module2)

        if is_circular:
            print(
                f"Circular dependency confirmed between {Path(module1).name} and {Path(module2).name}"
            )

            # Check for runtime import candidates
            if details["module1"]["runtime_candidates"]:
                print(f"\nRuntime import candidates in {Path(module1).name}:")
                for candidate in details["module1"]["runtime_candidates"]:
                    print(
                        f"  - Function: {candidate['function']}, Import: {candidate['import']}"
                    )

            if details["module2"]["runtime_candidates"]:
                print(f"\nRuntime import candidates in {Path(module2).name}:")
                for candidate in details["module2"]["runtime_candidates"]:
                    print(
                        f"  - Function: {candidate['function']}, Import: {candidate['import']}"
                    )

            # Check for common functionality
            suggestions = find_common_functionality(module1, module2)
            if suggestions:
                print("\nSuggestions for extracting common functionality:")
                for suggestion in suggestions:
                    print(f"  {suggestion}")
        else:
            print(
                f"No circular dependency detected between {Path(module1).name} and {Path(module2).name}"
            )


if __name__ == "__main__":
    main()
