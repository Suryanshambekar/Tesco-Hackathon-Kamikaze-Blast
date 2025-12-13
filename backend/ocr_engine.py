"""
OCR Engine for text extraction from creatives
"""
import pytesseract
from PIL import Image
import re
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OCREngine:
    """Handles OCR text extraction from creatives"""
    
    def __init__(self, languages: str = "eng"):
        """
        Initialize OCR engine
        
        Args:
            languages: Tesseract language codes (e.g., "eng", "eng+fra")
        """
        self.languages = languages
        # Set tesseract path if needed (Windows)
        try:
            # Try to find tesseract executable
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        except:
            pass
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Extract all text from image
        
        Args:
            image: PIL Image
        
        Returns:
            Extracted text string
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=self.languages)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return ""
    
    def extract_prices(self, image: Image.Image) -> List[Dict]:
        """
        Extract price information from image
        
        Args:
            image: PIL Image
        
        Returns:
            List of price dictionaries with 'value', 'currency', 'text'
        """
        text = self.extract_text(image)
        prices = []
        
        # Price patterns
        patterns = [
            r'£\s*(\d+\.?\d*)',  # British pounds
            r'\$\s*(\d+\.?\d*)',  # US dollars
            r'€\s*(\d+\.?\d*)',  # Euros
            r'(\d+\.?\d*)\s*p',   # Pence
            r'(\d+\.?\d*)\s*GBP', # GBP
        ]
        
        currency_map = {
            '£': 'GBP',
            '$': 'USD',
            '€': 'EUR',
        }
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                currency_symbol = match.group(0)[0] if match.group(0)[0] in currency_map else None
                value = match.group(1) if len(match.groups()) > 0 else match.group(0)
                
                prices.append({
                    'value': float(value),
                    'currency': currency_map.get(currency_symbol, 'UNKNOWN'),
                    'text': match.group(0),
                    'position': match.start()
                })
        
        return prices
    
    def extract_percentages(self, image: Image.Image) -> List[Dict]:
        """
        Extract percentage values from image
        
        Args:
            image: PIL Image
        
        Returns:
            List of percentage dictionaries
        """
        text = self.extract_text(image)
        percentages = []
        
        # Percentage pattern
        pattern = r'(\d+\.?\d*)\s*%'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            percentages.append({
                'value': float(match.group(1)),
                'text': match.group(0),
                'position': match.start()
            })
        
        return percentages
    
    def extract_claims(self, image: Image.Image) -> List[str]:
        """
        Extract promotional claims from image
        
        Args:
            image: PIL Image
        
        Returns:
            List of claim strings
        """
        text = self.extract_text(image)
        
        # Common claim patterns
        claim_keywords = [
            'save', 'discount', 'sale', 'offer', 'deal',
            'free', 'new', 'limited', 'exclusive', 'best',
            'lowest', 'guaranteed', 'special', 'promotion'
        ]
        
        sentences = re.split(r'[.!?]\s+', text)
        claims = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in claim_keywords:
                if keyword in sentence_lower:
                    claims.append(sentence.strip())
                    break
        
        return claims
    
    def extract_all(self, image: Image.Image) -> Dict:
        """
        Extract all information from image
        
        Args:
            image: PIL Image
        
        Returns:
            Dictionary with all extracted information
        """
        return {
            'full_text': self.extract_text(image),
            'prices': self.extract_prices(image),
            'percentages': self.extract_percentages(image),
            'claims': self.extract_claims(image),
        }

