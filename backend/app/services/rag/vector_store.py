from __future__ import annotations

import json
import logging
import uuid
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import settings
from app.services.rag.embedding import embedding_service
from app.vectorstore.store import Document

_LOGGER = logging.getLogger(__name__)


def _uuid_from_text(text: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, text))


@dataclass(frozen=True)
class QdrantConfig:
    url: str
    api_key: str
    collection: str
    timeout_s: float


class QdrantVectorStore:
    def __init__(self, config: QdrantConfig) -> None:
        self._config = config
        self._vector_size: Optional[int] = None
        self._named_vector: Optional[bool] = None
        self._vector_name: str = "dense"

    @property
    def collection_name(self) -> str:
        return self._config.collection

    def _request(self, *, method: str, path: str, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        url = f"{self._config.url}{path}"
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["api-key"] = self._config.api_key
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=self._config.timeout_s) as resp:
            raw = resp.read().decode("utf-8")
        parsed = json.loads(raw) if raw else {}
        return parsed if isinstance(parsed, dict) else {}

    def is_available(self) -> bool:
        try:
            self._request(method="GET", path="/collections")
            return True
        except Exception:
            return False

    def _collection_exists(self) -> bool:
        try:
            resp = self._request(method="GET", path=f"/collections/{self._config.collection}")
            return bool(resp.get("result"))
        except Exception:
            return False

    def _collection_vector_size(self) -> Optional[int]:
        try:
            resp = self._request(method="GET", path=f"/collections/{self._config.collection}")
            result = resp.get("result")
            if not isinstance(result, dict):
                return None
            config = result.get("config")
            if not isinstance(config, dict):
                return None
            params = config.get("params")
            if not isinstance(params, dict):
                return None
            vectors = params.get("vectors")
            if isinstance(vectors, dict) and isinstance(vectors.get("size"), int):
                self._named_vector = False
                return int(vectors["size"])
            if isinstance(vectors, dict):
                for name, spec in vectors.items():
                    if not isinstance(spec, dict):
                        continue
                    size = spec.get("size")
                    if isinstance(size, int):
                        self._named_vector = True
                        self._vector_name = str(name)
                        return int(size)
            return None
        except Exception:
            return None

    def ensure_collection(self, vector_size: int) -> None:
        self._vector_size = vector_size
        if self._collection_exists():
            existing_size = self._collection_vector_size()
            if existing_size is not None and int(existing_size) != int(vector_size):
                raise RuntimeError(
                    f"Qdrant collection '{self._config.collection}' vector size mismatch: "
                    f"existing={existing_size}, new={vector_size}. "
                    "Use a new QDRANT_COLLECTION or delete/recreate the collection."
                )
            return
        self._named_vector = True
        self._vector_name = "dense"
        payload = {
            "vectors": {self._vector_name: {"size": vector_size, "distance": "Cosine"}},
            "sparse_vectors": {"sparse": {"index": {"full_scan_threshold": 200}, "modifier": "IDF"}},
        }
        try:
            self._request(method="PUT", path=f"/collections/{self._config.collection}", payload=payload)
        except Exception:
            self._named_vector = False
            payload = {"vectors": {"size": vector_size, "distance": "Cosine"}}
            self._request(method="PUT", path=f"/collections/{self._config.collection}", payload=payload)

    def delete_collection(self) -> None:
        try:
            self._request(method="DELETE", path=f"/collections/{self._config.collection}")
        except Exception:
            return
        self._vector_size = None
        self._named_vector = None

    def count(self) -> int:
        if not self._collection_exists():
            return 0
        resp = self._request(
            method="POST",
            path=f"/collections/{self._config.collection}/points/count",
            payload={"exact": True},
        )
        result = resp.get("result")
        if isinstance(result, dict) and isinstance(result.get("count"), int):
            return int(result["count"])
        return 0

    def upsert_documents(self, docs: list[Document]) -> None:
        docs = [d for d in docs if isinstance(d, Document) and d.text.strip()]
        if not docs:
            return
        vectors = embedding_service.embed_texts([d.text for d in docs])
        if not vectors:
            return
        self.ensure_collection(vector_size=len(vectors[0]))
        sparse_vectors = embedding_service.create_sparse_embeddings_batch([d.text for d in docs])
        points: list[dict[str, Any]] = []
        for doc, vec, sparse in zip(docs, vectors, sparse_vectors):
            vector_payload: Any
            if self._named_vector:
                vector_payload = {self._vector_name: vec}
            else:
                vector_payload = vec
            points.append(
                {
                    "id": _uuid_from_text(doc.id),
                    "vector": vector_payload,
                    "payload": {
                        "doc_id": doc.id,
                        "text": doc.text,
                        "source": doc.source,
                        "metadata": doc.metadata,
                    },
                    "sparse_vectors": {"sparse": sparse},
                }
            )
        try:
            self._request(
                method="PUT",
                path=f"/collections/{self._config.collection}/points?wait=true",
                payload={"points": points},
            )
        except Exception:
            dense_only_points: list[dict[str, Any]] = []
            for p in points:
                dense_only_points.append({k: v for k, v in p.items() if k != "sparse_vectors"})
            self._request(
                method="PUT",
                path=f"/collections/{self._config.collection}/points?wait=true",
                payload={"points": dense_only_points},
            )

    def search(self, *, query: str, top_k: int, source: Optional[str] = None) -> list[tuple[Document, float]]:
        qv = embedding_service.embed_text(query)
        self.ensure_collection(vector_size=len(qv))
        flt = None
        if source is not None:
            flt = {"must": [{"key": "source", "match": {"value": source}}]}
        query_vector: Any
        if self._named_vector:
            query_vector = {"vector": qv, "name": self._vector_name}
        else:
            query_vector = qv
        payload: dict[str, Any] = {
            "vector": query_vector,
            "limit": int(top_k),
            "with_payload": True,
        }
        if flt is not None:
            payload["filter"] = flt
        resp = self._request(
            method="POST",
            path=f"/collections/{self._config.collection}/points/search",
            payload=payload,
        )
        result = resp.get("result")
        if not isinstance(result, list):
            return []
        out: list[tuple[Document, float]] = []
        for hit in result:
            if not isinstance(hit, dict):
                continue
            score = float(hit.get("score", 0.0))
            pl = hit.get("payload") or {}
            if not isinstance(pl, dict):
                continue
            doc_id = str(pl.get("doc_id") or "")
            text = str(pl.get("text") or "")
            src = str(pl.get("source") or "")
            raw_meta_any = pl.get("metadata")
            raw_meta: dict[Any, Any] = raw_meta_any if isinstance(raw_meta_any, dict) else {}
            meta: dict[str, object] = {str(k): v for k, v in raw_meta.items()}
            out.append((Document(id=doc_id, text=text, source=src, metadata=meta), score))
        return out


qdrant_store = QdrantVectorStore(
    QdrantConfig(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection=settings.qdrant_collection,
        timeout_s=max(0.2, float(settings.qdrant_timeout_s)),
    )
)
