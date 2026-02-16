"""
Extraction Controller

Handles HTTP request validation and response formatting.
Delegates business logic to extraction service.
"""

from fastapi import UploadFile, BackgroundTasks

from app.modules.extraction.extraction_service import ExtractionService
from app.utils.response_utils import APIResponse, validation_error, server_error


class ExtractionController:
    """
    Controller for document extraction endpoints.
    
    Handles:
    - File validation
    - Service orchestration
    - Response formatting
    - Background task cleanup
    """
    
    def __init__(self):
        """Initialize controller with extraction service."""
        self.service = ExtractionService()
    
    async def extract_data(
        self, 
        file: UploadFile, 
        background_tasks: BackgroundTasks,
        force_acord: bool = False
    ) -> dict:
        """
        Unified extraction endpoint handler.
        
        Args:
            file: Uploaded PDF file
            background_tasks: FastAPI background tasks for cleanup
            force_acord: Force ACORD pipeline even for non-ACORD PDFs
            
        Returns:
            API response with extracted data
        """
        # Validate file presence
        if file is None:
            return validation_error("No file provided. Please upload a PDF file.")
        
        # Validate file type
        if not file.filename:
            return validation_error("Invalid file. Missing filename.")
        
        if not file.filename.lower().endswith('.pdf'):
            return validation_error("Invalid file type. Only PDF files are supported.")
        
        try:
            # Call service for extraction
            result = await self.service.extract_data(file, force_acord=force_acord)
            
            if not result.get("success"):
                return server_error(result.get("error", "Extraction failed"))
            
            # Schedule file cleanup
            if result.get("file_path"):
                from app.utils.utils import cleanup_temp_file
                background_tasks.add_task(cleanup_temp_file, result["file_path"])
            
            # Return success response
            return APIResponse.extraction_success(
                formatted_data=result.get("formatted_data", {}),
                file_info=result.get("file_info", {}),
                document_type=result.get("document_type", "Document"),
                certificate_type=result.get("certificate_type"),
                extraction_method=result.get("extraction_method", "unknown"),
                tokens_used=result.get("tokens_used"),
                json_file=result.get("json_file")
            )
            
        except Exception as e:
            return server_error(f"Extraction failed: {str(e)}")
    
    async def detect_acord(
        self, 
        file: UploadFile, 
        background_tasks: BackgroundTasks
    ) -> dict:
        """
        Detect if PDF is an ACORD form.
        
        Args:
            file: Uploaded PDF file
            background_tasks: FastAPI background tasks for cleanup
            
        Returns:
            API response with detection results
        """
        # Validate file presence
        if file is None:
            return validation_error("No file provided. Please upload a PDF file.")
        
        # Validate file type
        if not file.filename:
            return validation_error("Invalid file. Missing filename.")
        
        if not file.filename.lower().endswith('.pdf'):
            return validation_error("Invalid file type. Only PDF files are supported.")
        
        try:
            # Call service for detection
            result = await self.service.detect_acord(file)
            
            # Schedule file cleanup
            if result.get("file_path"):
                from app.utils.utils import cleanup_temp_file
                background_tasks.add_task(cleanup_temp_file, result["file_path"])
            
            return APIResponse.detection_success(
                is_acord=result.get("is_acord", False),
                is_fillable=result.get("is_fillable", False),
                confidence=result.get("confidence", "none"),
                detected_form_type=result.get("detected_form_type"),
                field_count=result.get("field_count", 0),
                file_info=result.get("file_info", {})
            )
            
        except Exception as e:
            return server_error(f"Detection failed: {str(e)}")
