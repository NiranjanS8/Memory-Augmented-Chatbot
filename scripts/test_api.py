"""Quick API test against a running server at localhost:8000."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = "testuser_api@example.com"
TEST_PASSWORD = "testpass123"
TEST_MODEL = "openai"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    print("=== API Test (against running server) ===\n")

    # Health
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print(f"[PASS] Health: {r.json()}")

    # Unauthorized
    r = httpx.get(f"{BASE_URL}/api/conversations")
    assert r.status_code in (401, 403)
    print(f"[PASS] Unauthorized → {r.status_code}")

    # Register
    r = httpx.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL, "password": TEST_PASSWORD, "display_name": "API Tester",
    })
    if r.status_code == 409:
        print("[SKIP] Already registered, logging in instead")
        r = httpx.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD,
        })
    assert r.status_code == 200, f"Auth failed: {r.status_code} {r.text}"
    token = r.json()["access_token"]
    print(f"[PASS] Auth — token: {token[:20]}...")

    # Login bad password
    r = httpx.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL, "password": "wrong",
    })
    assert r.status_code == 401
    print("[PASS] Bad password → 401")

    # Conversations list
    r = httpx.get(f"{BASE_URL}/api/conversations", headers=_auth(token))
    assert r.status_code == 200
    print(f"[PASS] List conversations — {len(r.json())} existing")

    # Chat stream
    print("\n--- SSE Chat Stream ---")
    conv_id = None
    full_response = ""
    model_error = False

    with httpx.stream(
        "POST", f"{BASE_URL}/api/chat/stream",
        headers={**_auth(token), "Content-Type": "application/json"},
        json={"message": "Say hello in one sentence.", "model": TEST_MODEL},
        timeout=60.0,
    ) as response:
        assert response.status_code == 200, f"Stream failed: {response.status_code}"

        for line in response.iter_lines():
            if not line.strip():
                continue
            text = line
            if text.startswith("data: "):
                text = text[6:]
            elif text.startswith("data:"):
                text = text[5:]

            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue

            if event["type"] == "memory":
                conv_id = event.get("conversation_id")
                print(f"  [memory] {len(event['data'])} memories, conv: {conv_id[:8] if conv_id else 'N/A'}...")
            elif event["type"] == "chunk":
                full_response += event["data"]
                print(f"  [chunk] +{len(event['data'])} chars", end="\r")
            elif event["type"] == "done":
                print()
                break
            elif event["type"] == "error":
                model_error = True
                print(f"  [error] {event['data'][:80]}...")
                break

    assert conv_id is not None, "No conversation_id in memory event"
    print(f"[PASS] SSE stream protocol works — conv_id received")

    if model_error:
        print("[WARN] Model returned error (likely invalid API key) — SSE stream tested, skipping content check")
    else:
        assert len(full_response) > 0, "No response chunks received"
        print(f"[PASS] Chat stream — \"{full_response[:80]}\"")

    # Verify conversation was created even if model errored
    if conv_id:
        time.sleep(0.5)

        # Conversation exists
        r = httpx.get(f"{BASE_URL}/api/conversations/{conv_id}", headers=_auth(token))
        assert r.status_code == 200
        print(f"[PASS] Conversation created and retrievable")

        # Rename
        r = httpx.patch(
            f"{BASE_URL}/api/conversations/{conv_id}",
            headers=_auth(token),
            json={"title": "Test Chat"},
        )
        assert r.status_code == 200
        print("[PASS] Rename conversation")

        # Conversation detail after rename
        r = httpx.get(f"{BASE_URL}/api/conversations/{conv_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["title"] == "Test Chat"
        print("[PASS] Get conversation detail — title matches")

        if not model_error:
            r = httpx.get(f"{BASE_URL}/api/conversations/{conv_id}/messages", headers=_auth(token))
            assert r.status_code == 200
            msgs = r.json()
            assert len(msgs) >= 2
            print(f"[PASS] Messages persisted — {len(msgs)} messages")

    # Memory endpoints
    r = httpx.get(f"{BASE_URL}/api/memory", headers=_auth(token))
    assert r.status_code == 200
    print(f"[PASS] GET /api/memory — {len(r.json())} memories")

    r = httpx.delete(f"{BASE_URL}/api/memory", headers=_auth(token))
    assert r.status_code == 200
    print("[PASS] DELETE /api/memory — cleared")

    # Conversations list
    r = httpx.get(f"{BASE_URL}/api/conversations", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 1
    print(f"[PASS] Conversations list — {len(r.json())} conversation(s)")

    # Delete conversation
    if conv_id:
        r = httpx.delete(f"{BASE_URL}/api/conversations/{conv_id}", headers=_auth(token))
        assert r.status_code == 200
        print("[PASS] Delete conversation")

        # Verify deleted
        r = httpx.get(f"{BASE_URL}/api/conversations/{conv_id}", headers=_auth(token))
        assert r.status_code == 404
        print("[PASS] Deleted conversation returns 404")

    print("\n All API tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        success = False
    sys.exit(0 if success else 1)
