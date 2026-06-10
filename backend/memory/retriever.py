from collections.abc import Callable
from datetime import datetime, timezone

import chromadb

from backend.memory.types import MemoryRecord, MemoryType


class MemoryRetriever:
    """Wraps ChromaDB for memory storage and semantic search.

    Each user gets their own collection. The embed_fn is injected by
    MemoryManager so we can enforce a single embedding model (OpenAI
    text-embedding-3-small) across all providers.
    """

    def __init__(self, user_id: str, embed_fn: Callable[[str], list[float]], store_path: str = ".chroma_store"):
        self._embed = embed_fn
        self._client = chromadb.PersistentClient(path=store_path)
        self._collection = self._client.get_or_create_collection(
            name=f"memories_{user_id}",
            metadata={"hnsw:space": "cosine"},
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        memory_type: MemoryType | None = None,
    ) -> list[tuple[MemoryRecord, float]]:
        query_embedding = self._embed(query)
        where = {"memory_type": memory_type.value} if memory_type else None

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        records = []
        for doc_id, document, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            record = MemoryRecord(
                id=doc_id,
                user_id=metadata["user_id"],
                memory_type=MemoryType(metadata["memory_type"]),
                content=document,
                confidence=metadata.get("confidence", 1.0),
                access_count=metadata.get("access_count", 0),
                source_session=metadata.get("source_session"),
                superseded_by=metadata.get("superseded_by"),
            )
            # Cosine distance: 0 = identical, 2 = opposite. Convert to similarity.
            similarity = 1.0 - distance
            records.append((record, similarity))

        return records

    def upsert(self, record: MemoryRecord) -> None:
        if record.embedding is None:
            record.embedding = self._embed(record.content)

        metadata = {
            "user_id": record.user_id,
            "memory_type": record.memory_type.value,
            "confidence": record.confidence,
            "access_count": record.access_count,
            "created_at": record.created_at.isoformat(),
        }
        if record.source_session:
            metadata["source_session"] = record.source_session
        if record.superseded_by:
            metadata["superseded_by"] = record.superseded_by
        if record.last_accessed:
            metadata["last_accessed"] = record.last_accessed.isoformat()

        self._collection.upsert(
            ids=[record.id],
            embeddings=[record.embedding],
            documents=[record.content],
            metadatas=[metadata],
        )

    def delete(self, record_id: str) -> None:
        self._collection.delete(ids=[record_id])

    def clear(self) -> None:
        """Remove all documents from this user's collection."""
        all_ids = self._collection.get()["ids"]
        if all_ids:
            self._collection.delete(ids=all_ids)

    def list_all(self) -> list[MemoryRecord]:
        results = self._collection.get(include=["documents", "metadatas"])
        if not results["ids"]:
            return []

        records = []
        for doc_id, document, metadata in zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
        ):
            records.append(MemoryRecord(
                id=doc_id,
                user_id=metadata["user_id"],
                memory_type=MemoryType(metadata["memory_type"]),
                content=document,
                confidence=metadata.get("confidence", 1.0),
                access_count=metadata.get("access_count", 0),
                source_session=metadata.get("source_session"),
                superseded_by=metadata.get("superseded_by"),
            ))
        return records
