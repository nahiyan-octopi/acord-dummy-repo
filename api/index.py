"""
Vercel Serverless Function Entry Point

Standalone FastAPI app for Vercel deployment.
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="ACORD Data Extractor API",
    version="2.0.0",
    description="ACORD PDF Data Extraction using OpenAI GPT"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "ACORD Data Extractor API",
        "version": "2.0.0",
        "status": "running",
        "platform": "vercel",
        "endpoints": {
            "extract": "POST /api/extract-acord",
            "detect": "POST /api/detect-acord",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    openai_key = os.getenv("OPENAI_API_KEY")
    return {
        "status": "healthy",
        "version": "2.0.0",
        "openai_configured": bool(openai_key)
    }


# Import and include the extraction router
try:
    from app.routes.extraction import router as extraction_router
    app.include_router(extraction_router)
except ImportError as e:
    # If import fails, add a fallback endpoint
    @app.post("/api/extract-acord")
    async def extract_fallback():
        return {"error": f"App import failed: {str(e)}"}

