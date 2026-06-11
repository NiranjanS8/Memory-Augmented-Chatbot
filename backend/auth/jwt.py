from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.auth.users import AuthStore, User
from backend.config import settings

_ALGORITHM = "HS256"
_bearer_scheme = HTTPBearer()

_auth_store: AuthStore | None = None


def _get_auth_store() -> AuthStore:
    global _auth_store
    if _auth_store is None:
        _auth_store = AuthStore()
    return _auth_store


def create_jwt(user: User) -> str:
    """Issue a signed JWT for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    token_claims = {
        "sub": user.id,
        "email": user.email,
        "exp": expire,
    }
    return jwt.encode(token_claims, settings.JWT_SECRET, algorithm=_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> User:
    """FastAPI dependency — extracts and validates the JWT from the Authorization header."""
    token = credentials.credentials
    try:
        token_claims = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
        user_id: str | None = token_claims.get("sub")
        if user_id is None:
            raise _credentials_error()
    except JWTError:
        raise _credentials_error()

    store = _get_auth_store()
    user = store.get_by_id(user_id)
    if user is None:
        raise _credentials_error()

    return user


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
