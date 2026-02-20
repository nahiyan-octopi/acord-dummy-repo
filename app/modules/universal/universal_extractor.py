"""
Universal PDF Extractor

Extracts data from any PDF using parallel PyPDF + OCR processing.
Uses GPT-4-turbo for intelligent data organization.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

# PDF processing
from pypdf import PdfReader

# Try to import OCR dependencies (optional)
try:
    from pdf2image import convert_from_path
    from PIL import Image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not installed. OCR fallback disabled.")

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract not installed. OCR features disabled.")

from app.config.config import Config
from app.services.ai.openai_service import get_openai_service

# Suppress PyPDF warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)


class UniversalPDFExtractor:
    """
    Universal PDF extractor with parallel processing.
    
    Uses PyPDF for direct text extraction, with OCR fallback for
    scanned documents. Both run in parallel for speed.
    """
    
    def __init__(self, config=None):
        """Initialize the PDF extractor"""
        self.config = config or Config
        self.openai_service = None  # Lazy initialization
    
    async def extract_pdf(
        self,
        pdf_path: str,
        dpi: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract data from any PDF file using parallel processing.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for PDF rendering (OCR)
        
        Returns:
            Dictionary with extracted data
        """
        dpi = dpi or self.config.PDF_DPI
        
        try:
            # Initialize OpenAI service on first use
            if self.openai_service is None:
                self.openai_service = get_openai_service()
            
            # Validate file
            if not Path(pdf_path).exists():
                return {
                    "success": False,
                    "error": "PDF file not found"
                }
            
            # Extract form fields directly (fast, synchronous)
            form_fields = self._extract_form_fields(pdf_path)
            
            page_count = 0
            
            # Use run_in_executor for parallel processing
            loop = asyncio.get_event_loop()
            
            def run_pypdf():
                """Extract text using PyPDF"""
                text = self._extract_text_directly(pdf_path)
                print(f"PyPDF extraction: {len(text)} characters")
                return text
            
            def run_ocr():
                """Extract text using OCR (fallback)"""
                if not PDF2IMAGE_AVAILABLE or not PYTESSERACT_AVAILABLE:
                    return "", 0
                
                images = self._convert_pdf_to_images(pdf_path, dpi)
                if not images:
                    return "", 0
                
                ocr_text = self._extract_text_from_images(images)
                print(f"OCR extraction: {len(ocr_text)} characters")
                return ocr_text, len(images)
            
            # Run PyPDF and OCR in parallel
            pypdf_task = loop.run_in_executor(None, run_pypdf)
            ocr_task = loop.run_in_executor(None, run_ocr)
            
            # Wait for PyPDF first (usually faster)
            direct_text = await pypdf_task
            
            ocr_text = ""
            full_text = ""
            
            # Smart selection: Use PyPDF if successful, otherwise wait for OCR
            if direct_text and len(direct_text.strip()) > 50:
                print("Using PyPDF text extraction (successful)")
                full_text = direct_text
                
                # Get page count from PyPDF
                try:
                    with open(pdf_path, 'rb') as f:
                        page_count = len(PdfReader(f).pages)
                except:
                    page_count = 1
            else:
                # PyPDF failed, wait for OCR
                print("PyPDF insufficient, waiting for OCR...")
                ocr_result = await ocr_task
                
                if isinstance(ocr_result, tuple):
                    ocr_text, page_count = ocr_result
                else:
                    ocr_text = ocr_result
                    page_count = 0
                
                print("Using OCR text extraction")
                full_text = ocr_text
            
            print(f"Total text for AI: {len(full_text)} characters")
            print(f"Form fields found: {len(form_fields.get('text_fields', {})) if form_fields else 0}")
            
            if not full_text and not form_fields:
                return {
                    "success": False,
                    "error": "No text could be extracted. Document may be image-only without readable text."
                }
            
            # Build context for AI
            ai_context = ""
            
            if full_text and full_text.strip():
                ai_context += "=== DOCUMENT TEXT ===\n"
                ai_context += full_text + "\n\n"
            
            # Add form fields if they exist
            if form_fields and form_fields.get('text_fields'):
                ai_context += "=== FORM FIELD VALUES ===\n"
                for field_name, field_value in form_fields.get('text_fields', {}).items():
                    clean_name = field_name.replace('[', '').replace(']', '').replace('.', ' ')
                    ai_context += f"{clean_name}: {field_value}\n"
                ai_context += "\n"
            
            if form_fields and form_fields.get('checkboxes'):
                ai_context += "=== CHECKBOX VALUES ===\n"
                for cb_name, cb_value in form_fields.get('checkboxes', {}).items():
                    clean_name = cb_name.replace('[', '').replace(']', '').replace('.', ' ')
                    status = "CHECKED" if cb_value else "UNCHECKED"
                    ai_context += f"{clean_name}: {status}\n"
                ai_context += "\n"
            
            print(f"Sending {len(ai_context)} characters to GPT-4o...")
            
            # Use OpenAI to extract and organize data
            ai_result = self.openai_service.extract_universal_data(ai_context)
            
            if not ai_result.get("success"):
                # If AI fails, fall back to raw form fields
                if form_fields:
                    print("AI extraction failed, falling back to raw form fields")
                    return {
                        "success": True,
                        "formatted_data": form_fields,
                        "document_type": "Unknown",
                        "extraction_method": "form_fields_only"
                    }
                return ai_result
            
            # Get the AI-enhanced extracted data
            ai_data = ai_result.get("data", {})
            
            if isinstance(ai_data, dict):
                extracted_data = ai_data.get("sections", {})
                document_type = ai_data.get("document_type", "Document")
                
                if not extracted_data and ai_data:
                    extracted_data = {k: v for k, v in ai_data.items() 
                                    if k not in ["document_type", "success", "error"]}
            else:
                extracted_data = ai_data if ai_data else {}
                document_type = "Document"
            
            return {
                "success": True,
                "formatted_data": extracted_data,
                "document_type": document_type,
                "tokens_used": ai_result.get("usage", {}),
                "model": self.config.OPENAI_MODEL,
                "extraction_method": "universal_ai",
                "page_count": page_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF extraction failed: {str(e)}"
            }
    
    def _extract_text_directly(self, pdf_path: str) -> str:
        """Extract text directly from PDF using PyPDF"""
        try:
            all_text = []
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                num_pages = min(len(pdf_reader.pages), self.config.MAX_PAGES)
                
                for i in range(num_pages):
                    try:
                        page = pdf_reader.pages[i]
                        text = page.extract_text()
                        if text and text.strip():
                            all_text.append(f"--- PAGE {i + 1} ---\n{text}\n")
                    except Exception as page_error:
                        print(f"Warning: Could not extract text from page {i + 1}: {str(page_error)}")
                        continue
            
            return "\n".join(all_text)
            
        except Exception as e:
            print(f"Error extracting text directly from PDF: {str(e)}")
            return ""
    
    def _convert_pdf_to_images(self, pdf_path: str, dpi: int) -> List:
        """Convert PDF pages to images for OCR"""
        if not PDF2IMAGE_AVAILABLE:
            return []
        
        try:
            max_pages = self.config.MAX_PAGES
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=1,
                last_page=max_pages
            )
            return images
        except Exception as e:
            print(f"Error converting PDF to images: {str(e)}")
            return []
    
    def _extract_text_from_images(self, images: List) -> str:
        """Extract text from images using OCR"""
        if not PYTESSERACT_AVAILABLE:
            return ""
        
        try:
            all_text = []
            for i, image in enumerate(images, 1):
                try:
                    text = pytesseract.image_to_string(image)
                    if text.strip():
                        all_text.append(f"--- PAGE {i} ---\n{text}\n")
                except Exception as ocr_error:
                    print(f"Warning: OCR failed for page {i}: {str(ocr_error)}")
                    continue
            
            return "\n".join(all_text)
            
        except Exception as e:
            print(f"Error extracting text from images: {str(e)}")
            return ""
    
    def _extract_form_fields(self, pdf_path: str) -> Dict[str, Any]:
        """Extract form fields directly from PDF"""
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                
                if not pdf_reader.get_fields():
                    return {}
                
                text_fields = {}
                checkboxes = {}
                radio_buttons = {}
                dropdowns = {}
                
                for field_name, field in pdf_reader.get_fields().items():
                    field_type = field.get("/FT")
                    field_value = field.get("/V")
                    
                    if field_type == "/Tx":  # Text field
                        text_fields[field_name] = field_value or ""
                    elif field_type == "/Ch":  # Choice (dropdown)
                        dropdowns[field_name] = field_value or ""
                    elif field_type == "/Btn":  # Button (checkbox/radio)
                        flags = field.get("/Ff", 0)
                        if flags & 0x8000:  # Radio button
                            radio_buttons[field_name] = field_value or ""
                        else:  # Checkbox
                            checkboxes[field_name] = bool(field_value and field_value != "Off")
                
                return {
                    "text_fields": text_fields,
                    "checkboxes": checkboxes,
                    "radio_buttons": radio_buttons,
                    "dropdowns": dropdowns
                }
        
        except Exception as e:
            print(f"Error extracting form fields: {str(e)}")
            return {}


# Singleton instance
_universal_extractor = None


def get_universal_extractor() -> UniversalPDFExtractor:
    """Get or create universal extractor singleton"""
    global _universal_extractor
    if _universal_extractor is None:
        _universal_extractor = UniversalPDFExtractor()
    return _universal_extractor
