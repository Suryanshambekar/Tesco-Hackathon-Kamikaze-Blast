"""
Multi-format Export Engine
"""
from PIL import Image
from pathlib import Path
from typing import Dict, List
import logging

from backend.config import CREATIVE_FORMATS, MAX_FILE_SIZE_KB
from backend.utils import compress_image, validate_file_size
from backend.layout_engine import LayoutEngine

logger = logging.getLogger(__name__)


class ExportEngine:
    """Handles multi-format creative export"""
    
    def __init__(self):
        """Initialize export engine"""
        self.layout_engine = LayoutEngine()
    
    def export_creatives(
        self,
        packshot: Image.Image,
        background: Image.Image = None,
        headline: str = None,
        price: str = None,
        claim: str = None,
        logo: Image.Image = None,
        formats: List[str] = None,
        output_dir: Path = None
    ) -> Dict[str, Dict]:
        """
        Export creatives in multiple formats
        
        Args:
            packshot: Packshot image (with transparent background)
            background: Background image
            headline: Headline text
            price: Price text
            claim: Claim text
            logo: Logo image
            formats: List of format names to export (default: all)
            output_dir: Output directory
        
        Returns:
            Dictionary mapping format names to export results
        """
        if formats is None:
            formats = list(CREATIVE_FORMATS.keys())
        
        if output_dir is None:
            output_dir = Path("outputs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for format_name in formats:
            try:
                result = self._export_format(
                    format_name=format_name,
                    packshot=packshot,
                    background=background,
                    headline=headline,
                    price=price,
                    claim=claim,
                    logo=logo,
                    output_dir=output_dir
                )
                results[format_name] = result
            except Exception as e:
                logger.error(f"Error exporting format {format_name}: {e}")
                results[format_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def _export_format(
        self,
        format_name: str,
        packshot: Image.Image,
        background: Image.Image,
        headline: str,
        price: str,
        claim: str,
        logo: Image.Image,
        output_dir: Path
    ) -> Dict:
        """
        Export creative in a specific format
        
        Returns:
            Dictionary with export results
        """
        # Generate layout
        creative = self.layout_engine.suggest_layout(
            format_name=format_name,
            packshot=packshot,
            background=background,
            headline=headline,
            price=price,
            claim=claim,
            logo=logo
        )
        
        # Compress to meet size requirements
        creative_compressed = compress_image(creative, max_size_kb=MAX_FILE_SIZE_KB)
        
        # Generate filename
        filename = f"creative_{format_name.replace(':', '_')}.jpg"
        output_path = output_dir / filename
        
        # Save
        creative_compressed.save(output_path, format='JPEG', quality=85, optimize=True)
        
        # Validate size
        is_valid, size_message = validate_file_size(output_path, MAX_FILE_SIZE_KB)
        
        return {
            'success': True,
            'path': str(output_path),
            'format': format_name,
            'dimensions': creative_compressed.size,
            'size_kb': round(output_path.stat().st_size / 1024, 2),
            'size_valid': is_valid,
            'size_message': size_message
        }
    
    def export_single(
        self,
        format_name: str,
        packshot: Image.Image,
        background: Image.Image = None,
        headline: str = None,
        price: str = None,
        claim: str = None,
        logo: Image.Image = None,
        output_path: Path = None
    ) -> Dict:
        """
        Export a single creative in specified format
        
        Args:
            format_name: Format name ("1:1", "4:5", "9:16")
            packshot: Packshot image
            background: Background image
            headline: Headline text
            price: Price text
            claim: Claim text
            logo: Logo image
            output_path: Output file path
        
        Returns:
            Dictionary with export results
        """
        if output_path is None:
            output_path = Path("outputs") / f"creative_{format_name.replace(':', '_')}.jpg"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate layout
        creative = self.layout_engine.suggest_layout(
            format_name=format_name,
            packshot=packshot,
            background=background,
            headline=headline,
            price=price,
            claim=claim,
            logo=logo
        )
        
        # Compress
        creative_compressed = compress_image(creative, max_size_kb=MAX_FILE_SIZE_KB)
        
        # Save
        creative_compressed.save(output_path, format='JPEG', quality=85, optimize=True)
        
        # Validate
        is_valid, size_message = validate_file_size(output_path, MAX_FILE_SIZE_KB)
        
        return {
            'success': True,
            'path': str(output_path),
            'format': format_name,
            'dimensions': creative_compressed.size,
            'size_kb': round(output_path.stat().st_size / 1024, 2),
            'size_valid': is_valid,
            'size_message': size_message
        }

