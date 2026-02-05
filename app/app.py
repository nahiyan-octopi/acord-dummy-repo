"""
ACORD Data Extractor API

Minimal backend API for extracting data from ACORD PDF forms using OpenAI GPT.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Config
from app.routes.extraction import router as extraction_router
from app.core.keep_alive import start_keep_alive

# Initialize configuration
Config.init_app()

# Initialize FastAPI app
app = FastAPI(
    title="ACORD Data Extractor API",
    version=Config.VERSION,
    description="ACORD PDF Data Extraction using OpenAI GPT"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include extraction routes
app.include_router(extraction_router)


@app.on_event("startup")
async def startup_event():
    """Start keep-alive pinger on Render deployment."""
    if os.environ.get('RENDER'):
        start_keep_alive()



@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": Config.APP_NAME,
        "version": Config.VERSION,
        "status": "running",
        "endpoints": {
            "extract": "POST /api/extract-acord",
            "detect": "POST /api/detect-acord",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": Config.VERSION,
        "model": Config.OPENAI_MODEL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
