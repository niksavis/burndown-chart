"""
Import Analyzer Tool

This script analyzes the project's import structure to identify potential circular imports
and suggest fixes. It creates a dependency graph of modules and identifies cycles.
"""

import os
import re
import sys
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
from typing import List


def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the project directory tree."""
    return list(Path(root_dir).rglob("*.py"))


def extract_imports(file_path: Path) -> List[str]:
    """Extract import statements from a Python file."""
    imports = []
    import_re = re.compile(
        r"^(?:from\s+(\S+)\s+import.*|import\s+(\S+)(?:\s*,\s*(\S+))*)", re.MULTILINE
    )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    for match in import_re.finditer(content):
        # Handle 'from x import y'
        if match.group(1):
            imports.append(match.group(1))
        # Handle 'import x, y, z'
        else:
            for i in range(2, len(match.groups()) + 1):
                if match.group(i):
                    imports.append(match.group(i))

    return imports


def build_import_graph(files: List[Path]) -> nx.DiGraph:
    """Build a directed graph of module dependencies."""
    G = nx.DiGraph()

    # Map file paths to module names
    file_to_module = {}
    for file_path in files:
        rel_path = file_path.as_posix()
        module_name = rel_path.replace("/", ".").replace(".py", "")
        file_to_module[file_path] = module_name
        G.add_node(module_name)

    # Add edges for imports
    for file_path in files:
        source_module = file_to_module[file_path]
        imports = extract_imports(file_path)

        for imp in imports:
            # Only consider internal imports
            if any(
                imp == mod_name or mod_name.startswith(imp + ".")
                for mod_name in file_to_module.values()
            ):
                G.add_edge(source_module, imp)

    return G


def find_cycles(G: nx.DiGraph) -> List[List[str]]:
    """Find circular dependencies in the import graph."""
    try:
        cycles = list(nx.simple_cycles(G))
        return cycles
    except nx.NetworkXNoCycle:
        return []


def visualize_graph(G: nx.DiGraph, output_path: str) -> None:
    """Visualize the import graph."""
    plt.figure(figsize=(12, 8))
    nx.draw(G, with_labels=True, node_color="lightblue", node_size=500)
    plt.savefig(output_path)
    plt.close()


def suggest_fixes(cycles: List[List[str]]) -> List[str]:
    """Provide suggestions to fix circular imports."""
    suggestions = []

    for cycle in cycles:
        suggestions.append(
            f"Circular dependency found: {' -> '.join(cycle + [cycle[0]])}"
        )
        suggestions.append("Possible solutions:")
        suggestions.append("1. Use lazy/runtime imports in one of these modules")
        suggestions.append("2. Extract common functionality to a separate module")
        suggestions.append("3. Refactor the code to remove the dependency")
        suggestions.append("")

    return suggestions


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python analyze_imports.py <project_directory>")
        sys.exit(1)

    project_dir = sys.argv[1]
    python_files = find_python_files(project_dir)

    print(f"Found {len(python_files)} Python files in {project_dir}")

    # Build import graph
    import_graph = build_import_graph(python_files)

    # Find circular dependencies
    cycles = find_cycles(import_graph)

    # Print results
    if cycles:
        print(f"Found {len(cycles)} circular dependencies:")
        for cycle in cycles:
            print(f"  {' -> '.join(cycle + [cycle[0]])}")

        # Print suggestions
        print("\nSuggested fixes:")
        for suggestion in suggest_fixes(cycles):
            print(suggestion)

        # Visualize graph
        visualize_graph(import_graph, os.path.join(project_dir, "import_graph.png"))
        print(
            f"\nImport graph visualization saved to {os.path.join(project_dir, 'import_graph.png')}"
        )
    else:
        print("No circular dependencies found!")


if __name__ == "__main__":
    main()
