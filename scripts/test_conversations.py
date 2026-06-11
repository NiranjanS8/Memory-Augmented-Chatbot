"""Verifies conversation persistence: create, append, list, load, rename, delete."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import tempfile

from backend.conversations.store import ConversationStore


def _temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


def test_create_and_list():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        conv = store.create_conversation("user_1", "Hello, how are you?", "openai")
        assert conv.user_id == "user_1"
        assert conv.model == "openai"
        assert conv.title == "Hello, how are you?"
        assert conv.message_count == 0
        print(f"[PASS] Create conversation — id: {conv.id[:8]}...")

        convs = store.list_conversations("user_1")
        assert len(convs) == 1
        assert convs[0].id == conv.id
        print("[PASS] List conversations returns created conv")

        empty = store.list_conversations("user_2")
        assert len(empty) == 0
        print("[PASS] List conversations for other user is empty")
    finally:
        store.close()
        os.unlink(db_path)


def test_title_truncation():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        long_msg = "A" * 100
        conv = store.create_conversation("user_1", long_msg, "claude")
        assert len(conv.title) == 63  # 60 chars + "..."
        assert conv.title.endswith("...")
        print("[PASS] Long title truncated to 60 chars + ellipsis")
    finally:
        store.close()
        os.unlink(db_path)


def test_append_and_load_messages():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        conv = store.create_conversation("user_1", "Test conv", "openai")
        store.append_message(conv.id, "user", "What is Python?")
        store.append_message(conv.id, "assistant", "Python is a programming language.")
        store.append_message(conv.id, "user", "Tell me more")

        messages = store.load_messages(conv.id)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is Python?"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["content"] == "Tell me more"
        print("[PASS] Append and load messages in order")

        updated_conv = store.get_conversation(conv.id)
        assert updated_conv.message_count == 3
        print("[PASS] Message count updated to 3")
    finally:
        store.close()
        os.unlink(db_path)


def test_rename():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        conv = store.create_conversation("user_1", "Original title", "gemini")
        store.rename_conversation(conv.id, "Renamed Title")

        updated = store.get_conversation(conv.id)
        assert updated.title == "Renamed Title"
        print("[PASS] Rename conversation")
    finally:
        store.close()
        os.unlink(db_path)


def test_delete_cascades():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        conv = store.create_conversation("user_1", "To delete", "mistral")
        store.append_message(conv.id, "user", "Hello")
        store.append_message(conv.id, "assistant", "Hi there")

        store.delete_conversation(conv.id)

        assert store.get_conversation(conv.id) is None
        assert len(store.load_messages(conv.id)) == 0
        assert len(store.list_conversations("user_1")) == 0
        print("[PASS] Delete conversation cascades to messages")
    finally:
        store.close()
        os.unlink(db_path)


def test_ordering():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        c1 = store.create_conversation("user_1", "First conv", "openai")
        c2 = store.create_conversation("user_1", "Second conv", "claude")

        # Append to c1 so its updated_at is newer
        store.append_message(c1.id, "user", "New message")

        convs = store.list_conversations("user_1")
        assert len(convs) == 2
        assert convs[0].id == c1.id, "Most recently updated should be first"
        assert convs[1].id == c2.id
        print("[PASS] Conversations ordered by updated_at DESC")
    finally:
        store.close()
        os.unlink(db_path)


def test_multiple_users_isolated():
    db_path = _temp_db()
    store = ConversationStore(db_path=db_path)

    try:
        store.create_conversation("alice", "Alice's chat", "openai")
        store.create_conversation("alice", "Alice's second", "claude")
        store.create_conversation("bob", "Bob's chat", "gemini")

        assert len(store.list_conversations("alice")) == 2
        assert len(store.list_conversations("bob")) == 1
        assert len(store.list_conversations("charlie")) == 0
        print("[PASS] Conversations isolated per user")
    finally:
        store.close()
        os.unlink(db_path)


def main():
    tests = [
        test_create_and_list,
        test_title_truncation,
        test_append_and_load_messages,
        test_rename,
        test_delete_cascades,
        test_ordering,
        test_multiple_users_isolated,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
