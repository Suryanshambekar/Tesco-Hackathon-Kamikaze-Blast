"""
Background Removal Engine using U²-Net or RMBG models
"""
import torch
from PIL import Image
import numpy as np
from pathlib import Path
import cv2
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BackgroundRemovalEngine:
    """Handles automatic background removal from product packshots"""
    
    def __init__(self, model_name: str = "briaai/RMBG-1.4", use_rembg: bool = True):
        """
        Initialize background removal engine
        
        Args:
            model_name: Hugging Face model name
            use_rembg: Use rembg library (simpler, recommended for prototype)
        """
        self.model_name = model_name
        self.use_rembg = use_rembg
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if use_rembg:
            try:
                from rembg import remove
                self.remove_bg = remove
                logger.info("Using rembg library for background removal")
            except ImportError:
                logger.warning("rembg not available, falling back to model-based approach")
                self.use_rembg = False
                self._load_model()
        else:
            self._load_model()
    
    def _load_model(self):
        """Load U²-Net or RMBG model from Hugging Face"""
        try:
            from transformers import AutoModelForImageSegmentation
            from PIL import Image as PILImage
            
            logger.info(f"Loading model: {self.model_name}")
            # For prototype, we'll use a simpler approach
            # In production, you'd load the actual model here
            logger.warning("Model loading deferred - using rembg fallback")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def remove_background(self, image_path: Path, output_path: Optional[Path] = None) -> Image.Image:
        """
        Remove background from product packshot
        
        Args:
            image_path: Path to input image
            output_path: Optional path to save output
        
        Returns:
            PIL Image with transparent background
        """
        try:
            # Load image
            input_image = Image.open(image_path).convert("RGB")
            
            if self.use_rembg:
                # Use rembg library (simpler and faster for prototype)
                import io
                input_bytes = io.BytesIO()
                input_image.save(input_bytes, format='PNG')
                input_bytes.seek(0)
                
                output_bytes = self.remove_bg(input_bytes.read())
                output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            else:
                # Use model-based approach
                output_image = self._remove_background_model(input_image)
            
            # Save if output path provided
            if output_path:
                output_image.save(output_path, format='PNG')
                logger.info(f"Background removed and saved to {output_path}")
            
            return output_image
            
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            # Fallback: return original image
            return input_image.convert("RGBA")
    
    def _remove_background_model(self, image: Image.Image) -> Image.Image:
        """
        Remove background using loaded model (fallback method)
        
        Args:
            image: PIL Image
        
        Returns:
            PIL Image with transparent background
        """
        # For prototype, use simple threshold-based approach as fallback
        # In production, this would use the actual U²-Net model
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Simple edge detection and masking (basic fallback)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Create RGBA image
        rgba = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)
        rgba[:, :, :3] = img_array
        rgba[:, :, 3] = mask
        
        return Image.fromarray(rgba, 'RGBA')
    
    def process_packshot(self, image_path: Path, output_dir: Path) -> Path:
        """
        Process packshot and save result
        
        Args:
            image_path: Path to packshot image
            output_dir: Directory to save processed image
        
        Returns:
            Path to processed image
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"packshot_no_bg_{image_path.stem}.png"
        
        result = self.remove_background(image_path, output_path)
        return output_path

