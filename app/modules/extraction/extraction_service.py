"""
Extraction Service

Core business logic for document extraction.
Routes to appropriate pipeline based on document type:
- ACORD forms: Hybrid extraction (direct mapping + AI for unformatted)
- Universal PDFs: AI-powered universal extraction
"""

from pathlib import Path
from typing import Dict, Any

from fastapi import UploadFile

from app.utils.utils import save_upload_file, get_file_info, save_json_output
from app.services.acord.acord_detector import detect_acord_form
from app.services.acord.acord_pipeline import AcordExtractionPipeline
from app.modules.universal.universal_extractor import get_universal_extractor
from app.config.config import Config


class ExtractionService:
    """
    Service for handling document extraction.
    
    Routes to appropriate pipeline:
    - ACORD Pipeline (hybrid): Direct mapping + AI for unformatted data
    - Universal Pipeline: Full AI extraction
    """
    
    def __init__(self):
        """Initialize service components."""
        self.acord_pipeline = AcordExtractionPipeline()
        self.universal_extractor = get_universal_extractor()
    
    async def extract_data(
        self, 
        file: UploadFile,
        force_acord: bool = False
    ) -> Dict[str, Any]:
        """
        Extract data from uploaded PDF file.
        
        Args:
            file: Uploaded PDF file
            force_acord: Force ACORD pipeline even for non-ACORD forms
            
        Returns:
            Extraction result with formatted_data
        """
        # Save uploaded file
        save_result, file_path = await save_upload_file(file)
        
        if not save_result:
            return {
                "success": False,
                "error": file_path  # Contains error message in this case
            }
        
        file_path = Path(file_path)
        
        # Get file info
        file_info = get_file_info(file_path)
        
        try:
            # Detect if ACORD form
            detection = detect_acord_form(file_path)
            
            is_acord = detection.get("is_acord", False)
            is_fillable = detection.get("is_fillable", False)
            
            # Route to appropriate pipeline
            if force_acord or (is_acord and is_fillable):
                # Use ACORD hybrid pipeline
                print("Using ACORD hybrid extraction pipeline")
                result = self.acord_pipeline.process(file_path)
                document_type = "ACORD Form"
                certificate_type = None
                extraction_method = "acord_hybrid"
            else:
                # Use universal extraction
                print("Using Universal AI extraction pipeline")
                result = await self.universal_extractor.extract_pdf(str(file_path))
                document_type = result.get("document_type", "Document")
                certificate_type = result.get("certificate_type")
                extraction_method = "universal_ai"
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Extraction failed"),
                    "file_path": str(file_path)
                }
            
            # Prepare extraction result
            extraction_result = {
                "success": True,
                "document_type": document_type,
                "certificate_type": certificate_type,
                "formatted_data": result.get("formatted_data", {}),
                "extraction_method": extraction_method,
                "tokens_used": result.get("tokens_used"),
                "file_info": file_info,
                "file_path": str(file_path)
            }
            
            # Save JSON output
            save_success, json_file = save_json_output(extraction_result)
            if save_success:
                extraction_result["json_file"] = json_file
            
            return extraction_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path)
            }
    
    async def detect_acord(self, file: UploadFile) -> Dict[str, Any]:
        """
        Detect if uploaded PDF is an ACORD form.
        
        Args:
            file: Uploaded PDF file
            
        Returns:
            Detection results
        """
        # Save uploaded file
        save_result, file_path = await save_upload_file(file)
        
        if not save_result:
            return {
                "success": False,
                "is_acord": False,
                "is_fillable": False,
                "error": file_path
            }
        
        file_path = Path(file_path)
        
        # Get file info
        file_info = get_file_info(file_path)
        
        # Run detection
        detection = detect_acord_form(file_path)
        
        return {
            "success": True,
            "is_acord": detection.get("is_acord", False),
            "is_fillable": detection.get("is_fillable", False),
            "confidence": detection.get("confidence", "none"),
            "detected_form_type": detection.get("detected_form_type"),
            "field_count": detection.get("field_count", 0),
            "file_info": file_info,
            "file_path": str(file_path)
        }
