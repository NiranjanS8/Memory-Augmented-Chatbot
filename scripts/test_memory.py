"""Verifies memory storage and retrieval via ChromaDB."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
import gc
import time
from backend.memory.manager import MemoryManager
from backend.memory.types import MemoryType

TEST_STORE_PATH = ".chroma_test"
TEST_USER = "test_user_001"

# Ref held at module level so we can close it before cleanup.
_manager: MemoryManager | None = None


def cleanup():
    global _manager
    # Release ChromaDB's SQLite handle before deleting the directory.
    if _manager is not None:
        _manager.retriever._collection = None
        _manager.retriever._client = None
        _manager = None
    gc.collect()
    time.sleep(0.2)

    store = Path(TEST_STORE_PATH)
    if store.exists():
        shutil.rmtree(store, ignore_errors=True)


def test_store_and_retrieve():
    global _manager
    from backend.config import settings
    settings.CHROMA_STORE_PATH = TEST_STORE_PATH

    mgr = MemoryManager(TEST_USER)
    _manager = mgr

    mgr.store_memory("User prefers TypeScript over JavaScript")
    mgr.store_memory("User is building a SaaS product in healthcare")
    mgr.store_memory("User has a dog named Max")

    stored = mgr.list_memories()
    print(f"Stored {len(stored)} memories")
    assert len(stored) == 3, f"Expected 3, got {len(stored)}"

    results = mgr.retriever.search("What programming language does the user like?", n_results=3)
    print(f"\nSearch: 'What programming language does the user like?'")
    for record, similarity in results:
        print(f"  [{similarity:.3f}] {record.content}")

    top_record, top_similarity = results[0]
    assert "TypeScript" in top_record.content, f"Expected TypeScript fact, got: {top_record.content}"
    assert top_similarity > 0.3, f"Similarity too low: {top_similarity}"

    context = mgr.get_context("Tell me about the user's project")
    print(f"\nget_context returned {len(context)} memories for 'Tell me about the user\\'s project'")
    for r in context:
        print(f"  - {r.content}")

    mgr.clear_memories()
    assert len(mgr.list_memories()) == 0, "Clear failed"
    print("\nClear verified.")


def main():
    try:
        test_store_and_retrieve()
        print("\nAll memory tests passed.")
        return True
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
