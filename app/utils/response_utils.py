"""
Response Utilities - Standardized API response patterns

This module provides standardized response functions to ensure
consistent API responses across all endpoints.
"""
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from datetime import datetime


class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(
        data: Dict[str, Any] = None,
        message: str = "Operation completed successfully",
        metadata: Dict[str, Any] = None
    ) -> JSONResponse:
        """
        Create standardized success response.
        
        Args:
            data: Response data payload
            message: Success message
            metadata: Additional metadata (file_info, tokens_used, etc.)
            
        Returns:
            JSONResponse with standardized format
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "error": None
        }
        
        if metadata:
            response_data["metadata"] = metadata
            
        return JSONResponse(
            status_code=200,
            content=response_data
        )
    
    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        error_code: str = None,
        details: Dict[str, Any] = None
    ) -> JSONResponse:
        """
        Create standardized error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Custom error code for frontend handling
            details: Additional error details
            
        Returns:
            JSONResponse with standardized format
        """
        response_data = {
            "success": False,
            "message": message,
            "data": {},
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "code": error_code or f"HTTP_{status_code}",
                "message": message,
                "details": details or {}
            }
        }
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def extraction_success(
        formatted_data: Dict[str, Any],
        document_type: str,
        extraction_method: str,
        file_info: Dict[str, Any],
        tokens_used: Dict[str, Any] = None,
        model: str = None,
        json_file: str = None
    ) -> JSONResponse:
        """
        Create standardized extraction success response.
        
        Args:
            formatted_data: Extracted and formatted data
            document_type: Type of document processed
            extraction_method: Method used for extraction
            file_info: File information
            tokens_used: Token usage information (optional)
            model: Model used (optional)
            json_file: Generated JSON file name (optional)
            
        Returns:
            JSONResponse with extraction-specific format
        """
        data = {
            "formatted_data": formatted_data,
            "document_type": document_type,
            "extraction_method": extraction_method
        }
        
        if json_file:
            data["json_file"] = json_file
            
        metadata = {
            "file_info": file_info
        }
        
        if tokens_used:
            metadata["tokens_used"] = tokens_used
            
        if model:
            metadata["model"] = model
            
        return APIResponse.success(
            data=data,
            message="Extraction completed successfully",
            metadata=metadata
        )
    
    @staticmethod
    def detection_success(
        is_acord: bool,
        is_fillable: bool,
        confidence: float,
        filename: str,
        form_type: str = None
    ) -> JSONResponse:
        """
        Create standardized detection success response.
        
        Args:
            is_acord: Whether document is ACORD form
            is_fillable: Whether document is fillable
            confidence: Detection confidence score
            filename: Original filename
            form_type: Detected form type (optional)
            
        Returns:
            JSONResponse with detection-specific format
        """
        data = {
            "is_acord": is_acord,
            "is_fillable": is_fillable,
            "confidence": confidence,
            "filename": filename
        }
        
        if form_type:
            data["form_type"] = form_type
            
        return APIResponse.success(
            data=data,
            message="Document detection completed successfully"
        )


# Convenience functions for common use cases
def success_response(data=None, message="Success", metadata=None):
    """Shorthand for success response"""
    return APIResponse.success(data, message, metadata)


def error_response(message, status_code=400, error_code=None, details=None):
    """Shorthand for error response"""
    return APIResponse.error(message, status_code, error_code, details)


def validation_error(message="Invalid input provided"):
    """Shorthand for validation error response"""
    return APIResponse.error(
        message=message,
        status_code=422,
        error_code="VALIDATION_ERROR"
    )


def server_error(message="Internal server error occurred"):
    """Shorthand for server error response"""
    return APIResponse.error(
        message=message,
        status_code=500,
        error_code="SERVER_ERROR"
    )