"""
ACORD Form Detector

Detects if a PDF is a fillable ACORD form by checking for form fields
and ACORD-specific field naming patterns.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from pypdf import PdfReader


# ACORD-specific field patterns that indicate an ACORD form
ACORD_FIELD_PATTERNS = [
    "NamedInsured",
    "Producer_",
    "Policy_GeneralLiability",
    "Policy_AutomobileLiability",
    "Policy_WorkersCompensation",
    "Policy_ExcessLiability",
    "Insurer_FullName",
    "Insurer_NAICCode",
    "CertificateHolder",
    "Vehicle_",
    "WorkersCompensation",
    "GeneralAggregateLimitAmount",
    "EachOccurrenceLimitAmount",
]


def detect_acord_form(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Detect if a PDF is a fillable ACORD form.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with detection results:
        {
            "is_fillable": bool,      # Has form fields
            "is_acord": bool,         # Appears to be ACORD form
            "field_count": int,       # Number of form fields
            "acord_pattern_matches": int,  # How many ACORD patterns matched
            "confidence": str,        # "high", "medium", "low", "none"
            "detected_form_type": str # e.g., "ACORD 25", "Unknown"
        }
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        return {
            "is_fillable": False,
            "is_acord": False,
            "field_count": 0,
            "acord_pattern_matches": 0,
            "confidence": "none",
            "detected_form_type": "File not found",
            "error": f"PDF file not found: {pdf_path}"
        }
    
    try:
        reader = PdfReader(str(pdf_path))
        fields = reader.get_fields()
        
        if fields is None or len(fields) == 0:
            return {
                "is_fillable": False,
                "is_acord": False,
                "field_count": 0,
                "acord_pattern_matches": 0,
                "confidence": "none",
                "detected_form_type": "Not a fillable PDF"
            }
        
        field_count = len(fields)
        field_names = list(fields.keys())
        
        # Check how many ACORD patterns match
        pattern_matches = 0
        matched_patterns = []
        
        for pattern in ACORD_FIELD_PATTERNS:
            for field_name in field_names:
                if pattern.lower() in field_name.lower():
                    pattern_matches += 1
                    matched_patterns.append(pattern)
                    break  # Count each pattern only once
        
        # Determine if this is an ACORD form and confidence level
        is_acord = pattern_matches >= 3
        
        if pattern_matches >= 8:
            confidence = "high"
            detected_form_type = _detect_acord_form_type(field_names)
        elif pattern_matches >= 5:
            confidence = "medium"
            detected_form_type = _detect_acord_form_type(field_names)
        elif pattern_matches >= 3:
            confidence = "low"
            detected_form_type = "Possible ACORD form"
        else:
            confidence = "none"
            detected_form_type = "Not an ACORD form"
        
        return {
            "is_fillable": True,
            "is_acord": is_acord,
            "field_count": field_count,
            "acord_pattern_matches": pattern_matches,
            "confidence": confidence,
            "detected_form_type": detected_form_type,
            "matched_patterns": matched_patterns
        }
        
    except Exception as e:
        return {
            "is_fillable": False,
            "is_acord": False,
            "field_count": 0,
            "acord_pattern_matches": 0,
            "confidence": "none",
            "detected_form_type": "Error reading PDF",
            "error": str(e)
        }


def _detect_acord_form_type(field_names: list) -> str:
    """
    Attempt to identify which ACORD form this is.
    
    Args:
        field_names: List of all field names in the PDF
        
    Returns:
        Detected form type string
    """
    field_names_lower = [f.lower() for f in field_names]
    
    # ACORD 25 - Certificate of Liability Insurance
    acord_25_indicators = [
        "certificateholder",
        "generalliability",
        "automobileliability",
        "workerscompensation",
        "excessliability",
        "namedinsured"
    ]
    
    acord_25_matches = sum(1 for indicator in acord_25_indicators 
                          if any(indicator in fn for fn in field_names_lower))
    
    if acord_25_matches >= 4:
        return "ACORD 25 - Certificate of Liability Insurance"
    
    # Could add detection for other ACORD forms here (ACORD 27, 28, 125, etc.)
    
    return "ACORD Form (type undetermined)"


def is_fillable_acord(pdf_path: str | Path) -> bool:
    """
    Quick check if PDF is a fillable ACORD form.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        True if fillable ACORD form with high/medium confidence
    """
    result = detect_acord_form(pdf_path)
    return result["is_fillable"] and result["is_acord"] and result["confidence"] in ["high", "medium"]
