"""
Extraction Routes - PDF extraction endpoint
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path

from app.config import Config
from app.core.utils import (
    save_upload_file,
    cleanup_file,
    save_json_output,
    get_file_info,
)
from app.services.acord.acord_pipeline import AcordExtractionPipeline
from app.services.acord.acord_detector import detect_acord_form

router = APIRouter(prefix="/api", tags=["extraction"])


@router.post("/extract-acord")
async def extract_acord_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Extract data from ACORD PDF using the extraction pipeline:
    1. Detect if fillable ACORD form
    2. Extract with PyPDF (100% accuracy for fillable PDFs)
    3. Organize with GPT-4-turbo
    4. Format output
    
    Returns:
    - Complete extraction and organization results
    """
    pdf_path = None
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file
        success, pdf_path = await save_upload_file(file)
        if not success:
            raise HTTPException(status_code=400, detail=pdf_path)
        
        # Get file info
        file_info = get_file_info(pdf_path)
        
        # Process through ACORD pipeline
        pipeline = AcordExtractionPipeline()
        result = pipeline.process(pdf_path)
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_file, pdf_path)
        else:
            cleanup_file(pdf_path)
        
        # Build simplified response with only formatted_data
        response = {
            "success": result.get("success", False),
            "formatted_data": result.get("formatted_data", {}),
            "file_info": file_info,
            "error": result.get("error")
        }
        
        # Save result to JSON file
        json_success, json_path = save_json_output(response)
        if json_success:
            response["json_file"] = Path(json_path).name
        
        return JSONResponse(response)
        
    except Exception as e:
        if pdf_path:
            cleanup_file(pdf_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-acord")
async def detect_acord_endpoint(file: UploadFile = File(...)):
    """
    Detect if a PDF is a fillable ACORD form.
    
    Returns:
    - Detection result with is_fillable, is_acord, confidence
    """
    pdf_path = None
    
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        success, pdf_path = await save_upload_file(file)
        if not success:
            raise HTTPException(status_code=400, detail=pdf_path)
        
        result = detect_acord_form(pdf_path)
        result["filename"] = file.filename
        
        cleanup_file(pdf_path)
        return JSONResponse(result)
        
    except Exception as e:
        if pdf_path:
            cleanup_file(pdf_path)
        raise HTTPException(status_code=500, detail=str(e))
