import json
import logging

import openai

from backend.config import settings
from backend.memory.retriever import MemoryRetriever
from backend.memory.types import MemoryRecord, MemoryType
from backend.memory.reconciler import MemoryReconciler
from backend.prompts.extraction import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

_EXTRACTION_MODEL = "gpt-4o-mini"

# Similarity threshold for triggering reconciliation instead of inserting new.
_RECONCILE_SIMILARITY_THRESHOLD = 0.85


class MemoryWriter:
    def __init__(self):
        self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def extract_and_store(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        retriever: MemoryRetriever,
        reconciler: MemoryReconciler,
        source_session: str | None = None,
    ) -> list[MemoryRecord]:
        facts = self._extract_facts(user_message, assistant_message)
        if not facts:
            return []

        stored = []
        for fact in facts:
            existing = retriever.search(fact, n_results=1, memory_type=MemoryType.SEMANTIC)
            if existing:
                existing_record, similarity = existing[0]
                if similarity >= _RECONCILE_SIMILARITY_THRESHOLD:
                    reconciled_record = reconciler.reconcile(existing_record, fact)
                    stored.append(reconciled_record)
                    continue

            record = MemoryRecord(
                user_id=user_id,
                memory_type=MemoryType.SEMANTIC,
                content=fact,
                source_session=source_session,
            )
            retriever.upsert(record)
            stored.append(record)
            logger.info("Stored memory for user %s: %s", user_id, fact)

        return stored

    def _extract_facts(self, user_message: str, assistant_message: str) -> list[str]:
        prompt = EXTRACTION_PROMPT.format(
            user_message=user_message,
            assistant_message=assistant_message,
        )
        try:
            response = self._client.chat.completions.create(
                model=_EXTRACTION_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=256,
            )
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            facts = parsed.get("facts", [])
            if not isinstance(facts, list):
                return []
            return [f for f in facts if isinstance(f, str) and f.strip()]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse extraction response: %s", e)
            return []
        except Exception as e:
            logger.error("Fact extraction failed: %s", e)
            return []
