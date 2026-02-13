"""Vectorize routes."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.modules.vectorize.vectorize_schemas import VectorizeByIdRequest
from app.modules.vectorize.vectorize_controller import VectorizeController, get_vectorize_controller

router = APIRouter(prefix='/api', tags=['vectorize'])


@router.post('/vectorize')
async def vectorize(
    request: VectorizeByIdRequest,
    controller: VectorizeController = Depends(get_vectorize_controller)
):
    """Fetch rows by IDs from DB, vectorize text, and store in OpenSearch."""
    result = await controller.vectorize(request)
    status_code = 200 if result.get('success') else 500
    return JSONResponse(status_code=status_code, content=result)
