from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_payload
from app.database import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserRead
from app.services.user_service import AuthService, UserService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain a JWT",
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate credentials against the database and return a signed JWT.

    The token payload includes ``sub`` (username) and ``role``, so subsequent
    requests do **not** need to hit the database to determine the user's role.
    """
    service = AuthService(db)
    return service.login(body.username, body.password)


# ---------------------------------------------------------------------------
# User management endpoints (protected — any authenticated user)
# ---------------------------------------------------------------------------

users_router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user_payload)],
)


@users_router.post("/", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Create a new user (requires a valid JWT)."""
    return UserService(db).create_user(body)


@users_router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[UserRead]:
    """Return all users (requires a valid JWT)."""
    return UserService(db).list_users()


@users_router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    """Fetch a single user by ID (requires a valid JWT)."""
    return UserService(db).get_user(user_id)
