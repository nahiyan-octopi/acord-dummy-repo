"""Vectorize routes."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.modules.vectorize.vectorize_schemas import VectorizeQueryRequest
from app.modules.vectorize.vectorize_controller import VectorizeController, get_vectorize_controller

router = APIRouter(prefix='/api', tags=['vectorize'])


@router.post('/vectorize')
async def vectorize(
    file: UploadFile = File(...),
    controller: VectorizeController = Depends(get_vectorize_controller)
):
    """Vectorize a single uploaded PDF into chunk-level embeddings."""
    result = await controller.vectorize_pdf(file)
    status_code = 200 if result.get('success') else 400
    return JSONResponse(status_code=status_code, content=result)


@router.post('/vectorize-query')
async def vectorize_query(
    request: VectorizeQueryRequest,
    controller: VectorizeController = Depends(get_vectorize_controller)
):
    """Vectorize query text using the same embedding model used for document chunks."""
    result = await controller.vectorize_query(request.query)
    status_code = 200 if result.get('success') else 400
    return JSONResponse(status_code=status_code, content=result)
