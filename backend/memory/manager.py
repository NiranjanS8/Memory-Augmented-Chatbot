import openai

from backend.config import settings
from backend.memory.retriever import MemoryRetriever
from backend.memory.types import MemoryRecord, MemoryType


def _openai_embed(text: str) -> list[float]:
    """All memory embeddings use OpenAI text-embedding-3-small regardless
    of which chat model is active. This keeps all vectors in the same
    embedding space so cosine similarity scores remain meaningful."""
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


# Cache to avoid re-creating the OpenAI client per call.
_embed_client: openai.OpenAI | None = None


def _get_embed_fn():
    global _embed_client
    if _embed_client is None:
        _embed_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed(text: str) -> list[float]:
        response = _embed_client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding

    return embed


class MemoryManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._embed_fn = _get_embed_fn()
        self.retriever = MemoryRetriever(
            user_id=user_id,
            embed_fn=self._embed_fn,
            store_path=settings.CHROMA_STORE_PATH,
        )

    def get_context(self, query: str) -> list[MemoryRecord]:
        """Retrieve relevant memories for injection into the system prompt.
        Returns top-5 semantic + top-2 episodic memories."""
        semantic = self.retriever.search(query, n_results=5, memory_type=MemoryType.SEMANTIC)
        episodic = self.retriever.search(query, n_results=2, memory_type=MemoryType.EPISODIC)

        records = []
        for record, _similarity in semantic + episodic:
            if record.confidence > 0.1:
                records.append(record)
        return records

    def store_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        source_session: str | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            user_id=self.user_id,
            memory_type=memory_type,
            content=content,
            source_session=source_session,
        )
        self.retriever.upsert(record)
        return record

    def list_memories(self) -> list[MemoryRecord]:
        return self.retriever.list_all()

    def clear_memories(self) -> None:
        self.retriever.clear()
