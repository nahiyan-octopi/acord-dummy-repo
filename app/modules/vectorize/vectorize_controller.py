"""Controller for vectorization endpoints."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import UploadFile

from app.modules.vectorize.vectorize_service import VectorizeService, get_vectorize_service

logger = logging.getLogger(__name__)


class VectorizeController:
    """Controller layer for vectorization endpoints."""

    def __init__(self, service: VectorizeService = None):
        self._service = service

    @property
    def service(self) -> VectorizeService:
        if self._service is None:
            self._service = get_vectorize_service()
        return self._service

    async def vectorize_pdf(self, file: UploadFile) -> Dict[str, Any]:
        try:
            if file is None:
                raise ValueError("No file provided")

            if not file.filename:
                raise ValueError("Invalid file. Missing filename")

            if not file.filename.lower().endswith('.pdf'):
                raise ValueError("Invalid file type. Only PDF files are supported")

            result = await self.service.vectorize_pdf(file)
            result['timestamp'] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def vectorize_query(self, query: str) -> Dict[str, Any]:
        try:
            result = self.service.vectorize_query(query)
            result['timestamp'] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:
            logger.error(f"Query vectorization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


_vectorize_controller: Optional[VectorizeController] = None


def get_vectorize_controller() -> VectorizeController:
    global _vectorize_controller
    if _vectorize_controller is None:
        _vectorize_controller = VectorizeController()
    return _vectorize_controller
