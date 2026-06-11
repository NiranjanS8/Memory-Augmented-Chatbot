import logging
import sqlite3
import uuid
from datetime import datetime, timezone

import openai
from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)

_AUTO_TITLE_MODEL = "gpt-4o-mini"

_AUTO_TITLE_PROMPT = (
    "Generate a concise 4-6 word title for a conversation that starts with "
    "the following message. Return only the title, no quotes or punctuation.\n\n"
    "Message: {message}"
)


class Conversation(BaseModel):
    id: str
    user_id: str
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationStore:
    """SQLite-backed conversation and message persistence."""

    def __init__(self, db_path: str = "conversations.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._openai: openai.OpenAI | None = None

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
        """)

    def create_conversation(
        self, user_id: str, first_message: str, model: str,
    ) -> Conversation:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        title = first_message[:60] + ("..." if len(first_message) > 60 else "")

        self._conn.execute(
            "INSERT INTO conversations (id, user_id, title, model, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (conv_id, user_id, title, model, now.isoformat(), now.isoformat()),
        )
        self._conn.commit()

        return Conversation(
            id=conv_id,
            user_id=user_id,
            title=title,
            model=model,
            created_at=now,
            updated_at=now,
            message_count=0,
        )

    def append_message(self, conversation_id: str, role: str, content: str) -> None:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        self._conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, now.isoformat()),
        )
        self._conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now.isoformat(), conversation_id),
        )
        self._conn.commit()

    def list_conversations(self, user_id: str) -> list[Conversation]:
        rows = self._conn.execute(
            "SELECT c.*, COUNT(m.id) AS message_count "
            "FROM conversations c "
            "LEFT JOIN messages m ON m.conversation_id = c.id "
            "WHERE c.user_id = ? "
            "GROUP BY c.id "
            "ORDER BY c.updated_at DESC",
            (user_id,),
        ).fetchall()

        return [
            Conversation(
                id=row["id"],
                user_id=row["user_id"],
                title=row["title"],
                model=row["model"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                message_count=row["message_count"],
            )
            for row in rows
        ]

    def load_messages(self, conversation_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT role, content, created_at FROM messages "
            "WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()

        return [
            {"role": row["role"], "content": row["content"], "created_at": row["created_at"]}
            for row in rows
        ]

    def rename_conversation(self, conversation_id: str, title: str) -> None:
        self._conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conversation_id),
        )
        self._conn.commit()

    def delete_conversation(self, conversation_id: str) -> None:
        self._conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        self._conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        self._conn.commit()

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        row = self._conn.execute(
            "SELECT c.*, COUNT(m.id) AS message_count "
            "FROM conversations c "
            "LEFT JOIN messages m ON m.conversation_id = c.id "
            "WHERE c.id = ? "
            "GROUP BY c.id",
            (conversation_id,),
        ).fetchone()

        if not row:
            return None
        return Conversation(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            model=row["model"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            message_count=row["message_count"],
        )

    async def auto_title(self, conversation_id: str, first_message: str) -> str:
        """Generate a short title via a cheap LLM call and update the conversation.
        Designed to be called via asyncio.create_task (fire-and-forget)."""
        try:
            if self._openai is None:
                self._openai = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = _AUTO_TITLE_PROMPT.format(message=first_message[:200])
            response = self._openai.chat.completions.create(
                model=_AUTO_TITLE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=20,
            )
            title = response.choices[0].message.content.strip().strip('"\'')
            if title:
                self.rename_conversation(conversation_id, title)
                logger.info("Auto-titled conversation %s: %s", conversation_id[:8], title)
                return title
        except Exception as e:
            logger.warning("Auto-title failed for %s: %s", conversation_id[:8], e)

        return first_message[:60]

    def close(self) -> None:
        self._conn.close()
