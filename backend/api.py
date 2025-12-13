"""
API Layer for Streamlit Integration
Simplified interface for frontend
"""
from pathlib import Path
from typing import Optional, Dict, List
import logging

from backend.service import TescoraService

logger = logging.getLogger(__name__)

# Global service instance
_service = None


def get_service() -> TescoraService:
    """Get or create service instance"""
    global _service
    if _service is None:
        _service = TescoraService()
    return _service


def process_creative_api(
    packshot_path: str,
    background_path: Optional[str] = None,
    headline: Optional[str] = None,
    price: Optional[str] = None,
    claim: Optional[str] = None,
    logo_path: Optional[str] = None,
    formats: Optional[List[str]] = None,
    run_compliance: bool = True
) -> Dict:
    """
    API function for processing creatives
    
    Args:
        packshot_path: Path to packshot image
        background_path: Path to background image
        headline: Headline text
        price: Price text
        claim: Claim text
        logo_path: Path to logo image
        formats: List of formats
        run_compliance: Run compliance checks
    
    Returns:
        Processing results dictionary
    """
    service = get_service()
    
    return service.process_creative(
        packshot_path=Path(packshot_path),
        background_path=Path(background_path) if background_path else None,
        headline=headline,
        price=price,
        claim=claim,
        logo_path=Path(logo_path) if logo_path else None,
        formats=formats,
        run_compliance=run_compliance
    )


def preview_layout_api(
    format_name: str,
    packshot_path: str,
    background_path: Optional[str] = None,
    headline: Optional[str] = None,
    price: Optional[str] = None,
    claim: Optional[str] = None,
    logo_path: Optional[str] = None
):
    """
    API function for layout preview
    
    Returns:
        PIL Image
    """
    service = get_service()
    
    return service.preview_layout(
        format_name=format_name,
        packshot_path=Path(packshot_path),
        background_path=Path(background_path) if background_path else None,
        headline=headline,
        price=price,
        claim=claim,
        logo_path=Path(logo_path) if logo_path else None
    )


def validate_creative_api(creative_path: str, format_name: str) -> Dict:
    """API function for creative validation"""
    service = get_service()
    return service.validate_existing_creative(Path(creative_path), format_name)


def get_formats_api() -> List[str]:
    """Get available formats"""
    service = get_service()
    return service.get_available_formats()

