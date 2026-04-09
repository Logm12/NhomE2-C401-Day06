from __future__ import annotations

import json
import logging
import math
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import settings

_LOGGER = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^0-9A-Za-zÀ-ỹ]+", text.lower()) if t]


class HashingEmbedder:
    def __init__(self, dim: int) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokenize(text):
            h = 2166136261
            for c in tok.encode("utf-8"):
                h ^= c
                h = (h * 16777619) % 2**32
            idx = int(h % self.dim)
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


@dataclass
class EmbeddingService:
    embed_model_name: str
    fallback_dim: int
    api_key: str
    endpoint: str
    timeout_s: float

    def __post_init__(self) -> None:
        self._fallback = HashingEmbedder(dim=self.fallback_dim)
        self._dense_model: Any = None
        self._sparse_model: Any = None
        self.embedding_dimension: int = self.fallback_dim
        self._initialize_local_models()

    def _initialize_local_models(self) -> None:
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except Exception:
            return

        device = "cpu"
        try:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
        except Exception:
            device = "cpu"

        try:
            dtype = torch.bfloat16 if device == "cuda" else torch.float32
            trust_remote_code = bool(re.search(r"\bqwen\b", self.embed_model_name, flags=re.IGNORECASE))
            self._dense_model = SentenceTransformer(
                self.embed_model_name,
                device=device,
                model_kwargs={"dtype": dtype, "attn_implementation": "sdpa"},
                tokenizer_kwargs={"padding_side": "left", "model_max_length": 1024},
                cache_folder="./model_cache",
                trust_remote_code=trust_remote_code,
                backend="torch",
            )
            dim = int(self._dense_model.get_sentence_embedding_dimension())
            if dim > 0:
                self.embedding_dimension = dim
        except Exception as e:
            _LOGGER.info("embedding_local_dense_failed: %s", str(e))
            self._dense_model = None

        try:
            from fastembed import SparseTextEmbedding

            self._sparse_model = SparseTextEmbedding("Qdrant/bm25")
        except Exception as e:
            _LOGGER.info("embedding_local_sparse_failed: %s", str(e))
            self._sparse_model = None

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.endpoint}/embeddings"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw)

    def _remote_embeddings(self, texts: list[str]) -> Optional[list[list[float]]]:
        if not self.api_key:
            return None
        try:
            payload = {"model": self.embed_model_name, "input": texts}
            data = self._request(payload)
            items = data.get("data")
            if not isinstance(items, list):
                return None
            out: list[list[float]] = []
            for it in items:
                if not isinstance(it, dict):
                    return None
                emb = it.get("embedding")
                if not isinstance(emb, list) or not emb:
                    return None
                out.append([float(x) for x in emb])
            if len(out) != len(texts):
                return None
            return out
        except Exception as e:
            _LOGGER.info("embedding_remote_failed: %s", str(e))
            return None

    def _local_dense_embeddings(self, texts: list[str]) -> Optional[list[list[float]]]:
        if self._dense_model is None:
            return None
        try:
            embs = self._dense_model.encode(
                texts,
                batch_size=128,
                show_progress_bar=False,
                convert_to_tensor=True,
                normalize_embeddings=True,
                precision="float32",
            )
            return embs.tolist()
        except Exception as e:
            _LOGGER.info("embedding_local_dense_encode_failed: %s", str(e))
            return None

    def embed_text(self, text: str) -> list[float]:
        batch = self.embed_texts([text])
        return batch[0] if batch else self._fallback.embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if not texts:
            return []
        local = self._local_dense_embeddings(texts)
        if local is not None:
            return local
        remote = self._remote_embeddings(texts)
        if remote is not None:
            return remote
        return [self._fallback.embed(t) for t in texts]

    def create_sparse_embedding(self, text: str) -> dict[str, list[float] | list[int]]:
        if self._sparse_model is None:
            return {"indices": [], "values": []}
        try:
            sparse_embedding = list(self._sparse_model.embed([text]))[0]
            return {"indices": sparse_embedding.indices.tolist(), "values": sparse_embedding.values.tolist()}
        except Exception as e:
            _LOGGER.info("embedding_local_sparse_encode_failed: %s", str(e))
            return {"indices": [], "values": []}

    def create_sparse_embeddings_batch(self, texts: list[str], batch_size: int = 128) -> list[dict[str, list[float] | list[int]]]:
        if self._sparse_model is None:
            return [{"indices": [], "values": []} for _ in texts]
        try:
            result = self._sparse_model.embed(texts, batch_size=batch_size)
            return [{"indices": se.indices.tolist(), "values": se.values.tolist()} for se in result]
        except Exception as e:
            _LOGGER.info("embedding_local_sparse_batch_failed: %s", str(e))
            return [{"indices": [], "values": []} for _ in texts]


embedding_service = EmbeddingService(
    embed_model_name=settings.embed_model_name,
    fallback_dim=settings.embed_dim,
    api_key=settings.api_key,
    endpoint=settings.endpoint,
    timeout_s=min(settings.timeout_s, 20.0),
)
