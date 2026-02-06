"""
Routes Index - Central route aggregation

All routes flow through this file.
Request path: app.py → index.py → modules/[module]/routes.py → controller → service
"""
from fastapi import APIRouter

from app.modules.extraction.routes import router as extraction_router

# Main router aggregates all sub-routers from modules
main_router = APIRouter()
main_router.include_router(extraction_router)


# =============================================================================
# API ROUTES REGISTRY & RESPONSE PATTERNS
# =============================================================================
# 
# EXTRACTION MODULE (/api)
# ├── POST /api/extract - Smart extraction (auto-detects ACORD vs Universal)
# ├── POST /api/extract-acord - Force ACORD pipeline
# │   └── modules/extraction/routes.py → controller → service
# │
# └── POST /api/detect-acord - Detect if PDF is ACORD form
#     └── modules/extraction/routes.py → controller → service
#
# ROOT ENDPOINTS (/)
# ├── GET /         → app.py
# └── GET /health   → app.py
#
# STANDARDIZED RESPONSE FORMAT:
# Success: {"success": true, "message": "...", "data": {...}, "timestamp": "...", "error": null, "metadata": {...}}
# Error:   {"success": false, "message": "...", "data": {}, "timestamp": "...", "error": {"code": "...", "message": "...", "details": {...}}}
# =============================================================================
