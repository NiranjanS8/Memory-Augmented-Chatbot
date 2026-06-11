"""Verifies auth: register, login, password hashing, JWT issue + decode."""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import tempfile

from backend.auth.users import AuthStore, _hash_password, _verify_password
from backend.auth.jwt import create_jwt

# Use python-jose directly for decode verification
from jose import jwt as jose_jwt
from backend.config import settings


def _temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


def test_password_hashing():
    hashed = _hash_password("mysecretpassword")
    assert ":" in hashed, "Hash should be salt:dk format"
    assert _verify_password("mysecretpassword", hashed)
    assert not _verify_password("wrongpassword", hashed)
    print("[PASS] Password hashing and verification")


def test_register_and_login():
    db_path = _temp_db()
    store = AuthStore(db_path=db_path)

    try:
        user = store.register("test@example.com", "password123", "Test User")
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.id is not None
        print(f"[PASS] Register — user id: {user.id[:8]}...")

        logged_in = store.login("test@example.com", "password123")
        assert logged_in.id == user.id
        assert logged_in.email == user.email
        print("[PASS] Login with correct credentials")

        try:
            store.login("test@example.com", "wrongpassword")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("[PASS] Login rejects wrong password")

        try:
            store.login("nonexistent@example.com", "password123")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("[PASS] Login rejects unknown email")

        try:
            store.register("test@example.com", "anotherpass")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("[PASS] Duplicate email rejected")

    finally:
        store.close()
        os.unlink(db_path)


def test_get_by_id():
    db_path = _temp_db()
    store = AuthStore(db_path=db_path)

    try:
        user = store.register("lookup@example.com", "pass")

        found = store.get_by_id(user.id)
        assert found is not None
        assert found.email == "lookup@example.com"
        print("[PASS] get_by_id returns user")

        missing = store.get_by_id("nonexistent-id")
        assert missing is None
        print("[PASS] get_by_id returns None for unknown id")
    finally:
        store.close()
        os.unlink(db_path)


def test_display_name_default():
    db_path = _temp_db()
    store = AuthStore(db_path=db_path)

    try:
        user = store.register("alice@company.io", "pass")
        assert user.display_name == "alice", f"Expected 'alice', got '{user.display_name}'"
        print("[PASS] Display name defaults to email prefix")
    finally:
        store.close()
        os.unlink(db_path)


def test_jwt_roundtrip():
    db_path = _temp_db()
    store = AuthStore(db_path=db_path)

    try:
        user = store.register("jwt@example.com", "pass")

        token = create_jwt(user)
        assert isinstance(token, str) and len(token) > 0
        print(f"[PASS] JWT created — {len(token)} chars")

        payload = jose_jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == user.id
        assert payload["email"] == "jwt@example.com"
        assert "exp" in payload
        print("[PASS] JWT decodes with correct claims")
    finally:
        store.close()
        os.unlink(db_path)


def main():
    tests = [
        test_password_hashing,
        test_register_and_login,
        test_get_by_id,
        test_display_name_default,
        test_jwt_roundtrip,
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
