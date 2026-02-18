"""
Routes Index - Central route aggregation

All routes flow through this file.
Request path: app.py → routes/index.py → modules/[module]/routes.py → controller → service
"""
from fastapi import APIRouter

# Import all module routers
from app.modules.extraction.routes import router as extraction_router
from app.modules.rules.routes import router as rules_router

# Main router aggregates all sub-routers from modules
main_router = APIRouter()

# Include module routers
main_router.include_router(extraction_router)
main_router.include_router(rules_router)
