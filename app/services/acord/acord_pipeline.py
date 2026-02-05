"""
ACORD Extraction Pipeline

Unified service that combines detection, extraction, and organization
for ACORD form processing.
"""

from pathlib import Path
from typing import Dict, Any

from app.services.acord.acord_detector import detect_acord_form
from app.services.pypdf_extractor import extract_form_fields, extract_for_llama
from app.services.acord.acord_organizer import AcordOrganizer
from app.services.acord.acord_formatter import AcordFormatter


class AcordExtractionPipeline:
    """
    ACORD extraction pipeline:
    1. Detect if PDF is fillable ACORD form
    2. Extract form fields using PyPDF (100% accuracy)
    3. Organize data using GPT-4-turbo
    4. Format for output
    """
    
    def __init__(self):
        """Initialize pipeline components"""
        self.organizer = AcordOrganizer()
        self.formatter = AcordFormatter()
    
    def process(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Process a PDF through the ACORD extraction pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Complete processing result with:
            - detection: ACORD form detection results
            - extraction: Raw extracted fields
            - organization: Organized schema data
            - formatted_data: Formatted output
        """
        pdf_path = Path(pdf_path)
        
        result = {
            "success": False,
            "pdf_file": pdf_path.name,
            "detection": {},
            "extraction": {},
            "organization": {},
            "error": None
        }
        
        # Step 1: Detect if ACORD form
        detection = detect_acord_form(pdf_path)
        result["detection"] = detection
        
        if not detection.get("is_fillable"):
            result["error"] = "PDF is not a fillable form. Use OCR/AI extraction instead."
            return result
        
        if not detection.get("is_acord"):
            result["error"] = f"PDF does not appear to be an ACORD form. Confidence: {detection.get('confidence', 'none')}"
            # Continue anyway but with warning
        
        # Step 2: Extract form fields using PyPDF (complete data)
        extraction = extract_form_fields(pdf_path)
        result["extraction"] = {
            "field_count": extraction.get("field_count", 0),
            "success": extraction.get("success", False)
        }
        
        if not extraction.get("success"):
            result["error"] = extraction.get("error", "Extraction failed")
            return result
        
        # Prepare data for GPT-4-turbo
        llama_data = extract_for_llama(pdf_path)
        
        if not llama_data.get("success"):
            result["error"] = llama_data.get("error", "Failed to prepare data for organization")
            return result
        
        # Step 3: Organize data using GPT-4-turbo
        organization = self.organizer.organize(llama_data.get("data", {}))
        result["organization"] = organization
        
        if not organization.get("success"):
            result["error"] = organization.get("error", "Organization failed")
            return result
        
        organized_data = organization.get("organized_data", {})
        
        # Step 4: Format data for output
        formatted_data = self.formatter.format(organized_data)
        
        # Set overall success
        result["success"] = True
        result["formatted_data"] = formatted_data
        
        return result
    
    def extract_only(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Extract and organize data (same as process for this simplified version).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extraction and organization results
        """
        return self.process(pdf_path)


def process_acord_pdf(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Convenience function to process an ACORD PDF through the pipeline.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Complete processing result
    """
    pipeline = AcordExtractionPipeline()
    return pipeline.process(pdf_path)
