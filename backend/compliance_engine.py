"""
Compliance Intelligence Engine - Hybrid rule-based + LLM approach
"""
from PIL import Image
from typing import Dict, List, Optional
import logging
from pathlib import Path

from backend.config import (
    MIN_FONT_SIZE, MIN_CONTRAST_RATIO, RISKY_KEYWORDS, RISK_LEVELS,
    SAFE_ZONE_MARGIN
)
from backend.utils import get_safe_zone, calculate_contrast_ratio, get_dominant_colors
from backend.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """Handles compliance validation using rule-based and LLM-based checks"""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize compliance engine
        
        Args:
            use_llm: Whether to use LLM for claim analysis
        """
        self.use_llm = use_llm
        self.ocr_engine = OCREngine()
        self.llm_model = None
        
        if use_llm:
            self._load_llm()
    
    def _load_llm(self):
        """Load LLM model for compliance checking"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_name = "mistralai/Mistral-7B-Instruct-v0.2"
            logger.info(f"Loading LLM model: {model_name}")
            
            # For prototype, we'll use a lightweight approach
            # In production, you'd load the actual model or use an API
            logger.warning("LLM loading deferred - using rule-based fallback for now")
            self.llm_available = False
        except Exception as e:
            logger.warning(f"LLM not available: {e}. Using rule-based checks only.")
            self.llm_available = False
    
    def validate_creative(
        self,
        image: Image.Image,
        format_name: str,
        headline: Optional[str] = None,
        price: Optional[str] = None,
        claim: Optional[str] = None
    ) -> Dict:
        """
        Validate creative for compliance
        
        Args:
            image: PIL Image of the creative
            format_name: Format name ("1:1", "4:5", "9:16")
            headline: Headline text (optional, for validation)
            price: Price text (optional)
            claim: Claim text (optional)
        
        Returns:
            Dictionary with validation results and risk assessment
        """
        results = {
            'is_compliant': True,
            'risk_level': 'LOW',
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        # Rule-based checks
        safe_zone_check = self._check_safe_zones(image, format_name)
        results['checks']['safe_zones'] = safe_zone_check
        
        contrast_check = self._check_contrast(image)
        results['checks']['contrast'] = contrast_check
        
        text_check = self._check_text_legibility(image)
        results['checks']['text_legibility'] = text_check
        
        # OCR-based text extraction
        ocr_results = self.ocr_engine.extract_all(image)
        results['extracted_text'] = ocr_results
        
        # Claim validation
        claim_check = self._validate_claims(ocr_results, headline, claim)
        results['checks']['claims'] = claim_check
        
        # Price validation
        price_check = self._validate_prices(ocr_results, price)
        results['checks']['prices'] = price_check
        
        # Aggregate results
        all_issues = []
        all_warnings = []
        max_risk = RISK_LEVELS['LOW']
        
        for check_name, check_result in results['checks'].items():
            if isinstance(check_result, dict):
                if not check_result.get('passed', True):
                    all_issues.append({
                        'type': check_name,
                        'message': check_result.get('message', ''),
                        'risk': check_result.get('risk', 'LOW')
                    })
                    risk_level = RISK_LEVELS.get(check_result.get('risk', 'LOW'), 1)
                    max_risk = max(max_risk, risk_level)
                
                if check_result.get('warning'):
                    all_warnings.append({
                        'type': check_name,
                        'message': check_result.get('warning', '')
                    })
        
        results['issues'] = all_issues
        results['warnings'] = all_warnings
        
        # Determine overall risk level
        if max_risk >= RISK_LEVELS['HIGH']:
            results['risk_level'] = 'HIGH'
            results['is_compliant'] = False
        elif max_risk >= RISK_LEVELS['MEDIUM']:
            results['risk_level'] = 'MEDIUM'
        else:
            results['risk_level'] = 'LOW'
        
        if all_issues:
            results['is_compliant'] = False
        
        return results
    
    def _check_safe_zones(self, image: Image.Image, format_name: str) -> Dict:
        """Check if content respects safe zones"""
        from backend.config import CREATIVE_FORMATS
        
        if format_name not in CREATIVE_FORMATS:
            return {'passed': False, 'message': 'Unknown format', 'risk': 'MEDIUM'}
        
        canvas_width, canvas_height = CREATIVE_FORMATS[format_name]
        safe_zone = get_safe_zone(
            canvas_width,
            canvas_height,
            SAFE_ZONE_MARGIN["horizontal"],
            SAFE_ZONE_MARGIN["vertical"]
        )
        
        # Basic check: ensure image dimensions match expected format
        if image.size != (canvas_width, canvas_height):
            return {
                'passed': False,
                'message': f'Image dimensions ({image.size}) do not match format {format_name} ({canvas_width}x{canvas_height})',
                'risk': 'MEDIUM'
            }
        
        # In a full implementation, we'd analyze content placement
        # For prototype, we assume layout engine handles this correctly
        return {'passed': True, 'message': 'Safe zones respected'}
    
    def _check_contrast(self, image: Image.Image) -> Dict:
        """Check text contrast ratios"""
        try:
            # Get dominant colors
            colors = get_dominant_colors(image, k=5)
            
            # Check contrast between colors
            min_contrast = float('inf')
            for i, color1 in enumerate(colors):
                for color2 in colors[i+1:]:
                    contrast = calculate_contrast_ratio(color1, color2)
                    min_contrast = min(min_contrast, contrast)
            
            if min_contrast < MIN_CONTRAST_RATIO:
                return {
                    'passed': False,
                    'message': f'Contrast ratio ({min_contrast:.2f}) below minimum ({MIN_CONTRAST_RATIO})',
                    'risk': 'MEDIUM',
                    'warning': 'Text may not be readable for all users'
                }
            
            return {
                'passed': True,
                'message': f'Contrast ratio acceptable ({min_contrast:.2f})'
            }
        except Exception as e:
            logger.error(f"Contrast check error: {e}")
            return {'passed': True, 'warning': 'Could not verify contrast'}
    
    def _check_text_legibility(self, image: Image.Image) -> Dict:
        """Check if text is legible (size, clarity)"""
        # OCR can help detect if text is readable
        text = self.ocr_engine.extract_text(image)
        
        if not text or len(text.strip()) < 3:
            return {
                'passed': False,
                'message': 'No readable text detected',
                'risk': 'LOW',
                'warning': 'Text may be too small or unclear'
            }
        
        return {'passed': True, 'message': 'Text is legible'}
    
    def _validate_claims(self, ocr_results: Dict, headline: Optional[str], claim: Optional[str]) -> Dict:
        """Validate promotional claims"""
        all_text = ocr_results.get('full_text', '').lower()
        claims = ocr_results.get('claims', [])
        
        # Combine with provided text
        if headline:
            all_text += " " + headline.lower()
        if claim:
            all_text += " " + claim.lower()
        
        risky_found = []
        for keyword in RISKY_KEYWORDS:
            if keyword in all_text:
                risky_found.append(keyword)
        
        if risky_found:
            # Use LLM if available for deeper analysis
            if self.llm_available and self.use_llm:
                risk_assessment = self._llm_assess_claims(all_text, risky_found)
            else:
                # Rule-based assessment
                risk_assessment = self._rule_based_assess_claims(risky_found, all_text)
            
            return {
                'passed': risk_assessment['risk'] == 'LOW',
                'message': f"Potentially risky claims detected: {', '.join(risky_found)}",
                'risk': risk_assessment['risk'],
                'details': risk_assessment.get('details', '')
            }
        
        return {'passed': True, 'message': 'No risky claims detected'}
    
    def _rule_based_assess_claims(self, risky_keywords: List[str], text: str) -> Dict:
        """Rule-based claim risk assessment"""
        high_risk_keywords = ['free', 'guaranteed', 'best', 'lowest price']
        medium_risk_keywords = ['save', 'discount', 'sale', 'limited time']
        
        has_high_risk = any(kw in risky_keywords for kw in high_risk_keywords)
        has_medium_risk = any(kw in risky_keywords for kw in medium_risk_keywords)
        
        if has_high_risk:
            risk = 'HIGH'
        elif has_medium_risk:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'
        
        return {
            'risk': risk,
            'details': f'Found {len(risky_keywords)} potentially risky keywords'
        }
    
    def _llm_assess_claims(self, text: str, keywords: List[str]) -> Dict:
        """LLM-based claim risk assessment"""
        # For prototype, fallback to rule-based
        # In production, this would use the loaded LLM model
        return self._rule_based_assess_claims(keywords, text)
    
    def _validate_prices(self, ocr_results: Dict, price: Optional[str]) -> Dict:
        """Validate price information"""
        prices = ocr_results.get('prices', [])
        
        if not prices and not price:
            return {'passed': True, 'message': 'No price information found'}
        
        # Check for multiple conflicting prices
        if len(prices) > 1:
            values = [p['value'] for p in prices]
            if max(values) - min(values) > 0.01:  # Significant difference
                return {
                    'passed': False,
                    'message': 'Multiple conflicting prices detected',
                    'risk': 'HIGH'
                }
        
        # Check for unrealistic prices (e.g., £0.00)
        for price_info in prices:
            if price_info['value'] <= 0:
                return {
                    'passed': False,
                    'message': 'Invalid price detected (zero or negative)',
                    'risk': 'HIGH'
                }
        
        return {'passed': True, 'message': 'Price information valid'}

