"""Smoke test: sends a single chat message and one embedding request to each provider."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_model
from backend.models.base import Message

PROVIDERS = ["claude", "openai", "gemini", "mistral", "groq"]
TEST_MESSAGE = [Message(role="user", content="Say hello in one sentence.")]


def test_chat(name: str) -> bool:
    try:
        client = get_model(name)
        response = client.chat(TEST_MESSAGE, system="You are a helpful assistant.")
        print(f"  [{name}] chat: {response.content[:80]}...")
        print(f"           tokens: {response.input_tokens} in / {response.output_tokens} out")
        return True
    except Exception as e:
        print(f"  [{name}] chat FAILED: {e}")
        return False


def test_embed(name: str) -> bool:
    try:
        client = get_model(name)
        vec = client.embed("test embedding")
        print(f"  [{name}] embed: dim={len(vec)}, first 3={vec[:3]}")
        return True
    except Exception as e:
        print(f"  [{name}] embed FAILED: {e}")
        return False


def main():
    results = {}

    print("\nChat tests:")
    for name in PROVIDERS:
        results[f"{name}_chat"] = test_chat(name)

    print("\nEmbed tests:")
    for name in PROVIDERS:
        results[f"{name}_embed"] = test_embed(name)

    passed = sum(results.values())
    total = len(results)
    print(f"\n{passed}/{total} tests passed.")
    return all(results.values())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
