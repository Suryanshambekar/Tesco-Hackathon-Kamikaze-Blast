"""
Configuration settings for TESCORA.AI backend
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Creative format dimensions (width, height)
CREATIVE_FORMATS = {
    "1:1": (1080, 1080),      # Instagram feed
    "4:5": (1080, 1350),      # Facebook feed
    "9:16": (1080, 1920),     # Instagram Reels/Stories
}

# Safe zone margins (percentage of canvas)
SAFE_ZONE_MARGIN = {
    "horizontal": 0.1,  # 10% margin on left and right
    "vertical": 0.1,    # 10% margin on top and bottom
}

# Text constraints
MIN_FONT_SIZE = 24
MIN_CONTRAST_RATIO = 4.5  # WCAG AA standard

# File size constraints
MAX_FILE_SIZE_KB = 500

# Background removal model
BG_REMOVAL_MODEL = "briaai/RMBG-1.4"  # Alternative: "U2Net" or use rembg library

# OCR settings
OCR_LANGUAGES = "eng"  # English

# LLM settings for compliance
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # Or use smaller model for faster inference
USE_LOCAL_LLM = True  # Set to False to use API-based models

# Compliance risk levels
RISK_LEVELS = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}

# Risky claim keywords (rule-based)
RISKY_KEYWORDS = [
    "free", "guaranteed", "best", "lowest price", "save",
    "discount", "sale", "limited time", "act now", "exclusive"
]

