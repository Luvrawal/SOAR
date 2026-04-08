from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_current_user_optional, require_roles
from app.core.config import settings
from app.core.exceptions import AppException, AuthenticationException
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthTokenResponse, LoginRequest, RegisterRequest, UserResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth")


def _serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ApiResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise AppException(status_code=409, message="Email is already registered", error_code="email_exists")

    user_count = db.query(User).count()
    is_bootstrap = user_count == 0

    if not is_bootstrap and current_user is None:
        raise AuthenticationException(message="Admin authentication required to create users")

    if not is_bootstrap and current_user is not None and current_user.role != "admin":
        raise AppException(status_code=403, message="Only admins can create users", error_code="forbidden")

    role = payload.role
    if is_bootstrap and role != "admin":
        role = "admin"

    user = User(
        email=payload.email.lower().strip(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return ApiResponse(
        message="User registered successfully",
        data={"user": _serialize_user(user).model_dump(mode="json")},
    )


@router.get("/bootstrap-status", response_model=ApiResponse)
def bootstrap_status(db: Session = Depends(get_db)) -> ApiResponse:
    user_count = db.query(User).count()
    return ApiResponse(
        message="Bootstrap status fetched successfully",
        data={
            "requires_bootstrap": user_count == 0,
            "user_count": user_count,
        },
    )


@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse:
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthenticationException(message="Invalid email or password")

    if not user.is_active:
        raise AuthenticationException(message="User account is inactive")

    token = create_access_token(user_id=user.id, role=user.role)
    auth_payload = AuthTokenResponse(
        access_token=token,
        expires_in_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        user=_serialize_user(user),
    )

    return ApiResponse(message="Login successful", data=auth_payload.model_dump(mode="json"))


@router.get("/me", response_model=ApiResponse)
def me(current_user: User = Depends(get_current_user)) -> ApiResponse:
    return ApiResponse(message="User profile fetched successfully", data={"user": _serialize_user(current_user).model_dump(mode="json")})


@router.get("/roles/check", response_model=ApiResponse, dependencies=[Depends(require_roles("admin"))])
def admin_guard_check() -> ApiResponse:
    return ApiResponse(message="Role check passed", data={"role": "admin"})
