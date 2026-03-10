import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, RoleEnum
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserRead

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic for authentication.

    Stateless design: once the JWT is issued the server never queries the
    database to validate a session — the JWT signature is the only proof of
    identity.
    """

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)

    def login(self, username: str, password: str) -> TokenResponse:
        """Validate credentials and return a signed JWT on success."""
        user = self._repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account",
            )

        token = create_access_token(
            data={"sub": user.username, "role": user.role.value}
        )
        return TokenResponse(access_token=token)


class UserService:
    """Business logic for user management."""

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)

    def create_user(self, payload: UserCreate) -> UserRead:
        """Create a new user, raising 409 if username or email already exists."""
        if self._repo.get_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{payload.username}' is already taken",
            )
        if self._repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered",
            )
        user = self._repo.create(
            username=payload.username,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        return UserRead.model_validate(user)

    def get_user(self, user_id: int) -> UserRead:
        """Fetch a user by ID, raising 404 if not found."""
        user = self._repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserRead.model_validate(user)

    def list_users(self) -> list[UserRead]:
        """Return all users as a list of DTOs."""
        return [UserRead.model_validate(u) for u in self._repo.get_all()]

    # ------------------------------------------------------------------
    # Internal helper used by the startup seed
    # ------------------------------------------------------------------

    def seed_if_empty(self, seed_users: list[dict]) -> None:
        """Insert seed users idempotently.

        Each user is inserted independently. If the username or email
        already exists (UNIQUE violation) the exception is caught, the
        transaction is rolled back for that record, and the loop continues
        with the next user. This makes the seed safe to run on every
        startup regardless of previous partial runs.
        """
        for u in seed_users:
            try:
                self._repo.create(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    role=RoleEnum(u["role"]),
                )
                logger.info("Seeded user: %s (%s)", u["username"], u["role"])
            except IntegrityError:
                self._repo._db.rollback()
                logger.info("Seed skipped (already exists): %s", u["username"])
