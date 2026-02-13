"""Controller for vectorization endpoints."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.modules.vectorize.vectorize_schemas import VectorizeByIdRequest
from app.modules.vectorize.vectorize_service import VectorizeService, get_vectorize_service

logger = logging.getLogger(__name__)


class VectorizeController:
    """Controller layer for generic vectorization."""

    def __init__(self, service: VectorizeService = None):
        self._service = service

    @property
    def service(self) -> VectorizeService:
        if self._service is None:
            self._service = get_vectorize_service()
        return self._service

    async def vectorize(self, request: VectorizeByIdRequest) -> Dict[str, Any]:
        try:
            result = self.service.vectorize_by_ids(
                ids=request.ids,
                db_config=request.db.model_dump(),
                index_name=request.index_name,
                source=request.source
            )
            result['timestamp'] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
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
