# Icon Generation Script
# Creates professional icon for the Burndown Chart application

# Requirements:
# pip install pillow

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_placeholder_icon():
    """
    Create modern burndown chart icon for Windows executable and web.

    Creates a 256x256 icon with:
    - Gradient blue background (#0d6efd to darker blue)
    - Clean white chart bars with subtle shadow
    - Smooth trend line showing burndown progress
    - Dashed target line
    - Professional rounded corners
    - Optimized for multiple resolutions (16x16 to 256x256)

    Design Philosophy: Simple, recognizable, scales well at small sizes.
    """
    # Icon size (Windows standard)
    size = 256

    # Create image with gradient blue background
    img = Image.new("RGBA", (size, size), color=(13, 110, 253, 255))
    draw = ImageDraw.Draw(img)

    # Add subtle gradient from top to bottom
    for y in range(size):
        gradient_factor = y / size
        r = int(13 * (1 - gradient_factor * 0.3))
        g = int(110 * (1 - gradient_factor * 0.3))
        b = int(253 * (1 - gradient_factor * 0.1))
        draw.rectangle([0, y, size, y + 1], fill=(r, g, b, 255))

    # Add rounded corners for modern look
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=32, fill=255)
    img.putalpha(mask)

    # Chart dimensions - well-balanced for visibility
    margin = 45
    chart_width = size - 2 * margin
    chart_height = size - 2 * margin

    # Bar configuration - 5 bars showing clear burndown
    num_bars = 5
    bar_width = 28
    spacing = (chart_width - num_bars * bar_width) / (num_bars + 1)

    # Heights with dramatic burndown curve
    max_bar_height = chart_height * 0.75
    bar_heights = [
        max_bar_height * 1.0,  # Full height
        max_bar_height * 0.78,  # Slight decline
        max_bar_height * 0.55,  # Steeper decline
        max_bar_height * 0.32,  # Approaching target
        max_bar_height * 0.15,  # Near completion
    ]

    # Subtle opacity variation for depth
    opacities = [0.98, 0.96, 0.94, 0.92, 0.90]

    trend_points = []

    # Draw bars with subtle shadow for depth
    for i in range(num_bars):
        x = margin + spacing + i * (bar_width + spacing)
        height = bar_heights[i]
        y = margin + (chart_height - height)

        # Shadow effect (subtle dark bar offset)
        shadow_offset = 2
        shadow_alpha = 40
        draw.rectangle(
            [
                x + shadow_offset,
                y + shadow_offset,
                x + bar_width + shadow_offset,
                y + height + shadow_offset,
            ],
            fill=(0, 0, 0, shadow_alpha),
        )

        # Main bar with high opacity for clarity
        alpha = int(255 * opacities[i])
        bar_color = (255, 255, 255, alpha)
        draw.rectangle([x, y, x + bar_width, y + height], fill=bar_color)

        # Store center point for trend line
        trend_points.append((x + bar_width / 2, y))

    # Draw smooth trend line connecting bar tops
    draw.line(trend_points, fill=(255, 255, 255, 250), width=5, joint="curve")

    # Draw target line (dashed diagonal)
    start_x, start_y = margin, margin + chart_height * 0.05
    end_x, end_y = size - margin, size - margin * 0.85
    segments = 20
    for i in range(0, segments, 2):
        x1 = start_x + (end_x - start_x) * i / segments
        y1 = start_y + (end_y - start_y) * i / segments
        x2 = start_x + (end_x - start_x) * (i + 1) / segments
        y2 = start_y + (end_y - start_y) * (i + 1) / segments
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 220), width=4)

    # Save as multiple sizes for Windows icon
    output_dir = Path(__file__).parent.parent / "assets"
    output_dir.mkdir(exist_ok=True)

    # Save as PNG (high quality for reference)
    png_path = output_dir / "icon.png"
    img.save(png_path, format="PNG", optimize=True)
    print(f"✓ Created PNG icon: {png_path}")

    # Create ICO with multiple sizes for Windows
    ico_path = output_dir / "icon.ico"
    icon_sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    images = [img.resize(size, Image.Resampling.LANCZOS) for size in icon_sizes]
    images[0].save(ico_path, format="ICO", sizes=icon_sizes, append_images=images[1:])
    print(f"✓ Created ICO icon: {ico_path}")

    print("\n✓ Icon generation complete!")
    print("  Design: Modern burndown chart with gradient background")
    print("  Sizes: 16x16, 32x32, 48x48, 256x256")
    print("  Features: Subtle shadows, smooth trend line, professional look")


if __name__ == "__main__":
    create_placeholder_icon()
