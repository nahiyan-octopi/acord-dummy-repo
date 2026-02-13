"""Schemas for by-id vectorization requests."""
from pydantic import BaseModel, Field
from typing import Optional, List, Union


class VectorizeDBConfig(BaseModel):
    connection_string: str = Field(..., description="SQLAlchemy connection string")
    table_name: str = Field(..., description="Table name containing source rows")
    id_column: str = Field(default="id", description="ID column name")
    text_column: str = Field(default="text", description="Text column name")


class VectorizeByIdRequest(BaseModel):
    ids: List[Union[str, int]] = Field(..., min_length=1, description="IDs to fetch and vectorize")
    db: VectorizeDBConfig = Field(..., description="Database fetch configuration")
    index_name: Optional[str] = Field(default=None, description="Optional index override")
    source: Optional[str] = Field(default=None, description="Optional source label")
