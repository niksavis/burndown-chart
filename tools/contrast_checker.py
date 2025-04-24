"""
Color Contrast Checker

This tool checks color contrast ratios according to WCAG 2.1 AA standards.
It can analyze CSS files or be used to check specific color combinations.
"""

import re
import sys
import os
import math
from pathlib import Path
import colorsys
from typing import Tuple, Dict, List, Optional, Union


def parse_color(color: str) -> Tuple[float, float, float]:
    """
    Parse a CSS color string into RGB values (0-1).

    Supports hex colors, rgb(), and rgba() formats.
    """
    color = color.strip().lower()

    # Handle named colors
    named_colors = {
        "black": (0, 0, 0),
        "white": (1, 1, 1),
        "red": (1, 0, 0),
        "green": (0, 0.5, 0),
        "blue": (0, 0, 1),
        "yellow": (1, 1, 0),
        # Add more named colors as needed
    }

    if color in named_colors:
        return named_colors[color]

    # Handle hex format
    if color.startswith("#"):
        if len(color) == 4:  # Short hex (#rgb)
            r = int(color[1] + color[1], 16) / 255
            g = int(color[2] + color[2], 16) / 255
            b = int(color[3] + color[3], 16) / 255
        else:  # Full hex (#rrggbb)
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
        return (r, g, b)

    # Handle rgb/rgba format
    if color.startswith("rgb"):
        match = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color)
        if match:
            r = int(match.group(1)) / 255
            g = int(match.group(2)) / 255
            b = int(match.group(3)) / 255
            return (r, g, b)

    # Default to black if parsing fails
    print(f"Warning: Could not parse color '{color}', using black")
    return (0, 0, 0)


