"""
OpenSearch configuration for generic vectorization.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)


class OpenSearchConfig:
    """OpenSearch Configuration Settings"""

    OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
    OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', 9200))
    OPENSEARCH_SCHEME = os.getenv('OPENSEARCH_SCHEME', 'http')

    OPENSEARCH_USERNAME = os.getenv('OPENSEARCH_USERNAME', '')
    OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_PASSWORD', '')

    OPENSEARCH_VERIFY_CERTS = os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
    OPENSEARCH_SSL_SHOW_WARN = os.getenv('OPENSEARCH_SSL_SHOW_WARN', 'false').lower() == 'true'

    INDEX_GENERIC_VECTORS = os.getenv('OPENSEARCH_INDEX_GENERIC_VECTORS', 'generic_vectors')

    SEARCH_TIMEOUT = int(os.getenv('OPENSEARCH_SEARCH_TIMEOUT', 120))
    VECTOR_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', 1024))

    @classmethod
    def get_connection_config(cls) -> Dict[str, Any]:
        auth = None
        if cls.OPENSEARCH_USERNAME:
            auth = (cls.OPENSEARCH_USERNAME, cls.OPENSEARCH_PASSWORD)

        return {
            'hosts': [{'host': cls.OPENSEARCH_HOST, 'port': cls.OPENSEARCH_PORT}],
            'http_auth': auth,
            'use_ssl': cls.OPENSEARCH_SCHEME == 'https',
            'verify_certs': cls.OPENSEARCH_VERIFY_CERTS,
            'ssl_show_warn': cls.OPENSEARCH_SSL_SHOW_WARN,
            'timeout': cls.SEARCH_TIMEOUT,
            'retry_on_timeout': True,
            'max_retries': 3
        }

    @classmethod
    def get_index_settings(cls) -> Dict[str, Any]:
        return {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index": {
                    "knn": True
                },
                "analysis": {
                    "analyzer": {
                        "default_text": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    },
                    "normalizer": {
                        "lowercase_normalizer": {
                            "type": "custom",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    }
                }
            }
        }


GENERIC_VECTOR_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "text": {
                "type": "text",
                "analyzer": "default_text",
                "fields": {
                    "keyword": {"type": "keyword", "normalizer": "lowercase_normalizer"}
                }
            },
            "full_text": {"type": "text", "analyzer": "default_text"},
            "payload": {"type": "object", "enabled": True},
            "metadata": {"type": "object", "enabled": True},
            "source": {"type": "keyword"},
            "created_at": {"type": "date"},
            "embedding": {
                "type": "knn_vector",
                "dimension": OpenSearchConfig.VECTOR_DIMENSIONS,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                    "parameters": {
                        "ef_construction": 256,
                        "m": 16
                    }
                }
            },
            "has_embedding": {"type": "boolean"}
        }
    }
}
