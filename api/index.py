"""
Vercel Serverless Function Entry Point

This file re-exports the FastAPI app for Vercel's serverless function runtime.
Vercel expects the app to be in api/index.py.
"""
import sys
import os

# Add project root to Python path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app

# Vercel expects an 'app' variable (ASGI application)
# The import above already defines it
