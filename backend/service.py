"""
Main Backend Service - Orchestrates all components
"""
from pathlib import Path
from PIL import Image
from typing import Dict, Optional, List
import logging
from datetime import datetime

from backend.background_removal import BackgroundRemovalEngine
from backend.layout_engine import LayoutEngine
from backend.ocr_engine import OCREngine
from backend.compliance_engine import ComplianceEngine
from backend.export_engine import ExportEngine
from backend.config import UPLOAD_DIR, OUTPUT_DIR, CREATIVE_FORMATS

logger = logging.getLogger(__name__)


class TescoraService:
    """Main service class for TESCORA.AI backend"""
    
    def __init__(self):
        """Initialize all engines"""
        self.bg_removal = BackgroundRemovalEngine()
        self.layout_engine = LayoutEngine()
        self.ocr_engine = OCREngine()
        self.compliance_engine = ComplianceEngine()
        self.export_engine = ExportEngine()
        
        # Ensure directories exist
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def process_creative(
        self,
        packshot_path: Path,
        background_path: Optional[Path] = None,
        headline: Optional[str] = None,
        price: Optional[str] = None,
        claim: Optional[str] = None,
        logo_path: Optional[Path] = None,
        formats: Optional[List[str]] = None,
        run_compliance: bool = True
    ) -> Dict:
        """
        Complete creative processing workflow
        
        Args:
            packshot_path: Path to packshot image
            background_path: Path to background image (optional)
            headline: Headline text (optional)
            price: Price text (optional)
            claim: Claim text (optional)
            logo_path: Path to logo image (optional)
            formats: List of formats to generate (default: all)
            run_compliance: Whether to run compliance checks
        
        Returns:
            Dictionary with processing results
        """
        try:
            results = {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'steps': {},
                'exports': {},
                'compliance': None,
                'errors': []
            }
            
            # Step 1: Load and process packshot
            logger.info("Step 1: Processing packshot")
            packshot = Image.open(packshot_path)
            packshot_no_bg = self.bg_removal.remove_background(packshot_path)
            results['steps']['background_removal'] = {
                'success': True,
                'message': 'Background removed successfully'
            }
            
            # Step 2: Load other assets
            logger.info("Step 2: Loading assets")
            background = None
            if background_path and background_path.exists():
                background = Image.open(background_path)
            
            logo = None
            if logo_path and logo_path.exists():
                logo = Image.open(logo_path)
            
            # Step 3: Generate creatives in all formats
            logger.info("Step 3: Generating creatives")
            if formats is None:
                formats = list(CREATIVE_FORMATS.keys())
            
            exports = self.export_engine.export_creatives(
                packshot=packshot_no_bg,
                background=background,
                headline=headline,
                price=price,
                claim=claim,
                logo=logo,
                formats=formats,
                output_dir=OUTPUT_DIR
            )
            results['exports'] = exports
            results['steps']['export'] = {
                'success': all(exp.get('success', False) for exp in exports.values()),
                'formats': list(exports.keys())
            }
            
            # Step 4: Compliance validation
            if run_compliance:
                logger.info("Step 4: Running compliance checks")
                compliance_results = {}
                
                for format_name, export_result in exports.items():
                    if export_result.get('success'):
                        creative_path = Path(export_result['path'])
                        creative_image = Image.open(creative_path)
                        
                        compliance = self.compliance_engine.validate_creative(
                            image=creative_image,
                            format_name=format_name,
                            headline=headline,
                            price=price,
                            claim=claim
                        )
                        compliance_results[format_name] = compliance
                
                results['compliance'] = compliance_results
                results['steps']['compliance'] = {
                    'success': True,
                    'checked_formats': list(compliance_results.keys())
                }
            
            results['success'] = True
            logger.info("Creative processing completed successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing creative: {e}", exc_info=True)
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    def preview_layout(
        self,
        format_name: str,
        packshot_path: Path,
        background_path: Optional[Path] = None,
        headline: Optional[str] = None,
        price: Optional[str] = None,
        claim: Optional[str] = None,
        logo_path: Optional[Path] = None
    ) -> Image.Image:
        """
        Generate a preview of the layout without exporting
        
        Args:
            format_name: Format name ("1:1", "4:5", "9:16")
            packshot_path: Path to packshot image
            background_path: Path to background image (optional)
            headline: Headline text (optional)
            price: Price text (optional)
            claim: Claim text (optional)
            logo_path: Path to logo image (optional)
        
        Returns:
            PIL Image preview
        """
        # Load packshot and remove background
        packshot = Image.open(packshot_path)
        packshot_no_bg = self.bg_removal.remove_background(packshot_path)
        
        # Load other assets
        background = None
        if background_path and background_path.exists():
            background = Image.open(background_path)
        
        logo = None
        if logo_path and logo_path.exists():
            logo = Image.open(logo_path)
        
        # Generate layout
        preview = self.layout_engine.suggest_layout(
            format_name=format_name,
            packshot=packshot_no_bg,
            background=background,
            headline=headline,
            price=price,
            claim=claim,
            logo=logo
        )
        
        return preview
    
    def validate_existing_creative(
        self,
        creative_path: Path,
        format_name: str
    ) -> Dict:
        """
        Validate an existing creative for compliance
        
        Args:
            creative_path: Path to creative image
            format_name: Format name
        
        Returns:
            Compliance validation results
        """
        creative = Image.open(creative_path)
        return self.compliance_engine.validate_creative(
            image=creative,
            format_name=format_name
        )
    
    def extract_text_from_creative(self, creative_path: Path) -> Dict:
        """
        Extract text information from a creative
        
        Args:
            creative_path: Path to creative image
        
        Returns:
            Extracted text information
        """
        creative = Image.open(creative_path)
        return self.ocr_engine.extract_all(creative)
    
    def get_available_formats(self) -> List[str]:
        """Get list of available creative formats"""
        return list(CREATIVE_FORMATS.keys())
    
    def get_format_dimensions(self, format_name: str) -> tuple:
        """
        Get dimensions for a format
        
        Args:
            format_name: Format name
        
        Returns:
            (width, height) tuple
        """
        from backend.config import CREATIVE_FORMATS
        return CREATIVE_FORMATS.get(format_name, (1080, 1080))

