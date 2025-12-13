# TESCORA.AI - AI-Assisted Tesco-Compliant Creative Builder

## Project Overview

TESCORA.AI is an AI-assisted creative builder that enables advertisers to quickly generate professional, guideline-aware, multi-format retail media creatives with minimal manual effort.

## Backend Architecture

The backend is built with Python and consists of the following modules:

### Core Components

1. **Background Removal Engine** (`backend/background_removal.py`)
   - Uses U²-Net/RMBG models for automatic packshot background removal
   - Supports transparent background generation

2. **Layout Suggestion Engine** (`backend/layout_engine.py`)
   - Rule-based creative composition
   - Handles multiple formats (1:1, 4:5, 9:16)
   - Maintains safe zones and visual balance

3. **OCR Engine** (`backend/ocr_engine.py`)
   - Text extraction using Tesseract OCR
   - Price, percentage, and claim detection
   - Multi-language support

4. **Compliance Intelligence Engine** (`backend/compliance_engine.py`)
   - Hybrid rule-based + LLM approach
   - Safe zone validation
   - Contrast ratio checks
   - Claim risk assessment

5. **Multi-format Export Engine** (`backend/export_engine.py`)
   - Generates creatives in multiple formats
   - Automatic compression to meet size requirements (<500 KB)
   - Format-specific optimization

6. **Main Service** (`backend/service.py`)
   - Orchestrates all components
   - End-to-end workflow management

7. **API Layer** (`backend/api.py`)
   - Simplified interface for Streamlit frontend
   - Easy integration points

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Mac: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

3. Set up directories:
   - The backend will automatically create `uploads/` and `outputs/` directories

## Usage

### Basic Usage

```python
from backend.service import TescoraService

# Initialize service
service = TescoraService()

# Process a creative
results = service.process_creative(
    packshot_path=Path("path/to/packshot.jpg"),
    background_path=Path("path/to/background.jpg"),
    headline="Amazing Product",
    price="£9.99",
    claim="Save 20%",
    formats=["1:1", "4:5", "9:16"]
)

# Check results
print(f"Success: {results['success']}")
print(f"Exports: {results['exports']}")
print(f"Compliance: {results['compliance']}")
```

### Using the API Layer

```python
from backend.api import process_creative_api

results = process_creative_api(
    packshot_path="path/to/packshot.jpg",
    headline="Amazing Product",
    price="£9.99",
    formats=["1:1", "4:5"]
)
```

## Configuration

Edit `backend/config.py` to customize:
- Creative format dimensions
- Safe zone margins
- Font size constraints
- File size limits
- Model selections

## Supported Formats

- **1:1** (1080x1080) - Instagram feed
- **4:5** (1080x1350) - Facebook feed
- **9:16** (1080x1920) - Instagram Reels/Stories

## Output

The backend generates:
- Processed creatives in JPEG format
- Compliance validation reports
- OCR-extracted text information
- Risk assessments

All outputs are saved to the `outputs/` directory.

## Notes

- This is a prototype implementation
- LLM features may require additional setup for production use
- Background removal uses rembg library by default (simpler for prototype)
- All images are compressed to meet <500 KB requirement

## License

Hackathon Project - Tesco Retail Media InnovAItion Jam

