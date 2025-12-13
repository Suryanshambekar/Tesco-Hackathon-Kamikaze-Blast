# TESCORA.AI Backend - Quick Start Guide

## Installation Steps

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Tesseract OCR:**
   - **Windows:** Download installer from https://github.com/UB-Mannheim/tesseract/wiki
   - **Mac:** `brew install tesseract`
   - **Linux:** `sudo apt-get install tesseract-ocr`

3. **Verify installation:**
```bash
python -c "from backend.service import TescoraService; print('Backend ready!')"
```

## Quick Test

1. Create an `uploads/` directory and add a test packshot image
2. Run the example:
```bash
python example_usage.py
```

## Integration with Streamlit

The backend is designed to work seamlessly with Streamlit. Here's a minimal example:

```python
import streamlit as st
from backend.api import process_creative_api

# In your Streamlit app
packshot_file = st.file_uploader("Upload Packshot", type=['jpg', 'png'])

if packshot_file:
    # Save uploaded file
    with open("uploads/temp_packshot.jpg", "wb") as f:
        f.write(packshot_file.getbuffer())
    
    # Process creative
    results = process_creative_api(
        packshot_path="uploads/temp_packshot.jpg",
        headline=st.text_input("Headline"),
        price=st.text_input("Price"),
        claim=st.text_input("Claim"),
        formats=["1:1", "4:5", "9:16"]
    )
    
    # Display results
    if results['success']:
        st.success("Creative generated successfully!")
        # Display images and compliance results
```

## Key Functions

### Main Service (`backend/service.py`)
- `TescoraService.process_creative()` - Full workflow
- `TescoraService.preview_layout()` - Generate preview
- `TescoraService.validate_existing_creative()` - Validate compliance

### API Layer (`backend/api.py`)
- `process_creative_api()` - Simple API for processing
- `preview_layout_api()` - Preview generation
- `validate_creative_api()` - Compliance validation
- `get_formats_api()` - Get available formats

## Output Structure

After processing, you'll get:
```
outputs/
  ├── creative_1_1.jpg
  ├── creative_4_5.jpg
  └── creative_9_16.jpg
```

Each creative includes:
- Proper dimensions for the format
- Size < 500 KB
- Compliance validation results

## Troubleshooting

**Issue: Tesseract not found**
- Solution: Install Tesseract and ensure it's in your PATH, or set the path in `backend/ocr_engine.py`

**Issue: Background removal fails**
- Solution: The backend uses `rembg` library. Install with `pip install rembg`

**Issue: Large file sizes**
- Solution: The export engine automatically compresses, but you can adjust quality in `backend/export_engine.py`

## Next Steps

1. Integrate with your Streamlit frontend
2. Customize layout logic in `backend/layout_engine.py`
3. Adjust compliance rules in `backend/compliance_engine.py`
4. Configure formats in `backend/config.py`