def get_luminance(color: Tuple[float, float, float]) -> float:
    """
    Calculate the relative luminance of a color according to WCAG 2.1.

    Args:
        color: RGB color values as floats between 0-1

    Returns:
        Relative luminance value
    """

    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = color
    r, g, b = adjust(r), adjust(g), adjust(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(
    color1: Tuple[float, float, float], color2: Tuple[float, float, float]
) -> float:
    """
    Calculate contrast ratio between two colors according to WCAG 2.1.

    Args:
        color1: First RGB color as floats between 0-1
        color2: Second RGB color as floats between 0-1

    Returns:
        Contrast ratio between 1:1 and 21:1
    """
    lum1 = get_luminance(color1)
    lum2 = get_luminance(color2)

    # Ensure lighter color is first for the formula
    if lum1 < lum2:
        lum1, lum2 = lum2, lum1

    # Calculate contrast ratio
    return (lum1 + 0.05) / (lum2 + 0.05)


def check_wcag_compliance(ratio: float) -> Dict[str, bool]:
    """
    Check if a contrast ratio complies with WCAG standards.

    Args:
        ratio: Contrast ratio between 1:1 and 21:1

    Returns:
        Dictionary with compliance status for different WCAG criteria
    """
    return {
        "AA_normal_text": ratio >= 4.5,
        "AA_large_text": ratio >= 3.0,
        "AAA_normal_text": ratio >= 7.0,
        "AAA_large_text": ratio >= 4.5,
    }


def find_colors_in_css(css_file: str) -> Dict[str, List[str]]:
    """
    Extract color declarations from a CSS file.

    Args:
        css_file: Path to the CSS file

    Returns:
        Dictionary mapping selectors to lists of color properties
    """
    colors = {}

    with open(css_file, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Find all color declarations (simplified regex)
    color_pattern = re.compile(
        r"([^{]+)\s*{[^}]*(color|background-color|border-color|fill|stroke):\s*([^;}]+)",
        re.DOTALL,
    )

    for match in color_pattern.finditer(css_content):
        selector = match.group(1).strip()
        property_name = match.group(2)
        color_value = match.group(3).strip()

        if selector not in colors:
            colors[selector] = []

        colors[selector].append({"property": property_name, "value": color_value})

    return colors


def generate_contrast_report(css_file: str) -> List[Dict]:
    """
    Generate a report of potential contrast issues in a CSS file.

    Args:
        css_file: Path to the CSS file

    Returns:
        List of contrast issues
    """
    color_map = find_colors_in_css(css_file)
    issues = []

    # This is a simplified analysis that identifies potential issues
    # A more comprehensive analysis would require parsing the DOM structure
    for selector, properties in color_map.items():
        text_colors = [p["value"] for p in properties if p["property"] == "color"]
        bg_colors = [
            p["value"] for p in properties if p["property"] == "background-color"
        ]

        # If we have both text color and background color in same selector
        if text_colors and bg_colors:
            for text_color in text_colors:
                for bg_color in bg_colors:
                    try:
                        rgb_text = parse_color(text_color)
                        rgb_bg = parse_color(bg_color)
                        ratio = calculate_contrast_ratio(rgb_text, rgb_bg)
                        compliance = check_wcag_compliance(ratio)

                        if not compliance["AA_normal_text"]:
                            issues.append(
                                {
                                    "selector": selector,
                                    "text_color": text_color,
                                    "background_color": bg_color,
                                    "ratio": ratio,
                                    "compliance": compliance,
                                }
                            )
                    except Exception as e:
                        issues.append(
                            {
                                "selector": selector,
                                "error": str(e),
                                "text_color": text_color,
                                "background_color": bg_color,
                            }
                        )

    return issues


def interactive_color_check() -> None:
    """Run an interactive color contrast checker."""
    print("Color Contrast Checker")
    print("Enter colors in hex (#RRGGBB), rgb(r,g,b), or color names.")
    print("Type 'exit' to quit.")

    while True:
        foreground = input("\nForeground color: ")
        if foreground.lower() == "exit":
            break

        background = input("Background color: ")
        if background.lower() == "exit":
            break

        try:
            rgb_fg = parse_color(foreground)
            rgb_bg = parse_color(background)
            ratio = calculate_contrast_ratio(rgb_fg, rgb_bg)
            compliance = check_wcag_compliance(ratio)

            print(f"\nContrast ratio: {ratio:.2f}:1")
            print(
                f"WCAG 2.1 AA Normal text: {'✓' if compliance['AA_normal_text'] else '✗'}"
            )
            print(
                f"WCAG 2.1 AA Large text: {'✓' if compliance['AA_large_text'] else '✗'}"
            )
            print(
                f"WCAG 2.1 AAA Normal text: {'✓' if compliance['AAA_normal_text'] else '✗'}"
            )
            print(
                f"WCAG 2.1 AAA Large text: {'✓' if compliance['AAA_large_text'] else '✗'}"
            )
        except Exception as e:
            print(f"Error: {e}")


def main() -> None:
    """Main entry point"""
    if len(sys.argv) == 1:
        interactive_color_check()
        return

    if len(sys.argv) < 2:
        print("Usage: python contrast_checker.py [css_file]")
        return

    css_file = sys.argv[1]
    if not os.path.exists(css_file):
        print(f"Error: File {css_file} not found")
        return

    print(f"Analyzing {css_file} for contrast issues...")
    issues = generate_contrast_report(css_file)

    if not issues:
        print("No contrast issues found!")
        return

    print(f"Found {len(issues)} potential contrast issues:")
    for i, issue in enumerate(issues, 1):
        print(f"\nIssue #{i}:")
        print(f"  Selector: {issue['selector']}")

        if "error" in issue:
            print(f"  Error: {issue['error']}")
            continue

        print(f"  Text color: {issue['text_color']}")
        print(f"  Background color: {issue['background_color']}")
        print(f"  Contrast ratio: {issue['ratio']:.2f}:1")
        print(
            f"  AA Compliant: {'No' if not issue['compliance']['AA_normal_text'] else 'Yes'}"
        )

    print("\nNote: This is an automated check and may not catch all issues.")
    print("Manual testing is still recommended.")


if __name__ == "__main__":
    main()
