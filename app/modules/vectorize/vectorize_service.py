"""Service for PDF and query vectorization."""
import os
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, Any, List, Optional

from fastapi import UploadFile

from app.services.ai.embedding_service import get_embedding_service
from app.modules.extraction.extraction_service import ExtractionService
from app.utils.utils import cleanup_file


class VectorizeService:
    """Service layer for vectorization-only APIs."""

    CHUNK_SIZE = 1200
    CHUNK_OVERLAP = 150

    def __init__(self):
        self.extraction_service = ExtractionService()

    @staticmethod
    def _single_chunk_enabled() -> bool:
        value = os.getenv("VECTORIZE_SINGLE_CHUNK")
        if value is None:
            raise ValueError("VECTORIZE_SINGLE_CHUNK is not set in environment variables")

        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False

        raise ValueError("VECTORIZE_SINGLE_CHUNK must be a boolean value (true/false)")

    @staticmethod
    def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        normalized = (text or "").strip()
        if not normalized:
            return []

        if overlap >= chunk_size:
            raise ValueError("chunk overlap must be smaller than chunk size")

        chunks: List[str] = []
        stride = chunk_size - overlap
        start = 0
        text_len = len(normalized)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            start += stride

        return chunks

    @staticmethod
    def _build_doc_id(filename: str, text: str, file_size: int = 0) -> str:
        hash_source = f"{filename}:{len(text)}:{file_size}"
        return sha256(hash_source.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _build_text_from_formatted_data(formatted_data: Dict[str, Any]) -> str:
        if not isinstance(formatted_data, dict) or not formatted_data:
            return ""

        lines: List[str] = []

        def flatten(value: Any, prefix: str = "") -> None:
            if isinstance(value, dict):
                for key in sorted(value.keys()):
                    child = value.get(key)
                    next_prefix = f"{prefix}.{key}" if prefix else str(key)
                    flatten(child, next_prefix)
                return

            if isinstance(value, list):
                for index, item in enumerate(value):
                    next_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
                    flatten(item, next_prefix)
                return

            value_text = "" if value is None else str(value).strip()
            if value_text and prefix:
                lines.append(f"{prefix}: {value_text}")

        flatten(formatted_data)

        if not lines:
            return ""

        return "FORMATTED_DATA\n" + "\n".join(lines).strip()

    async def vectorize_pdf(self, file: UploadFile) -> Dict[str, Any]:
        """
        Vectorize a PDF by running it through the extract-data pipeline
        and then embedding the extracted formatted data.
        """
        file_path = None

        try:
            # Step 1: Run the existing extract-data pipeline
            extraction_result = await self.extraction_service.extract_data(file)
            file_path = extraction_result.get("file_path")

            if not extraction_result.get("success"):
                return {
                    "success": False,
                    "error": extraction_result.get("error", "Extraction failed")
                }

            # Step 2: Build embeddable text from the extracted formatted_data
            formatted_data = extraction_result.get("formatted_data", {})
            full_text = self._build_text_from_formatted_data(formatted_data)

            if not full_text:
                return {
                    "success": False,
                    "error": "No extractable text found in PDF"
                }

            # Step 3: Vectorize the extracted text
            single_chunk_mode = self._single_chunk_enabled()

            embedding_service = get_embedding_service()
            file_info = extraction_result.get("file_info", {})
            created_at = datetime.now(timezone.utc).isoformat()
            doc_id = self._build_doc_id(
                filename=file_info.get("filename", ""),
                text=full_text,
                file_size=file_info.get("file_size", 0)
            )

            base_metadata = {
                "filename": file_info.get("filename"),
                "file_size": file_info.get("file_size"),
                "document_type": extraction_result.get("document_type", "Document"),
                "extraction_method": extraction_result.get("extraction_method", "unknown"),
            }

            if single_chunk_mode:
                single_embedding = embedding_service.embed_batch([full_text])[0]
                has_embedding = any(value != 0.0 for value in single_embedding)

                return {
                    "success": True,
                    "doc_id": doc_id,
                    "embedding_model": embedding_service.config.MODEL,
                    "embedding_dimensions": embedding_service.config.DIMENSIONS,
                    "single_chunk_mode": True,
                    "file_info": file_info,
                    "text": full_text,
                    "embedding": single_embedding,
                    "created_at": created_at,
                    "has_embedding": has_embedding,
                    "metadata": base_metadata
                }

            chunks = self._chunk_text(
                text=full_text,
                chunk_size=self.CHUNK_SIZE,
                overlap=self.CHUNK_OVERLAP
            )

            if not chunks:
                return {
                    "success": False,
                    "error": "No chunks generated from PDF text"
                }

            embeddings = embedding_service.embed_batch(chunks)

            chunk_docs: List[Dict[str, Any]] = []
            embedded_chunks = 0

            for index, chunk_text in enumerate(chunks):
                vector = embeddings[index] if index < len(embeddings) else None
                has_embedding = vector is not None and any(value != 0.0 for value in vector)
                if has_embedding:
                    embedded_chunks += 1

                chunk_docs.append({
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}:{index}",
                    "chunk_index": index,
                    "text": chunk_text,
                    "embedding": vector,
                    "created_at": created_at,
                    "has_embedding": has_embedding,
                    "metadata": base_metadata
                })

            return {
                "success": True,
                "doc_id": doc_id,
                "embedding_model": embedding_service.config.MODEL,
                "embedding_dimensions": embedding_service.config.DIMENSIONS,
                "chunk_size": self.CHUNK_SIZE,
                "chunk_overlap": self.CHUNK_OVERLAP,
                "total_chunks": len(chunk_docs),
                "embedded_chunks": embedded_chunks,
                "failed_chunks": len(chunk_docs) - embedded_chunks,
                "file_info": file_info,
                "chunks": chunk_docs
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }
        finally:
            if file_path:
                cleanup_file(file_path)

    def vectorize_query(self, query: str) -> Dict[str, Any]:
        clean_query = (query or "").strip()
        if not clean_query:
            return {
                "success": False,
                "error": "Query text is required"
            }

        embedding_service = get_embedding_service()
        embedding = embedding_service.embed_batch([clean_query])[0]

        return {
            "success": True,
            "query": clean_query,
            "embedding": embedding,
            "embedding_model": embedding_service.config.MODEL,
            "embedding_dimensions": embedding_service.config.DIMENSIONS,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "has_embedding": any(value != 0.0 for value in embedding)
        }


_vectorize_service: Optional[VectorizeService] = None


def get_vectorize_service() -> VectorizeService:
    global _vectorize_service
    if _vectorize_service is None:
        _vectorize_service = VectorizeService()
    return _vectorize_service
