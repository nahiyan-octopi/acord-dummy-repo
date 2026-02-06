"""
Extraction Routes

Single unified API endpoint for all document extraction:
- POST /api/extract-data - Auto-detects ACORD vs Universal

Detection endpoint (optional):
- POST /api/detect-acord - Check if PDF is ACORD form
"""

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import Optional

from app.modules.extraction.extraction_controller import ExtractionController


# Create router
router = APIRouter(prefix="/api", tags=["extraction"])

# Initialize controller
controller = ExtractionController()


@router.post("/extract-data")
async def extract_data(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    File_param: Optional[UploadFile] = File(None, alias="File")
):
    """
    Unified extraction endpoint for all document types.
    
    Automatically detects if PDF is an ACORD form and routes to appropriate pipeline:
    - ACORD forms: Hybrid extraction (direct mapping + AI for unformatted data)
    - Universal PDFs: AI-powered universal extraction
    
    Accepts file as either 'file' or 'File' parameter.
    
    Returns:
        JSON response with extracted data, document type, and extraction method
    """
    # Handle both 'file' and 'File' parameter names
    uploaded_file = file if file is not None else File_param
    
    return await controller.extract_data(uploaded_file, background_tasks)


@router.post("/detect-acord")
async def detect_acord(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    File_param: Optional[UploadFile] = File(None, alias="File")
):
    """
    Detect if a PDF is a fillable ACORD form.
    
    Returns detection info including:
    - is_fillable: Whether PDF has fillable form fields
    - is_acord: Whether it's an ACORD form
    - confidence: Detection confidence level (high/medium/low)
    - detected_form_type: Specific ACORD form type if detected
    """
    # Handle both 'file' and 'File' parameter names
    uploaded_file = file if file is not None else File_param
    
    return await controller.detect_acord(uploaded_file, background_tasks)


# Legacy endpoints for backwards compatibility (deprecated)
@router.post("/extract", deprecated=True)
async def extract_legacy(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    File_param: Optional[UploadFile] = File(None, alias="File")
):
    """
    [DEPRECATED] Use /api/extract-data instead.
    
    Smart extraction endpoint - automatically detects ACORD vs Universal.
    """
    uploaded_file = file if file is not None else File_param
    return await controller.extract_data(uploaded_file, background_tasks)


@router.post("/extract-acord", deprecated=True)
async def extract_acord_legacy(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    File_param: Optional[UploadFile] = File(None, alias="File")
):
    """
    [DEPRECATED] Use /api/extract-data instead.
    
    Force ACORD extraction pipeline.
    """
    uploaded_file = file if file is not None else File_param
    return await controller.extract_data(uploaded_file, background_tasks, force_acord=True)