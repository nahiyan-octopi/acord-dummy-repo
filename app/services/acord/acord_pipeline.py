"""
ACORD Extraction Pipeline

Hybrid extraction approach:
1. Direct mapping for coverage sections (no AI - fast, deterministic)
2. AI for unformatted data only (intelligent structuring)
"""

from pathlib import Path
from typing import Dict, Any

from app.services.acord.acord_detector import detect_acord_form
from app.services.pypdf_extractor import extract_for_llama as extract_pdf_fields
from app.services.acord.direct_mapper import get_direct_mapper
from app.services.acord.acord_organizer import get_acord_organizer
from app.services.acord.acord_formatter import AcordFormatter


class AcordExtractionPipeline:
    """
    ACORD extraction pipeline with hybrid approach:
    1. Detect if PDF is fillable ACORD form
    2. Extract form fields using PyPDF (100% accuracy)
    3. Direct map coverage sections (no AI)
    4. AI organize unformatted data only (contacts, addresses, insurers)
    5. Merge and format for output
    """
    
    def __init__(self):
        """Initialize pipeline components."""
        self.direct_mapper = get_direct_mapper()
        self.organizer = get_acord_organizer()
        self.formatter = AcordFormatter()
    
    def process(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Process a PDF through the hybrid ACORD extraction pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Complete processing result with formatted_data
        """
        pdf_path = Path(pdf_path)
        
        result = {
            "success": False,
            "pdf_file": pdf_path.name,
            "extraction_method": "acord_hybrid",
            "error": None
        }
        
        # Step 1: Detect if ACORD form
        detection = detect_acord_form(pdf_path)
        
        if not detection.get("is_fillable"):
            result["error"] = "PDF is not a fillable form. Use universal extraction instead."
            return result
        
        # Step 2: Extract form fields using PyPDF
        extraction_result = extract_pdf_fields(pdf_path)
        
        if not extraction_result.get("success"):
            result["error"] = extraction_result.get("error", "Failed to extract form fields")
            return result
        
        raw_fields = extraction_result.get("data", {})
        
        if not raw_fields:
            result["error"] = "No fields extracted from PDF"
            return result
        
        # Step 3: Direct map coverage sections (no AI)
        coverage_data, unmapped_fields = self.direct_mapper.direct_map(raw_fields)
        
        # Step 4: AI organize unformatted data only
        ai_result = self.organizer.organize_unformatted(unmapped_fields)
        
        if not ai_result.get("success"):
            # If AI fails, continue with just coverage data
            unformatted_data = {}
        else:
            unformatted_data = ai_result.get("unformatted_data", {})
        
        # Step 5: Merge coverage + unformatted data
        organized_data = coverage_data.copy()
        
        # Add AI-structured unformatted data
        if unformatted_data:
            organized_data["unformatted_data"] = unformatted_data
        
        # Step 6: Format for output
        formatted_data = self.formatter.format(organized_data)
        
        result["success"] = True
        result["formatted_data"] = formatted_data
        result["tokens_used"] = ai_result.get("tokens_used", {})
        
        return result
    
    def extract_only(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Alias for process() for backwards compatibility.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extraction results
        """
        return self.process(pdf_path)


def process_acord_pdf(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Convenience function to process an ACORD PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Complete processing result
    """
    pipeline = AcordExtractionPipeline()
    return pipeline.process(pdf_path)
