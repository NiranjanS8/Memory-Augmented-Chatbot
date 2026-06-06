"""Validates that all required API keys are present in backend/.env."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings


def check_keys() -> bool:
    all_ok = True
    results = []

    for provider, key in settings.PROVIDER_KEYS.items():
        if key and key != "your_key":
            masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "(set)"
            results.append(("[OK]", provider, masked))
        else:
            results.append(("[MISSING]", provider, "not configured"))
            all_ok = False

    tool_keys = {
        "Tavily (Web Search)": settings.TAVILY_API_KEY,
        "ElevenLabs (TTS)": settings.ELEVENLABS_API_KEY,
    }
    for tool, key in tool_keys.items():
        if key and key != "your_key":
            masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "(set)"
            results.append(("[OK]", tool, masked))
        else:
            results.append(("[WARN]", tool, "not set (optional)"))

    max_name = max(len(name) for _, name, _ in results)
    for status, name, detail in results:
        print(f"  {status:<10} {name:<{max_name}}  {detail}")

    print()
    if settings.JWT_SECRET == "change_this_in_production":
        print("  [WARN]     JWT_SECRET is using the default value")

    if all_ok:
        print("\nAll provider keys configured.")
    else:
        print("\nSome provider keys missing. See backend/.env.example.")

    return all_ok


if __name__ == "__main__":
    sys.exit(0 if check_keys() else 1)
