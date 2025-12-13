"""
Utility functions for TESCORA.AI backend
"""
import os
from pathlib import Path
from PIL import Image
import numpy as np
import cv2


def ensure_dir(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_safe_zone(canvas_width: int, canvas_height: int, margin_h: float = 0.1, margin_v: float = 0.1):
    """
    Calculate safe zone boundaries
    
    Args:
        canvas_width: Width of the canvas
        canvas_height: Height of the canvas
        margin_h: Horizontal margin as percentage (default 0.1 = 10%)
        margin_v: Vertical margin as percentage (default 0.1 = 10%)
    
    Returns:
        dict with x_min, x_max, y_min, y_max
    """
    x_min = int(canvas_width * margin_h)
    x_max = int(canvas_width * (1 - margin_h))
    y_min = int(canvas_height * margin_v)
    y_max = int(canvas_height * (1 - margin_v))
    
    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
    }


def calculate_contrast_ratio(color1: tuple, color2: tuple) -> float:
    """
    Calculate contrast ratio between two colors (WCAG standard)
    
    Args:
        color1: RGB tuple (0-255)
        color2: RGB tuple (0-255)
    
    Returns:
        Contrast ratio (1-21)
    """
    def get_luminance(rgb):
        """Calculate relative luminance"""
        r, g, b = [c / 255.0 for c in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    l1 = get_luminance(color1)
    l2 = get_luminance(color2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def resize_image_to_fit(image: Image.Image, max_width: int, max_height: int, maintain_aspect: bool = True) -> Image.Image:
    """
    Resize image to fit within dimensions
    
    Args:
        image: PIL Image
        max_width: Maximum width
        max_height: Maximum height
        maintain_aspect: Whether to maintain aspect ratio
    
    Returns:
        Resized PIL Image
    """
    if maintain_aspect:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    else:
        image = image.resize((max_width, max_height), Image.Resampling.LANCZOS)
    return image


def compress_image(image: Image.Image, max_size_kb: int = 500, quality: int = 85) -> Image.Image:
    """
    Compress image to meet size requirements
    
    Args:
        image: PIL Image
        max_size_kb: Maximum size in KB
        quality: Initial JPEG quality (0-100)
    
    Returns:
        Compressed PIL Image
    """
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'LA', 'P'):
        # Create white background for transparency
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Try to compress
    import io
    output = io.BytesIO()
    current_quality = quality
    
    while current_quality > 10:
        output.seek(0)
        output.truncate(0)
        image.save(output, format='JPEG', quality=current_quality, optimize=True)
        size_kb = len(output.getvalue()) / 1024
        
        if size_kb <= max_size_kb:
            break
        
        current_quality -= 10
    
    # Reload from buffer
    output.seek(0)
    return Image.open(output)


def get_image_size_kb(image_path: Path) -> float:
    """Get image file size in KB"""
    return os.path.getsize(image_path) / 1024


def validate_file_size(image_path: Path, max_kb: int = 500):
    """
    Validate if image meets size requirements
    
    Returns:
        (is_valid, message)
    """
    size_kb = get_image_size_kb(image_path)
    if size_kb > max_kb:
        return False, f"Image size ({size_kb:.2f} KB) exceeds maximum ({max_kb} KB)"
    return True, f"Image size: {size_kb:.2f} KB"


def get_dominant_colors(image: Image.Image, k: int = 3) -> list:
    """
    Get dominant colors from image using k-means clustering
    
    Args:
        image: PIL Image
        k: Number of colors to extract
    
    Returns:
        List of RGB tuples
    """
    from sklearn.cluster import KMeans
    
    # Resize for faster processing
    image_small = image.resize((150, 150))
    image_array = np.array(image_small).reshape(-1, 3)
    
    # Remove alpha channel if present
    if image_array.shape[1] == 4:
        image_array = image_array[:, :3]
    
    # Cluster colors
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(image_array)
    
    colors = kmeans.cluster_centers_.astype(int)
    return [tuple(color) for color in colors]

