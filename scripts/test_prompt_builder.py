"""Verifies build_system_prompt produces coherent output with memory injection."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.types import MemoryRecord, MemoryType
from backend.prompts.system import build_system_prompt


def test_empty_memories():
    prompt = build_system_prompt(memories=[], model_name="openai")
    assert "Current model: openai" in prompt
    assert "What I know about you" not in prompt
    print("[PASS] Empty memories — no memory sections rendered")


def test_semantic_injection():
    memories = [
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.SEMANTIC,
            content="User prefers TypeScript over JavaScript",
        ),
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.SEMANTIC,
            content="User is building a SaaS product in healthcare",
        ),
    ]
    prompt = build_system_prompt(memories=memories, model_name="claude")
    assert "What I know about you" in prompt
    assert "TypeScript" in prompt
    assert "healthcare" in prompt
    assert "Current model: claude" in prompt
    print("[PASS] Semantic facts injected correctly")


def test_episodic_injection():
    memories = [
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.EPISODIC,
            content="Discussed React Native architecture decisions",
            source_session="session_003",
        ),
    ]
    prompt = build_system_prompt(memories=memories, model_name="gemini")
    assert "Our previous conversations" in prompt
    assert "session_003" in prompt
    assert "React Native" in prompt
    print("[PASS] Episodic summaries injected correctly")


def test_mixed_memories():
    memories = [
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.SEMANTIC,
            content="User has a dog named Max",
        ),
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.EPISODIC,
            content="Helped user debug a memory leak in Node.js",
            source_session="session_005",
        ),
    ]
    prompt = build_system_prompt(memories=memories, model_name="mistral")
    assert "What I know about you" in prompt
    assert "Our previous conversations" in prompt
    assert "dog named Max" in prompt
    assert "memory leak" in prompt
    print("[PASS] Mixed semantic + episodic memories")


def test_superseded_filtered():
    memories = [
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.SEMANTIC,
            content="User uses Python",
            confidence=0.1,
            superseded_by="new_id",
        ),
        MemoryRecord(
            user_id="u1",
            memory_type=MemoryType.SEMANTIC,
            content="User switched to Go",
            confidence=1.0,
        ),
    ]
    prompt = build_system_prompt(memories=memories, model_name="openai")
    assert "Python" not in prompt, "Superseded memory should be filtered"
    assert "Go" in prompt
    print("[PASS] Superseded memories (confidence <= 0.1) filtered out")


def test_tools_block():
    prompt = build_system_prompt(
        memories=[],
        model_name="openai",
        tools_available=["web_search", "code_interpreter"],
    )
    assert "Available tools" in prompt
    assert "web_search" in prompt
    print("[PASS] Tools block rendered")


def main():
    tests = [
        test_empty_memories,
        test_semantic_injection,
        test_episodic_injection,
        test_mixed_memories,
        test_superseded_filtered,
        test_tools_block,
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
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
