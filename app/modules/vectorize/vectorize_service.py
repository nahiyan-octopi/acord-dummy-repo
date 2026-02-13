"""
Vectorize service for by-id DB fetch payloads.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import re

from opensearchpy import OpenSearch, helpers
from sqlalchemy import create_engine, text, bindparam

from app.config.opensearch_config import OpenSearchConfig, GENERIC_VECTOR_INDEX_MAPPING
from app.services.ai.embedding_service import get_embedding_service


class VectorizeService:
    """Service layer for by-id DB vectorization and indexing."""

    def __init__(self):
        self._client: Optional[OpenSearch] = None
        self._default_index_name = OpenSearchConfig.INDEX_GENERIC_VECTORS

    @property
    def client(self) -> OpenSearch:
        if self._client is None:
            config = OpenSearchConfig.get_connection_config()
            self._client = OpenSearch(
                hosts=config['hosts'],
                http_auth=config['http_auth'],
                use_ssl=config['use_ssl'],
                verify_certs=config['verify_certs'],
                ssl_show_warn=config['ssl_show_warn'],
                timeout=config['timeout'],
                retry_on_timeout=config['retry_on_timeout'],
                max_retries=config['max_retries']
            )
        return self._client

    def _ensure_index(self, index_name: str) -> None:
        if self.client.indices.exists(index=index_name):
            return

        body = OpenSearchConfig.get_index_settings()
        body.update(GENERIC_VECTOR_INDEX_MAPPING)
        self.client.indices.create(index=index_name, body=body)

    def _validate_identifier(self, value: str, field_name: str) -> str:
        if not value or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError(f"Invalid {field_name}: {value}")
        return value

    def _fetch_texts_by_ids(self, ids: List[Any], db_config: Dict[str, Any]) -> Dict[str, str]:
        connection_string = (db_config or {}).get('connection_string')
        table_name = self._validate_identifier((db_config or {}).get('table_name', ''), 'table_name')
        id_column = self._validate_identifier((db_config or {}).get('id_column', 'id'), 'id_column')
        text_column = self._validate_identifier((db_config or {}).get('text_column', 'text'), 'text_column')

        if not connection_string:
            raise ValueError('db.connection_string is required')

        engine = create_engine(connection_string, pool_pre_ping=True)
        try:
            stmt = text(
                f"SELECT {id_column} AS doc_id, {text_column} AS text_value "
                f"FROM {table_name} WHERE {id_column} IN :ids"
            ).bindparams(bindparam('ids', expanding=True))

            with engine.connect() as conn:
                rows = conn.execute(stmt, {'ids': list(ids)}).mappings().all()

            result: Dict[str, str] = {}
            for row in rows:
                doc_id = str(row.get('doc_id'))
                text_value = row.get('text_value')
                if text_value is None:
                    continue
                text_str = str(text_value).strip()
                if text_str:
                    result[doc_id] = text_str
            return result
        finally:
            engine.dispose()

    def vectorize_by_ids(self, ids: List[Any], db_config: Dict[str, Any], index_name: Optional[str] = None, source: Optional[str] = None) -> Dict[str, Any]:
        target_index = index_name or self._default_index_name
        self._ensure_index(target_index)

        normalized_ids = [str(value) for value in ids]
        text_map = self._fetch_texts_by_ids(ids=ids, db_config=db_config)

        found_ids = [doc_id for doc_id in normalized_ids if doc_id in text_map]
        missing_ids = [doc_id for doc_id in normalized_ids if doc_id not in text_map]

        if not found_ids:
            return {
                'success': False,
                'indexed_count': 0,
                'failed_count': 0,
                'fetched_count': 0,
                'missing_ids': missing_ids,
                'index_name': target_index,
                'errors': [{'error': 'No matching rows found for provided IDs'}]
            }

        texts = [text_map[doc_id] for doc_id in found_ids]
        embeddings = get_embedding_service().embed_batch(texts)

        actions = []
        for idx, doc_id in enumerate(found_ids):
            vector = embeddings[idx] if idx < len(embeddings) else None
            full_text = texts[idx]

            doc = {
                'doc_id': doc_id,
                'text': full_text,
                'full_text': full_text,
                'metadata': {
                    'table_name': db_config.get('table_name'),
                    'id_column': db_config.get('id_column', 'id'),
                    'text_column': db_config.get('text_column', 'text')
                },
                'source': source,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'has_embedding': vector is not None
            }

            if vector is not None:
                doc['embedding'] = vector

            actions.append({
                '_index': target_index,
                '_id': doc_id,
                '_source': doc
            })

        indexed_count = 0
        failed_count = 0

        if actions:
            indexed_count, failed_count = helpers.bulk(
                self.client,
                actions,
                stats_only=True,
                request_timeout=300
            )

        return {
            'success': failed_count == 0,
            'indexed_count': indexed_count,
            'failed_count': failed_count,
            'fetched_count': len(found_ids),
            'missing_ids': missing_ids,
            'index_name': target_index,
            'errors': []
        }


_vectorize_service: Optional[VectorizeService] = None


def get_vectorize_service() -> VectorizeService:
    global _vectorize_service
    if _vectorize_service is None:
        _vectorize_service = VectorizeService()
    return _vectorize_service
