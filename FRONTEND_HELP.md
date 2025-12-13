# Frontend Integration Guide - TESCORA.AI Backend

## Table of Contents
1. [Backend Overview](#backend-overview)
2. [Backend Architecture](#backend-architecture)
3. [Creating a REST API Wrapper](#creating-a-rest-api-wrapper)
4. [API Endpoints Specification](#api-endpoints-specification)
5. [Data Flow](#data-flow)
6. [React Integration Guide](#react-integration-guide)
7. [Request/Response Formats](#requestresponse-formats)
8. [File Upload Handling](#file-upload-handling)
9. [Error Handling](#error-handling)
10. [Example Implementation](#example-implementation)

---

## Backend Overview

The TESCORA.AI backend is a Python-based service that processes retail media creatives. It handles:
- **Background removal** from product packshots
- **Layout generation** for multiple formats (1:1, 4:5, 9:16)
- **OCR text extraction** from images
- **Compliance validation** with risk assessment
- **Multi-format export** with automatic compression

### Key Backend Files Structure

```
backend/
├── __init__.py              # Package initialization
├── api.py                   # API layer (currently for Streamlit)
├── service.py               # Main service orchestrator
├── background_removal.py    # Background removal engine
├── layout_engine.py         # Creative layout generation
├── ocr_engine.py           # Text extraction from images
├── compliance_engine.py    # Compliance validation
├── export_engine.py        # Multi-format export
├── config.py               # Configuration settings
└── utils.py                # Utility functions
```

---

## Backend Architecture

### Component Flow

```
User Input (React)
    ↓
REST API Wrapper (Flask/FastAPI) ← YOU NEED TO CREATE THIS
    ↓
backend/api.py (API Layer)
    ↓
backend/service.py (Main Service)
    ↓
┌─────────────────────────────────────┐
│  Background Removal Engine          │
│  Layout Engine                      │
│  OCR Engine                         │
│  Compliance Engine                  │
│  Export Engine                      │
└─────────────────────────────────────┘
    ↓
Output Files (outputs/)
```

### Main Service Methods

The `TescoraService` class in `backend/service.py` provides these key methods:

1. **`process_creative()`** - Complete workflow
   - Input: Packshot, background, text inputs, logo
   - Output: Generated creatives + compliance reports

2. **`preview_layout()`** - Generate preview
   - Input: Format name, assets, text
   - Output: PIL Image (needs conversion to base64/URL)

3. **`validate_existing_creative()`** - Validate compliance
   - Input: Creative image path, format name
   - Output: Compliance validation results

4. **`get_available_formats()`** - Get supported formats
   - Output: List of format names ["1:1", "4:5", "9:16"]

---

## Creating a REST API Wrapper

**IMPORTANT**: The current backend is designed for Streamlit. You need to create a REST API wrapper using Flask or FastAPI to connect React.

### Option 1: FastAPI (Recommended)

Create `api_server.py` in the project root:

```python
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List
import uvicorn
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

from backend.api import (
    process_creative_api,
    preview_layout_api,
    get_formats_api,
    validate_creative_api
)

app = FastAPI(title="TESCORA.AI API")

# CORS middleware for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for temporary uploads
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/api/formats")
async def get_formats():
    """Get available creative formats"""
    formats = get_formats_api()
    return {"formats": formats}

@app.post("/api/process")
async def process_creative(
    packshot: UploadFile = File(...),
    background: Optional[UploadFile] = File(None),
    logo: Optional[UploadFile] = File(None),
    headline: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    claim: Optional[str] = Form(None),
    formats: Optional[str] = Form(None),  # JSON string like '["1:1", "4:5"]'
    run_compliance: bool = Form(True)
):
    """Process creative and generate outputs"""
    try:
        # Save uploaded files
        packshot_path = UPLOAD_DIR / f"packshot_{packshot.filename}"
        with open(packshot_path, "wb") as f:
            f.write(await packshot.read())
        
        background_path = None
        if background:
            background_path = UPLOAD_DIR / f"background_{background.filename}"
            with open(background_path, "wb") as f:
                f.write(await background.read())
        
        logo_path = None
        if logo:
            logo_path = UPLOAD_DIR / f"logo_{logo.filename}"
            with open(logo_path, "wb") as f:
                f.write(await logo.read())
        
        # Parse formats
        format_list = None
        if formats:
            import json
            format_list = json.loads(formats)
        
        # Process creative
        results = process_creative_api(
            packshot_path=str(packshot_path),
            background_path=str(background_path) if background_path else None,
            logo_path=str(logo_path) if logo_path else None,
            headline=headline,
            price=price,
            claim=claim,
            formats=format_list,
            run_compliance=run_compliance
        )
        
        # Convert file paths to URLs
        if results.get('success'):
            exports = results.get('exports', {})
            for format_name, export_data in exports.items():
                if export_data.get('success'):
                    # Convert path to URL
                    file_path = export_data['path']
                    export_data['url'] = f"/api/download/{Path(file_path).name}"
        
        return JSONResponse(content=results)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/preview")
async def preview_creative(
    format_name: str = Form(...),
    packshot: UploadFile = File(...),
    background: Optional[UploadFile] = File(None),
    logo: Optional[UploadFile] = File(None),
    headline: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    claim: Optional[str] = Form(None)
):
    """Generate preview of creative layout"""
    try:
        # Save packshot
        packshot_path = UPLOAD_DIR / f"preview_packshot_{packshot.filename}"
        with open(packshot_path, "wb") as f:
            f.write(await packshot.read())
        
        background_path = None
        if background:
            background_path = UPLOAD_DIR / f"preview_bg_{background.filename}"
            with open(background_path, "wb") as f:
                f.write(await background.read())
        
        logo_path = None
        if logo:
            logo_path = UPLOAD_DIR / f"preview_logo_{logo.filename}"
            with open(logo_path, "wb") as f:
                f.write(await logo.read())
        
        # Generate preview
        preview_image = preview_layout_api(
            format_name=format_name,
            packshot_path=str(packshot_path),
            background_path=str(background_path) if background_path else None,
            logo_path=str(logo_path) if logo_path else None,
            headline=headline,
            price=price,
            claim=claim
        )
        
        # Convert PIL Image to base64
        buffer = BytesIO()
        preview_image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return JSONResponse(content={
            "success": True,
            "preview": f"data:image/png;base64,{img_base64}"
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download generated creative file"""
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return FileResponse(
            path=file_path,
            media_type="image/jpeg",
            filename=filename
        )
    return JSONResponse(
        status_code=404,
        content={"error": "File not found"}
    )

@app.post("/api/validate")
async def validate_creative(
    creative: UploadFile = File(...),
    format_name: str = Form(...)
):
    """Validate existing creative for compliance"""
    try:
        creative_path = UPLOAD_DIR / f"validate_{creative.filename}"
        with open(creative_path, "wb") as f:
            f.write(await creative.read())
        
        results = validate_creative_api(
            creative_path=str(creative_path),
            format_name=format_name
        )
        
        return JSONResponse(content=results)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the API Server

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn python-multipart

# Run the server
python api_server.py
```

The API will be available at `http://localhost:8000`

---

## API Endpoints Specification

### 1. GET `/api/formats`
Get available creative formats.

**Response:**
```json
{
  "formats": ["1:1", "4:5", "9:16"]
}
```

### 2. POST `/api/process`
Process creative and generate outputs.

**Request (multipart/form-data):**
- `packshot` (file, required): Product packshot image
- `background` (file, optional): Background image
- `logo` (file, optional): Logo image
- `headline` (string, optional): Headline text
- `price` (string, optional): Price text (e.g., "£9.99")
- `claim` (string, optional): Claim text
- `formats` (string, optional): JSON array of formats, e.g., `'["1:1", "4:5"]'`
- `run_compliance` (boolean, optional): Run compliance checks (default: true)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-XX...",
  "steps": {
    "background_removal": {
      "success": true,
      "message": "Background removed successfully"
    },
    "export": {
      "success": true,
      "formats": ["1:1", "4:5", "9:16"]
    },
    "compliance": {
      "success": true,
      "checked_formats": ["1:1", "4:5", "9:16"]
    }
  },
  "exports": {
    "1:1": {
      "success": true,
      "path": "outputs/creative_1_1.jpg",
      "url": "/api/download/creative_1_1.jpg",
      "format": "1:1",
      "dimensions": [1080, 1080],
      "size_kb": 245.5,
      "size_valid": true,
      "size_message": "Image size: 245.5 KB"
    },
    "4:5": { ... },
    "9:16": { ... }
  },
  "compliance": {
    "1:1": {
      "is_compliant": true,
      "risk_level": "LOW",
      "issues": [],
      "warnings": [],
      "checks": {
        "safe_zones": { "passed": true },
        "contrast": { "passed": true },
        "claims": { "passed": true }
      }
    },
    "4:5": { ... },
    "9:16": { ... }
  },
  "errors": []
}
```

### 3. POST `/api/preview`
Generate preview of creative layout.

**Request (multipart/form-data):**
- `format_name` (string, required): Format name ("1:1", "4:5", or "9:16")
- `packshot` (file, required): Product packshot image
- `background` (file, optional): Background image
- `logo` (file, optional): Logo image
- `headline` (string, optional): Headline text
- `price` (string, optional): Price text
- `claim` (string, optional): Claim text

**Response:**
```json
{
  "success": true,
  "preview": "data:image/png;base64,iVBORw0KGgoAAAANS..."
}
```

### 4. GET `/api/download/{filename}`
Download generated creative file.

**Response:** Binary image file (JPEG)

### 5. POST `/api/validate`
Validate existing creative for compliance.

**Request (multipart/form-data):**
- `creative` (file, required): Creative image to validate
- `format_name` (string, required): Format name

**Response:**
```json
{
  "is_compliant": false,
  "risk_level": "MEDIUM",
  "issues": [
    {
      "type": "claims",
      "message": "Potentially risky claims detected: save, discount",
      "risk": "MEDIUM"
    }
  ],
  "warnings": [
    {
      "type": "contrast",
      "message": "Text may not be readable for all users"
    }
  ],
  "checks": { ... }
}
```

---

## Data Flow

### Complete Workflow

```
1. User uploads images in React
   ↓
2. React sends FormData to /api/process
   ↓
3. FastAPI receives files, saves to uploads/
   ↓
4. FastAPI calls backend/api.py functions
   ↓
5. Backend processes:
   - Background removal
   - Layout generation
   - OCR extraction
   - Compliance validation
   - Multi-format export
   ↓
6. Backend saves outputs to outputs/
   ↓
7. FastAPI returns JSON with file URLs
   ↓
8. React displays results and download links
```

### Preview Workflow

```
1. User changes inputs in React
   ↓
2. React sends to /api/preview
   ↓
3. Backend generates preview image
   ↓
4. Backend converts to base64
   ↓
5. React displays preview image
```

---

## React Integration Guide

### 1. Setup API Client

Create `src/services/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

// Helper function for file uploads
export const uploadFiles = async (endpoint, formData) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Request failed');
  }
  
  return response.json();
};

// Get available formats
export const getFormats = async () => {
  const response = await fetch(`${API_BASE_URL}/formats`);
  return response.json();
};

// Process creative
export const processCreative = async (data) => {
  const formData = new FormData();
  
  // Add files
  formData.append('packshot', data.packshot);
  if (data.background) formData.append('background', data.background);
  if (data.logo) formData.append('logo', data.logo);
  
  // Add text fields
  if (data.headline) formData.append('headline', data.headline);
  if (data.price) formData.append('price', data.price);
  if (data.claim) formData.append('claim', data.claim);
  
  // Add formats
  if (data.formats) {
    formData.append('formats', JSON.stringify(data.formats));
  }
  
  formData.append('run_compliance', data.runCompliance ?? true);
  
  return uploadFiles('/process', formData);
};

// Generate preview
export const generatePreview = async (data) => {
  const formData = new FormData();
  
  formData.append('format_name', data.formatName);
  formData.append('packshot', data.packshot);
  if (data.background) formData.append('background', data.background);
  if (data.logo) formData.append('logo', data.logo);
  if (data.headline) formData.append('headline', data.headline);
  if (data.price) formData.append('price', data.price);
  if (data.claim) formData.append('claim', data.claim);
  
  return uploadFiles('/preview', formData);
};

// Validate creative
export const validateCreative = async (creative, formatName) => {
  const formData = new FormData();
  formData.append('creative', creative);
  formData.append('format_name', formatName);
  
  return uploadFiles('/validate', formData);
};

// Download file URL
export const getDownloadUrl = (filename) => {
  return `${API_BASE_URL}/download/${filename}`;
};
```

### 2. React Component Example

Create `src/components/CreativeBuilder.jsx`:

```jsx
import React, { useState } from 'react';
import { processCreative, generatePreview, getFormats } from '../services/api';

const CreativeBuilder = () => {
  const [packshot, setPackshot] = useState(null);
  const [background, setBackground] = useState(null);
  const [logo, setLogo] = useState(null);
  const [headline, setHeadline] = useState('');
  const [price, setPrice] = useState('');
  const [claim, setClaim] = useState('');
  const [selectedFormats, setSelectedFormats] = useState(['1:1', '4:5', '9:16']);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleProcess = async () => {
    if (!packshot) {
      alert('Please upload a packshot image');
      return;
    }

    setLoading(true);
    try {
      const response = await processCreative({
        packshot,
        background,
        logo,
        headline,
        price,
        claim,
        formats: selectedFormats,
        runCompliance: true,
      });

      setResults(response);
    } catch (error) {
      console.error('Error processing creative:', error);
      alert('Failed to process creative: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (formatName) => {
    if (!packshot) return;

    try {
      const response = await generatePreview({
        formatName,
        packshot,
        background,
        logo,
        headline,
        price,
        claim,
      });

      if (response.success) {
        setPreview(response.preview);
      }
    } catch (error) {
      console.error('Error generating preview:', error);
    }
  };

  return (
    <div className="creative-builder">
      <h1>TESCORA.AI Creative Builder</h1>

      {/* File Uploads */}
      <div className="uploads">
        <div>
          <label>Packshot (Required)</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setPackshot(e.target.files[0])}
          />
        </div>
        <div>
          <label>Background (Optional)</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setBackground(e.target.files[0])}
          />
        </div>
        <div>
          <label>Logo (Optional)</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setLogo(e.target.files[0])}
          />
        </div>
      </div>

      {/* Text Inputs */}
      <div className="text-inputs">
        <input
          type="text"
          placeholder="Headline"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
        />
        <input
          type="text"
          placeholder="Price (e.g., £9.99)"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
        <input
          type="text"
          placeholder="Claim"
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
        />
      </div>

      {/* Format Selection */}
      <div className="formats">
        <label>
          <input
            type="checkbox"
            checked={selectedFormats.includes('1:1')}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedFormats([...selectedFormats, '1:1']);
              } else {
                setSelectedFormats(selectedFormats.filter(f => f !== '1:1'));
              }
            }}
          />
          1:1 (Instagram Feed)
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedFormats.includes('4:5')}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedFormats([...selectedFormats, '4:5']);
              } else {
                setSelectedFormats(selectedFormats.filter(f => f !== '4:5'));
              }
            }}
          />
          4:5 (Facebook Feed)
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedFormats.includes('9:16')}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedFormats([...selectedFormats, '9:16']);
              } else {
                setSelectedFormats(selectedFormats.filter(f => f !== '9:16'));
              }
            }}
          />
          9:16 (Instagram Reels/Stories)
        </label>
      </div>

      {/* Preview Button */}
      <button onClick={() => handlePreview('1:1')}>
        Generate Preview
      </button>

      {/* Preview Display */}
      {preview && (
        <div className="preview">
          <img src={preview} alt="Preview" />
        </div>
      )}

      {/* Process Button */}
      <button onClick={handleProcess} disabled={loading}>
        {loading ? 'Processing...' : 'Generate Creatives'}
      </button>

      {/* Results Display */}
      {results && results.success && (
        <div className="results">
          <h2>Generated Creatives</h2>
          {Object.entries(results.exports).map(([format, data]) => (
            data.success && (
              <div key={format} className="creative-result">
                <h3>{format}</h3>
                <img
                  src={`http://localhost:8000${data.url}`}
                  alt={`Creative ${format}`}
                />
                <p>Size: {data.size_kb} KB</p>
                <a
                  href={`http://localhost:8000${data.url}`}
                  download
                >
                  Download
                </a>

                {/* Compliance Results */}
                {results.compliance && results.compliance[format] && (
                  <div className="compliance">
                    <h4>Compliance</h4>
                    <p>
                      Risk Level: {results.compliance[format].risk_level}
                    </p>
                    <p>
                      Compliant: {results.compliance[format].is_compliant ? 'Yes' : 'No'}
                    </p>
                    {results.compliance[format].issues.length > 0 && (
                      <ul>
                        {results.compliance[format].issues.map((issue, idx) => (
                          <li key={idx}>{issue.message}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            )
          ))}
        </div>
      )}
    </div>
  );
};

export default CreativeBuilder;
```

---

## Request/Response Formats

### Process Creative Request

**Content-Type:** `multipart/form-data`

```
packshot: [File]
background: [File] (optional)
logo: [File] (optional)
headline: "Amazing Product"
price: "£9.99"
claim: "Save 20% Today!"
formats: '["1:1", "4:5", "9:16"]'
run_compliance: true
```

### Process Creative Response

```json
{
  "success": true,
  "timestamp": "2025-01-XX...",
  "steps": {
    "background_removal": { "success": true, "message": "..." },
    "export": { "success": true, "formats": [...] },
    "compliance": { "success": true, "checked_formats": [...] }
  },
  "exports": {
    "1:1": {
      "success": true,
      "path": "outputs/creative_1_1.jpg",
      "url": "/api/download/creative_1_1.jpg",
      "format": "1:1",
      "dimensions": [1080, 1080],
      "size_kb": 245.5,
      "size_valid": true
    }
  },
  "compliance": {
    "1:1": {
      "is_compliant": true,
      "risk_level": "LOW",
      "issues": [],
      "warnings": [],
      "checks": { ... }
    }
  },
  "errors": []
}
```

---

## File Upload Handling

### Supported Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- Other formats supported by PIL

### File Size Recommendations
- Packshot: < 5 MB (will be processed)
- Background: < 5 MB
- Logo: < 1 MB

### Output File Constraints
- All outputs are compressed to < 500 KB
- Format: JPEG
- Dimensions: As per format (1080x1080, 1080x1350, 1080x1920)

---

## Error Handling

### Common Errors

1. **Missing Packshot**
   ```json
   {
     "success": false,
     "error": "Packshot is required"
   }
   ```

2. **Invalid Format**
   ```json
   {
     "success": false,
     "error": "Unknown format: invalid_format"
   }
   ```

3. **Processing Error**
   ```json
   {
     "success": false,
     "errors": ["Error message here"]
   }
   ```

### React Error Handling Example

```javascript
try {
  const response = await processCreative(data);
  if (!response.success) {
    // Handle backend errors
    console.error('Backend error:', response.errors);
    alert('Processing failed: ' + response.errors.join(', '));
  }
} catch (error) {
  // Handle network/API errors
  console.error('API error:', error);
  alert('Failed to connect to server');
}
```

---

## Example Implementation

### Complete React App Structure

```
react-app/
├── src/
│   ├── components/
│   │   ├── CreativeBuilder.jsx
│   │   ├── FileUpload.jsx
│   │   ├── Preview.jsx
│   │   └── Results.jsx
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   └── index.js
├── package.json
└── ...
```

### Key Dependencies

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "axios": "^1.6.0"  // Alternative to fetch
  }
}
```

### Environment Variables

Create `.env`:

```
REACT_APP_API_URL=http://localhost:8000/api
```

---

## Backend Configuration

### Important Settings (backend/config.py)

- **Creative Formats:**
  - `1:1`: 1080x1080 (Instagram feed)
  - `4:5`: 1080x1350 (Facebook feed)
  - `9:16`: 1080x1920 (Instagram Reels/Stories)

- **File Size Limit:** 500 KB per output
- **Safe Zone Margins:** 10% on all sides
- **Min Font Size:** 24px
- **Min Contrast Ratio:** 4.5 (WCAG AA)

### Directory Structure

```
project-root/
├── backend/          # Backend code
├── uploads/          # Temporary uploads (auto-created)
├── outputs/          # Generated creatives (auto-created)
├── api_server.py     # REST API wrapper (YOU CREATE THIS)
└── requirements.txt  # Python dependencies
```

---

## Testing the Integration

### 1. Start Backend API Server

```bash
cd "F:\Tesco Hackathon Protype"
python api_server.py
```

### 2. Test with curl

```bash
# Get formats
curl http://localhost:8000/api/formats

# Process creative
curl -X POST http://localhost:8000/api/process \
  -F "packshot=@path/to/packshot.jpg" \
  -F "headline=Test Product" \
  -F "price=£9.99" \
  -F 'formats=["1:1"]'
```

### 3. Test in React

Start your React app and use the API client functions.

---

## Tips for Frontend Development

1. **Real-time Preview:** Use debouncing when user changes inputs to avoid too many preview requests
2. **Progress Indicators:** Show loading states during processing (can take 10-30 seconds)
3. **Error Messages:** Display compliance issues clearly to users
4. **File Validation:** Validate file types and sizes before upload
5. **Image Preview:** Show uploaded images before processing
6. **Download Buttons:** Make it easy to download generated creatives
7. **Compliance Warnings:** Highlight high-risk issues prominently

---

## Support

If you encounter issues:
1. Check backend logs for errors
2. Verify file paths and permissions
3. Ensure all dependencies are installed
4. Check CORS settings if React can't connect
5. Verify image formats are supported

---

## Quick Checklist

- [ ] Create `api_server.py` with FastAPI wrapper
- [ ] Install FastAPI dependencies (`pip install fastapi uvicorn python-multipart`)
- [ ] Test API endpoints with curl/Postman
- [ ] Create React API client service
- [ ] Implement file upload components
- [ ] Add preview functionality
- [ ] Display results and compliance data
- [ ] Add error handling
- [ ] Test end-to-end workflow

Good luck with the integration! 🚀

