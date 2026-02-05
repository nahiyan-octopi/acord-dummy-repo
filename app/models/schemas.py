"""
Pydantic models for request/response validation
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class ValidationRule(BaseModel):
    """Validation rule schema"""
    required_fields: Optional[List[str]] = None
    required_checkboxes: Optional[List[str]] = None
    checkbox_groups: Optional[List[str]] = None


class ExtractionRequest(BaseModel):
    """Request schema for extraction endpoint"""
    extraction_type: str = Field(
        default="comprehensive",
        description="Type of extraction: comprehensive, simple, or custom"
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Custom instructions for custom extraction type"
    )
    dpi: Optional[int] = Field(
        default=300,
        description="DPI for PDF rendering"
    )
    
    @field_validator('extraction_type')
    @classmethod
    def validate_extraction_type(cls, v):
        if v not in ['comprehensive', 'simple', 'custom']:
            raise ValueError('extraction_type must be comprehensive, simple, or custom')
        return v


class ValidationRequest(BaseModel):
    """Request schema for validation endpoint"""
    validation_rules: Optional[ValidationRule] = None


class FileInfo(BaseModel):
    """File information schema"""
    filename: str
    path: str
    file_size: int
    file_size_kb: float
    file_size_mb: float
    modified_time: str


class ExtractionResponse(BaseModel):
    """Response schema for extraction endpoint"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    file_info: Optional[FileInfo] = None
    extracted_data: Optional[Dict[str, Any]] = None
    extraction_type: Optional[str] = None
    page_count: Optional[int] = None
    raw_text: Optional[str] = None
    tokens_used: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    json_file: Optional[str] = None


class HealthResponse(BaseModel):
    """Response schema for health check endpoint"""
    status: str
    message: str
    version: str
    openai_api: Optional[bool] = None
    upload_folder: Optional[bool] = None
    output_folder: Optional[bool] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
    details: Optional[str] = None


class ValidationResult(BaseModel):
    """Validation result schema"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    summary: Optional[str] = None


class DownloadFile(BaseModel):
    """File for download"""
    filename: str
    size: int
    size_kb: float
    modified: str


class OutputFilesResponse(BaseModel):
    """Response for listing output files"""
    success: bool
    files: List[DownloadFile] = []
    count: int = 0
