"""
ACORD Extraction Pipeline

Unified service that combines detection, extraction, and organization
for ACORD form processing.
"""

from pathlib import Path
import time
from typing import Dict, Any

from app.services.acord.acord_detector import detect_acord_form
from app.services.pypdf_extractor import extract_form_fields, extract_for_openai_from_result
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
        t0 = time.perf_counter()
        detection = detect_acord_form(pdf_path)
        t1 = time.perf_counter()
        result["detection_time_ms"] = round((t1 - t0) * 1000, 2)
        result["detection"] = detection
        
        if not detection.get("is_fillable"):
            result["error"] = "PDF is not a fillable form. Use OCR/AI extraction instead."
            return result
        
        if not detection.get("is_acord"):
            result["error"] = f"PDF does not appear to be an ACORD form. Confidence: {detection.get('confidence', 'none')}"
            # Continue anyway but with warning
        
        # Step 2: Extract form fields using PyPDF (complete data)
        t2 = time.perf_counter()
        extraction = extract_form_fields(pdf_path)
        t3 = time.perf_counter()
        result["extraction_time_ms"] = round((t3 - t2) * 1000, 2)
        result["extraction"] = {
            "field_count": extraction.get("field_count", 0),
            "success": extraction.get("success", False)
        }
        
        if not extraction.get("success"):
            result["error"] = extraction.get("error", "Extraction failed")
            return result
        
        # Prepare data for GPT-4-turbo without re-reading the PDF
        t4 = time.perf_counter()
        openai_data = extract_for_openai_from_result(extraction)
        t5 = time.perf_counter()
        result["prep_time_ms"] = round((t5 - t4) * 1000, 2)
        
        if not openai_data.get("success"):
            result["error"] = openai_data.get("error", "Failed to prepare data for organization")
            return result
        
        # Step 3: Organize data using GPT-4-turbo
        t6 = time.perf_counter()
        organization = self.organizer.organize(openai_data.get("data", {}))
        t7 = time.perf_counter()
        result["organization_time_ms"] = round((t7 - t6) * 1000, 2)
        result["organization"] = organization
        
        if not organization.get("success"):
            result["error"] = organization.get("error", "Organization failed")
            return result
        
        organized_data = organization.get("organized_data", {})
        
        # Step 4: Format data for output
        t8 = time.perf_counter()
        formatted_data = self.formatter.format(organized_data)
        t9 = time.perf_counter()
        result["formatting_time_ms"] = round((t9 - t8) * 1000, 2)
        
        # Set overall success
        result["success"] = True
        result["formatted_data"] = formatted_data
        
        return result


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
