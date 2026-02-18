"""Schemas for vectorization endpoints."""
from pydantic import BaseModel, Field


class VectorizeQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query text to vectorize")
