"""Service for PDF and query vectorization."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import UploadFile

from app.services.ai.embedding_service import get_embedding_service
from app.services.pypdf_extractor import extract_text_content, extract_form_fields_for_structuring
from app.utils.utils import save_upload_file, cleanup_file, get_file_info


class VectorizeService:
    """Service layer for vectorization-only APIs."""

    CHUNK_SIZE = 1200
    CHUNK_OVERLAP = 150
    MIN_PAGE_TEXT_CHARS = 300

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
    def _build_doc_id(file_path: str, text: str) -> str:
        path = Path(file_path)
        try:
            file_size = path.stat().st_size
        except OSError:
            file_size = 0
        hash_source = f"{path.name}:{len(text)}:{file_size}"
        return sha256(hash_source.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _build_form_field_text(form_result: Dict[str, Any]) -> str:
        if not form_result or not form_result.get("success"):
            return ""

        data = form_result.get("data") or {}
        if not data:
            return ""

        lines: List[str] = []
        for key, value in data.items():
            key_text = str(key).strip()
            value_text = str(value).strip() if value is not None else ""
            if key_text and value_text:
                lines.append(f"{key_text}: {value_text}")

        return "\n".join(lines).strip()

    def _select_vector_text(self, page_text: str, form_text: str) -> Dict[str, Any]:
        normalized_page = (page_text or "").strip()
        normalized_form = (form_text or "").strip()

        page_len = len(normalized_page)
        form_len = len(normalized_form)

        if normalized_form and page_len < self.MIN_PAGE_TEXT_CHARS:
            return {
                "text": normalized_form,
                "strategy": "form_fields_only"
            }

        if normalized_form and normalized_page:
            merged = f"FORM_FIELDS\n{normalized_form}\n\nPAGE_TEXT\n{normalized_page}".strip()
            return {
                "text": merged,
                "strategy": "form_fields_plus_page_text"
            }

        if normalized_form:
            return {
                "text": normalized_form,
                "strategy": "form_fields_only"
            }

        return {
            "text": normalized_page,
            "strategy": "page_text_only"
        }

    async def vectorize_pdf(self, file: UploadFile) -> Dict[str, Any]:
        save_success, file_path = await save_upload_file(file)
        if not save_success:
            return {
                "success": False,
                "error": file_path
            }

        try:
            extraction = extract_text_content(file_path)
            if not extraction.get("success"):
                return {
                    "success": False,
                    "error": extraction.get("error", "Failed to extract PDF text")
                }

            form_extraction = extract_form_fields_for_structuring(file_path)
            form_text = self._build_form_field_text(form_extraction)

            selected_content = self._select_vector_text(
                page_text=(extraction.get("text") or ""),
                form_text=form_text
            )

            full_text = (selected_content.get("text") or "").strip()
            if not full_text:
                return {
                    "success": False,
                    "error": "No extractable text found in PDF"
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

            embedding_service = get_embedding_service()
            embeddings = embedding_service.embed_batch(chunks)

            file_info = get_file_info(file_path)
            created_at = datetime.now(timezone.utc).isoformat()
            doc_id = self._build_doc_id(file_path=file_path, text=full_text)

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
                    "metadata": {
                        "filename": file_info.get("filename"),
                        "file_size": file_info.get("file_size"),
                        "page_count": extraction.get("page_count", 0),
                        "extraction_method": extraction.get("extraction_method", "pypdf"),
                        "extraction_strategy": selected_content.get("strategy", "page_text_only"),
                        "form_field_count": form_extraction.get("field_count", 0) if isinstance(form_extraction, dict) else 0
                    }
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
