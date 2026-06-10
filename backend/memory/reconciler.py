import json
import logging
from datetime import datetime, timezone

import openai

from backend.config import settings
from backend.memory.retriever import MemoryRetriever
from backend.memory.types import MemoryRecord, MemoryType

logger = logging.getLogger(__name__)

_JUDGE_MODEL = "gpt-4o-mini"

_CONTRADICTION_PROMPT = """\
Given two statements about the same user, determine their relationship.

Old fact: {old_fact}
New fact: {new_fact}

Respond with JSON only: {{"relationship": "consistent" | "contradiction" | "refinement"}}

- "consistent": both can be true simultaneously
- "contradiction": they cannot both be true (e.g. "uses Python" vs "switched to Go")
- "refinement": new fact is a more specific version of the old"""


class MemoryReconciler:
    def __init__(self, retriever: MemoryRetriever):
        self._retriever = retriever
        self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def reconcile(self, existing: MemoryRecord, new_fact: str) -> MemoryRecord:
        """Compare a new fact against an existing memory and handle accordingly."""
        relationship = self._classify(existing.content, new_fact)

        if relationship == "contradiction":
            return self._handle_contradiction(existing, new_fact)
        elif relationship == "refinement":
            return self._handle_refinement(existing, new_fact)
        else:
            return self._handle_consistent(existing)

    def _handle_contradiction(self, existing: MemoryRecord, new_fact: str) -> MemoryRecord:
        new_record = MemoryRecord(
            user_id=existing.user_id,
            memory_type=MemoryType.SEMANTIC,
            content=new_fact,
            confidence=1.0,
        )
        self._retriever.upsert(new_record)

        existing.superseded_by = new_record.id
        existing.confidence = 0.1
        self._retriever.upsert(existing)

        logger.info(
            "Contradiction: deprecated '%s' (conf=0.1), stored '%s'",
            existing.content, new_fact,
        )
        return new_record

    def _handle_refinement(self, existing: MemoryRecord, new_fact: str) -> MemoryRecord:
        new_record = MemoryRecord(
            user_id=existing.user_id,
            memory_type=MemoryType.SEMANTIC,
            content=new_fact,
            confidence=1.0,
        )
        self._retriever.upsert(new_record)

        existing.superseded_by = new_record.id
        existing.confidence = 0.3
        self._retriever.upsert(existing)

        logger.info("Refinement: '%s' replaced by '%s'", existing.content, new_fact)
        return new_record

    def _handle_consistent(self, existing: MemoryRecord) -> MemoryRecord:
        existing.access_count += 1
        existing.last_accessed = datetime.now(timezone.utc)
        self._retriever.upsert(existing)
        return existing

    def _classify(self, old_fact: str, new_fact: str) -> str:
        prompt = _CONTRADICTION_PROMPT.format(old_fact=old_fact, new_fact=new_fact)
        try:
            response = self._client.chat.completions.create(
                model=_JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=64,
            )
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            relationship = parsed.get("relationship", "consistent")
            if relationship in ("consistent", "contradiction", "refinement"):
                return relationship
            return "consistent"
        except Exception as e:
            logger.warning("Reconciliation classification failed: %s", e)
            return "consistent"
