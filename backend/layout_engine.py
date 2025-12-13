"""
Layout Suggestion Engine - Rule-based creative composition
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
import logging

from backend.config import CREATIVE_FORMATS, SAFE_ZONE_MARGIN
from backend.utils import get_safe_zone, resize_image_to_fit

logger = logging.getLogger(__name__)


class LayoutEngine:
    """Handles creative layout composition with rule-based logic"""
    
    def __init__(self):
        """Initialize layout engine"""
        self.font_cache = {}
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font with caching"""
        cache_key = (size, bold)
        if cache_key not in self.font_cache:
            try:
                # Try to load a system font
                if bold:
                    font_path = "arialbd.ttf"  # Windows
                else:
                    font_path = "arial.ttf"  # Windows
                self.font_cache[cache_key] = ImageFont.truetype(font_path, size)
            except:
                # Fallback to default font
                self.font_cache[cache_key] = ImageFont.load_default()
        return self.font_cache[cache_key]
    
    def suggest_layout(
        self,
        format_name: str,
        packshot: Image.Image,
        background: Optional[Image.Image] = None,
        headline: Optional[str] = None,
        price: Optional[str] = None,
        claim: Optional[str] = None,
        logo: Optional[Image.Image] = None
    ) -> Image.Image:
        """
        Create a suggested layout for the creative
        
        Args:
            format_name: Creative format ("1:1", "4:5", "9:16")
            packshot: Packshot image (with transparent background)
            background: Optional background image
            headline: Headline text
            price: Price text
            claim: Claim text
            logo: Optional logo image
        
        Returns:
            Composed PIL Image
        """
        # Get canvas dimensions
        if format_name not in CREATIVE_FORMATS:
            raise ValueError(f"Unknown format: {format_name}")
        
        canvas_width, canvas_height = CREATIVE_FORMATS[format_name]
        
        # Create canvas
        canvas = Image.new('RGB', (canvas_width, canvas_height), color=(255, 255, 255))
        
        # Add background if provided
        if background:
            bg_resized = resize_image_to_fit(background, canvas_width, canvas_height)
            # Center background
            bg_x = (canvas_width - bg_resized.width) // 2
            bg_y = (canvas_height - bg_resized.height) // 2
            canvas.paste(bg_resized, (bg_x, bg_y))
        
        # Get safe zone
        safe_zone = get_safe_zone(
            canvas_width,
            canvas_height,
            SAFE_ZONE_MARGIN["horizontal"],
            SAFE_ZONE_MARGIN["vertical"]
        )
        
        # Layout strategy based on format
        if format_name == "9:16":
            # Vertical format - stack elements
            layout = self._layout_vertical(
                canvas, packshot, safe_zone, headline, price, claim, logo
            )
        else:
            # Square/horizontal - use balanced layout
            layout = self._layout_balanced(
                canvas, packshot, safe_zone, headline, price, claim, logo
            )
        
        return layout
    
    def _layout_vertical(
        self,
        canvas: Image.Image,
        packshot: Image.Image,
        safe_zone: Dict,
        headline: Optional[str],
        price: Optional[str],
        claim: Optional[str],
        logo: Optional[Image.Image]
    ) -> Image.Image:
        """Layout for vertical (9:16) format"""
        draw = ImageDraw.Draw(canvas)
        canvas_width, canvas_height = canvas.size
        
        # Calculate available space
        available_height = safe_zone["y_max"] - safe_zone["y_min"]
        available_width = safe_zone["x_max"] - safe_zone["x_min"]
        
        # Position packshot in upper-middle area
        packshot_max_height = int(available_height * 0.5)
        packshot_resized = resize_image_to_fit(packshot, available_width, packshot_max_height)
        
        packshot_x = (canvas_width - packshot_resized.width) // 2
        packshot_y = safe_zone["y_min"] + 50
        
        # Paste packshot with alpha channel
        if packshot.mode == 'RGBA':
            canvas.paste(packshot_resized, (packshot_x, packshot_y), packshot_resized.split()[3])
        else:
            canvas.paste(packshot_resized, (packshot_x, packshot_y))
        
        # Position text below packshot
        text_y = packshot_y + packshot_resized.height + 40
        
        # Headline
        if headline:
            font_size = min(48, int(canvas_width * 0.045))
            font = self._get_font(font_size, bold=True)
            text_bbox = draw.textbbox((0, 0), headline, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (canvas_width - text_width) // 2
            draw.text((text_x, text_y), headline, fill=(0, 0, 0), font=font)
            text_y += font_size + 20
        
        # Price
        if price:
            font_size = min(56, int(canvas_width * 0.052))
            font = self._get_font(font_size, bold=True)
            text_bbox = draw.textbbox((0, 0), price, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (canvas_width - text_width) // 2
            draw.text((text_x, text_y), price, fill=(220, 20, 60), font=font)  # Red color
            text_y += font_size + 20
        
        # Claim
        if claim:
            font_size = min(32, int(canvas_width * 0.03))
            font = self._get_font(font_size)
            text_bbox = draw.textbbox((0, 0), claim, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (canvas_width - text_width) // 2
            draw.text((text_x, text_y), claim, fill=(50, 50, 50), font=font)
        
        # Logo in bottom right
        if logo:
            logo_size = min(100, int(canvas_width * 0.15))
            logo_resized = resize_image_to_fit(logo, logo_size, logo_size)
            logo_x = safe_zone["x_max"] - logo_resized.width - 20
            logo_y = safe_zone["y_max"] - logo_resized.height - 20
            
            if logo.mode == 'RGBA':
                canvas.paste(logo_resized, (logo_x, logo_y), logo_resized.split()[3])
            else:
                canvas.paste(logo_resized, (logo_x, logo_y))
        
        return canvas
    
    def _layout_balanced(
        self,
        canvas: Image.Image,
        packshot: Image.Image,
        safe_zone: Dict,
        headline: Optional[str],
        price: Optional[str],
        claim: Optional[str],
        logo: Optional[Image.Image]
    ) -> Image.Image:
        """Layout for square/horizontal formats"""
        draw = ImageDraw.Draw(canvas)
        canvas_width, canvas_height = canvas.size
        
        # Calculate available space
        available_height = safe_zone["y_max"] - safe_zone["y_min"]
        available_width = safe_zone["x_max"] - safe_zone["x_min"]
        
        # Packshot takes 60% of available width, positioned left-center
        packshot_max_width = int(available_width * 0.6)
        packshot_max_height = int(available_height * 0.8)
        packshot_resized = resize_image_to_fit(packshot, packshot_max_width, packshot_max_height)
        
        packshot_x = safe_zone["x_min"] + 30
        packshot_y = (canvas_height - packshot_resized.height) // 2
        
        # Paste packshot
        if packshot.mode == 'RGBA':
            canvas.paste(packshot_resized, (packshot_x, packshot_y), packshot_resized.split()[3])
        else:
            canvas.paste(packshot_resized, (packshot_x, packshot_y))
        
        # Text area on the right
        text_area_x = packshot_x + packshot_resized.width + 40
        text_area_width = safe_zone["x_max"] - text_area_x
        text_y = safe_zone["y_min"] + 50
        
        # Headline
        if headline:
            font_size = min(42, int(canvas_width * 0.04))
            font = self._get_font(font_size, bold=True)
            # Word wrap
            words = headline.split()
            lines = []
            current_line = []
            current_width = 0
            
            for word in words:
                word_bbox = draw.textbbox((0, 0), word + " ", font=font)
                word_width = word_bbox[2] - word_bbox[0]
                if current_width + word_width > text_area_width and current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            
            if current_line:
                lines.append(" ".join(current_line))
            
            for line in lines:
                draw.text((text_area_x, text_y), line, fill=(0, 0, 0), font=font)
                text_y += font_size + 10
        
        # Price
        if price:
            text_y += 20
            font_size = min(52, int(canvas_width * 0.05))
            font = self._get_font(font_size, bold=True)
            draw.text((text_area_x, text_y), price, fill=(220, 20, 60), font=font)
            text_y += font_size + 20
        
        # Claim
        if claim:
            font_size = min(28, int(canvas_width * 0.026))
            font = self._get_font(font_size)
            # Word wrap for claim
            words = claim.split()
            lines = []
            current_line = []
            current_width = 0
            
            for word in words:
                word_bbox = draw.textbbox((0, 0), word + " ", font=font)
                word_width = word_bbox[2] - word_bbox[0]
                if current_width + word_width > text_area_width and current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            
            if current_line:
                lines.append(" ".join(current_line))
            
            for line in lines:
                draw.text((text_area_x, text_y), line, fill=(50, 50, 50), font=font)
                text_y += font_size + 8
        
        # Logo in bottom right
        if logo:
            logo_size = min(80, int(canvas_width * 0.12))
            logo_resized = resize_image_to_fit(logo, logo_size, logo_size)
            logo_x = safe_zone["x_max"] - logo_resized.width - 20
            logo_y = safe_zone["y_max"] - logo_resized.height - 20
            
            if logo.mode == 'RGBA':
                canvas.paste(logo_resized, (logo_x, logo_y), logo_resized.split()[3])
            else:
                canvas.paste(logo_resized, (logo_x, logo_y))
        
        return canvas

