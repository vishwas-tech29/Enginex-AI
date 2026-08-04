import logging
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.ai.rag.embeddings import BaseEmbedder
from app.config import settings

logger = logging.getLogger("enginex.ai.rag")

KNOWLEDGE_COLLECTIONS = [
    "datasheets",
    "standards",
    "reference_designs",
    "app_notes",
    "company_knowledge",
]


class RAGService:
    """Retrieval-augmented generation over engineering knowledge collections."""

    def __init__(self, embedder: BaseEmbedder, client: AsyncQdrantClient | None = None):
        self.embedder = embedder
        # `location` accepts both ":memory:" and a real "http(s)://host:port"
        # URL — unlike the `url=` kwarg, which rejects ":memory:".
        self.client = client or AsyncQdrantClient(location=settings.qdrant_url)
        self._ensured: set[str] = set()

    async def _ensure_collection(self, collection: str) -> None:
        if collection in self._ensured:
            return
        if not await self.client.collection_exists(collection):
            await self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=self.embedder.dimensions, distance=Distance.COSINE),
            )
        self._ensured.add(collection)

    async def index_documents(self, collection: str, documents: list[dict]) -> int:
        await self._ensure_collection(collection)

        points = [
            PointStruct(
                id=doc.get("id") or str(uuid.uuid4()),
                vector=self.embedder.embed(doc["content"]),
                payload={
                    "title": doc.get("title", ""),
                    "source": doc.get("source", ""),
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                },
            )
            for doc in documents
        ]
        await self.client.upsert(collection_name=collection, points=points)
        logger.info("rag_indexed", extra={"collection": collection, "count": len(points)})
        return len(points)

    async def search(self, query: str, collection: str, limit: int = 5, score_threshold: float = 0.0) -> list[dict]:
        await self._ensure_collection(collection)

        result = await self.client.query_points(
            collection_name=collection,
            query=self.embedder.embed(query),
            limit=limit,
            score_threshold=score_threshold or None,
        )
        return [
            {
                "title": point.payload.get("title"),
                "source": point.payload.get("source"),
                "content": point.payload.get("content"),
                "score": point.score,
                "metadata": point.payload.get("metadata", {}),
            }
            for point in result.points
        ]

    async def search_all_collections(self, query: str, limit: int = 3) -> dict[str, list[dict]]:
        results = {}
        for collection in KNOWLEDGE_COLLECTIONS:
            results[collection] = await self.search(query, collection, limit)
        return results
