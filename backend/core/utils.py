"""
Utility functions for file handling and operations
"""
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any
from starlette.datastructures import UploadFile
from backend.config import Config


async def save_upload_file(file: UploadFile) -> Tuple[bool, str]:
    """
    Save uploaded file to uploads folder
    
    Args:
        file: UploadFile object from FastAPI
    
    Returns:
        Tuple of (success: bool, path_or_error: str)
    """
    try:
        # Validate file
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext != '.pdf':
            return False, f"Invalid file type. Only PDF files are allowed. Got: {file_ext}"
        
        # Create unique filename to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        
        # Ensure upload folder exists
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
        file_path = Config.UPLOAD_FOLDER / unique_filename
        
        # Save file
        contents = await file.read()
        
        # Check file size
        if len(contents) > Config.MAX_CONTENT_LENGTH:
            max_size_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_size_mb:.1f}MB"
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        return True, str(file_path)
        
    except Exception as e:
        return False, f"File save failed: {str(e)}"


def cleanup_file(file_path: str) -> bool:
    """
    Delete uploaded file after processing
    
    Args:
        file_path: Path to file to delete
    
    Returns:
        Success status
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Cleanup failed for {file_path}: {str(e)}")
        return False


def save_json_output(
    extraction_result: Dict[str, Any],
    filename: str = None
) -> Tuple[bool, str]:
    """
    Save extraction result as JSON file
    
    Args:
        extraction_result: Dictionary to save
        filename: Optional custom filename
    
    Returns:
        Tuple of (success: bool, file_path: str)
    """
    try:
        # Create output folder if not exists
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
            filename = f"extraction_{timestamp}.json"
        
        file_path = Config.OUTPUT_FOLDER / filename
        
        # Save JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(extraction_result, f, indent=2, ensure_ascii=False)
        
        return True, str(file_path)
        
    except Exception as e:
        return False, f"JSON save failed: {str(e)}"


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file
    
    Args:
        file_path: Path to file
    
    Returns:
        Dictionary with file information
    """
    try:
        path = Path(file_path)
        file_size = path.stat().st_size
        
        return {
            "filename": path.name,
            "path": str(path),
            "file_size": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "modified_time": datetime.fromtimestamp(
                path.stat().st_mtime
            ).isoformat()
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def allowed_file(filename: str) -> bool:
    """
    Check if file has allowed extension
    
    Args:
        filename: Filename to check
    
    Returns:
        True if allowed, False otherwise
    """
    return '.' in filename and \
           Path(filename).suffix.lower()[1:] in Config.ALLOWED_EXTENSIONS


def cleanup_old_files(folder_path: str, hours: int = 24) -> int:
    """
    Delete files older than specified hours
    
    Args:
        folder_path: Path to folder
        hours: Age threshold in hours
    
    Returns:
        Number of files deleted
    """
    try:
        import time
        
        folder = Path(folder_path)
        deleted_count = 0
        current_time = time.time()
        threshold = hours * 3600
        
        for file_path in folder.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > threshold:
                    file_path.unlink()
                    deleted_count += 1
        
        return deleted_count
        
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
        return 0


def get_available_output_files(limit: int = 100) -> list:
    """
    Get list of available output files
    
    Args:
        limit: Maximum number of files to return
    
    Returns:
        List of filenames
    """
    try:
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        
        files = list(Config.OUTPUT_FOLDER.glob('*.json'))
        # Sort by modification time, newest first
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "size_kb": round(f.stat().st_size / 1024, 2),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in files[:limit]
        ]
        
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        return []
