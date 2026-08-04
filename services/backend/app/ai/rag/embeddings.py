import hashlib
import math
import re
from abc import ABC, abstractmethod

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class BaseEmbedder(ABC):
    dimensions: int

    @abstractmethod
    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder(BaseEmbedder):
    """Deterministic, dependency-free embedding via the hashing trick.

    Real semantic embeddings (OpenAI/Cohere/etc.) need a network call and an
    API key. This needs neither, so RAG indexing/search is fully exercisable
    in dev and CI: word-overlap between documents pulls their vectors
    closer, which is enough to prove retrieval plumbing works end to end.
    Swap in a real embedding provider before relying on this for actual
    semantic quality — see docs/architecture/ai-agents.md.
    """

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]
