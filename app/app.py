"""
ACORD Data Extractor API - Application Entry Point

Request Flow:
    1. Request hits app.py (this file)
    2. Routes to routes/index.py (route aggregation)
    3. Routes to routes/[module].py (endpoint definitions)
    4. Calls modules/[module]/controller (request handling)
    5. Calls modules/[module]/service (business logic)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import Config
from app.routes.index import main_router

# Initialize configuration
Config.init_app()

# Initialize FastAPI app
app = FastAPI(
    title="DCN Ai",
    version=Config.VERSION,
    description="DCN Ai",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes from index
app.include_router(main_router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": Config.APP_NAME,
        "version": Config.VERSION,
        "status": "running",
        "message": "Welcome to DCN Ai Backend",
        "endpoints": {
            "extract": "POST /api/extract-data",
            "detect": "POST /api/detect-acord",
            "vectorize": "POST /api/vectorize",
            "vectorize_query": "POST /api/vectorize-query",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": Config.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
