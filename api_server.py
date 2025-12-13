"""
REST API Server for TESCORA.AI Backend
FastAPI wrapper for React frontend integration
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List
import uvicorn
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import json
import logging

from backend.api import (
    process_creative_api,
    preview_layout_api,
    get_formats_api,
    validate_creative_api
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TESCORA.AI API", version="1.0.0")

# CORS middleware for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Create React App
        "http://localhost:5173",  # Vite
        "http://localhost:5174",  # Vite (alternate)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for temporary uploads
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TESCORA.AI API Server",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/formats": "Get available creative formats",
            "POST /api/process": "Process creative and generate outputs",
            "POST /api/preview": "Generate preview of creative layout",
            "GET /api/download/{filename}": "Download generated creative file",
            "POST /api/validate": "Validate existing creative for compliance"
        }
    }


@app.get("/api/formats")
async def get_formats():
    """Get available creative formats"""
    try:
        formats = get_formats_api()
        return {"success": True, "formats": formats}
    except Exception as e:
        logger.error(f"Error getting formats: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


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
        logger.info(f"Processing creative: packshot={packshot.filename}")
        
        # Save uploaded files
        packshot_path = UPLOAD_DIR / f"packshot_{packshot.filename}"
        with open(packshot_path, "wb") as f:
            content = await packshot.read()
            f.write(content)
        logger.info(f"Saved packshot to {packshot_path}")
        
        background_path = None
        if background and background.filename:
            background_path = UPLOAD_DIR / f"background_{background.filename}"
            with open(background_path, "wb") as f:
                f.write(await background.read())
            logger.info(f"Saved background to {background_path}")
        
        logo_path = None
        if logo and logo.filename:
            logo_path = UPLOAD_DIR / f"logo_{logo.filename}"
            with open(logo_path, "wb") as f:
                f.write(await logo.read())
            logger.info(f"Saved logo to {logo_path}")
        
        # Parse formats
        format_list = None
        if formats:
            try:
                format_list = json.loads(formats)
            except json.JSONDecodeError:
                logger.warning(f"Invalid formats JSON: {formats}")
        
        # Process creative
        logger.info("Calling backend process_creative_api...")
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
                    filename = Path(file_path).name
                    export_data['url'] = f"/api/download/{filename}"
                    export_data['download_url'] = f"http://localhost:8000/api/download/{filename}"
        
        logger.info("Processing complete")
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error processing creative: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "errors": [str(e)]}
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
        logger.info(f"Generating preview for format: {format_name}")
        
        # Save packshot
        packshot_path = UPLOAD_DIR / f"preview_packshot_{packshot.filename}"
        with open(packshot_path, "wb") as f:
            f.write(await packshot.read())
        
        background_path = None
        if background and background.filename:
            background_path = UPLOAD_DIR / f"preview_bg_{background.filename}"
            with open(background_path, "wb") as f:
                f.write(await background.read())
        
        logo_path = None
        if logo and logo.filename:
            logo_path = UPLOAD_DIR / f"preview_logo_{logo.filename}"
            with open(logo_path, "wb") as f:
                f.write(await logo.read())
        
        # Generate preview
        logger.info("Calling backend preview_layout_api...")
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
        
        logger.info("Preview generated successfully")
        return JSONResponse(content={
            "success": True,
            "preview": f"data:image/png;base64,{img_base64}",
            "format": format_name
        })
    
    except Exception as e:
        logger.error(f"Error generating preview: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download generated creative file"""
    try:
        file_path = OUTPUT_DIR / filename
        if file_path.exists():
            return FileResponse(
                path=file_path,
                media_type="image/jpeg",
                filename=filename
            )
        return JSONResponse(
            status_code=404,
            content={"error": f"File not found: {filename}"}
        )
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/validate")
async def validate_creative(
    creative: UploadFile = File(...),
    format_name: str = Form(...)
):
    """Validate existing creative for compliance"""
    try:
        logger.info(f"Validating creative: {creative.filename}, format: {format_name}")
        
        creative_path = UPLOAD_DIR / f"validate_{creative.filename}"
        with open(creative_path, "wb") as f:
            f.write(await creative.read())
        
        results = validate_creative_api(
            creative_path=str(creative_path),
            format_name=format_name
        )
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error validating creative: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TESCORA.AI API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    print("Starting TESCORA.AI API Server...")
    print("API Documentation: http://localhost:8000/docs")
    print("API Root: http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

