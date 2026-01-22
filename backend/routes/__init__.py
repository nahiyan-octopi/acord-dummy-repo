"""
Routes module for ACORD Data Extractor API
"""
from .extraction import router as extraction_router

__all__ = ['extraction_router']
