from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


def _resolve_user_from_token(token: str, db: Session) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise AuthenticationException(message="Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationException(message="Invalid token payload")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise AuthenticationException(message="Invalid token payload") from None

    user = db.get(User, user_id_int)
    if user is None or not user.is_active:
        raise AuthenticationException(message="User account is unavailable")

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationException()

    return _resolve_user_from_token(credentials.credentials, db)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    return _resolve_user_from_token(credentials.credentials, db)


def require_roles(*roles: str) -> Callable[[User], User]:
    def _enforce(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AuthorizationException()
        return current_user

    return _enforce
