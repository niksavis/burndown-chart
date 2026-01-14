# Icon Generation Script
# Creates a simple placeholder icon for the Burndown Chart application

# Requirements:
# pip install pillow

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_placeholder_icon():
    """
    Create icon matching the favicon design for the Burndown Chart application.

    Creates a 256x256 icon with:
    - Blue background (#0d6efd - matching favicon)
    - White chart bars decreasing in height
    - White trend line and target line
    - Rounded corners for modern look
    - Suitable for Windows executable

    Matches the design from assets/favicon.svg
    """
    # Icon size (Windows standard)
    size = 256

    # Create image with blue background matching favicon (#0d6efd)
    img = Image.new("RGBA", (size, size), color=(13, 110, 253, 255))
    draw = ImageDraw.Draw(img)

    # Add rounded corners
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=32, fill=255)
    img.putalpha(mask)

    # Draw chart bars (decreasing height from left to right)
    # Centered and larger for better visibility
    margin = 40  # Margin from edges
    chart_width = size - 2 * margin
    chart_height = size - 2 * margin

    # Bar dimensions - 5 bars with spacing
    num_bars = 5
    bar_width = 24
    spacing = (chart_width - num_bars * bar_width) / (num_bars + 1)

    # Heights decrease from left to right (burndown effect)
    max_bar_height = chart_height * 0.7
    bar_heights = [
        max_bar_height * 0.95,
        max_bar_height * 0.80,
        max_bar_height * 0.60,
        max_bar_height * 0.40,
        max_bar_height * 0.25,
    ]

    # Opacity values for depth
    opacities = [0.95, 0.90, 0.85, 0.80, 0.75]

    bar_positions = []
    trend_points = []

    for i in range(num_bars):
        x = margin + spacing + i * (bar_width + spacing)
        height = bar_heights[i]
        y = margin + (chart_height - height)

        # Draw white bars with varying opacity
        alpha = int(255 * opacities[i])
        bar_color = (255, 255, 255, alpha)
        draw.rectangle([x, y, x + bar_width, y + height], fill=bar_color)

        # Store position for trend line
        trend_points.append((x + bar_width / 2, y))

    # Draw trend line (connecting top of bars) with thicker stroke
    draw.line(trend_points, fill=(255, 255, 255, 240), width=4)

    # Draw target line (dashed diagonal from top-left to bottom-right of chart area)
    start_x, start_y = margin, margin + chart_height * 0.1
    end_x, end_y = size - margin, size - margin * 0.8
    segments = 24
    for i in range(0, segments, 2):  # Draw every other segment for dashed effect
        x1 = start_x + (end_x - start_x) * i / segments
        y1 = start_y + (end_y - start_y) * i / segments
        x2 = start_x + (end_x - start_x) * (i + 1) / segments
        y2 = start_y + (end_y - start_y) * (i + 1) / segments
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 200), width=3)

    # Save as multiple sizes for Windows icon
    output_dir = Path(__file__).parent.parent / "assets"
    output_dir.mkdir(exist_ok=True)

    # Save as PNG first (for easier editing)
    png_path = output_dir / "icon.png"
    img.save(png_path, format="PNG")
    print(f"Created PNG icon: {png_path}")

    # Create ICO with multiple sizes
    ico_path = output_dir / "icon.ico"
    icon_sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    images = [img.resize(size, Image.Resampling.LANCZOS) for size in icon_sizes]
    images[0].save(ico_path, format="ICO", sizes=icon_sizes, append_images=images[1:])
    print(f"Created ICO icon: {ico_path}")

    print("\nIcon generation complete!")
    print(
        "Icon design matches favicon.svg (blue background with burndown chart visualization)"
    )


if __name__ == "__main__":
    create_placeholder_icon()
