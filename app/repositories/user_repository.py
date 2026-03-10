from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User, RoleEnum


class UserRepository:
    """Data-access layer for the User entity.

    All database interactions are isolated here; upper layers only deal
    with domain objects and never touch the ORM session directly.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch a user by primary key. Returns None if not found."""
        return self._db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        """Fetch a user by username. Returns None if not found."""
        return (
            self._db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by email. Returns None if not found."""
        return (
            self._db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_all(self) -> list[User]:
        """Return all users."""
        return self._db.query(User).all()

    def count(self) -> int:
        """Return the total number of users in the table."""
        return self._db.query(User).count()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
        role: RoleEnum = RoleEnum.Community,
        is_active: bool = True,
    ) -> User:
        """Persist a new user and return the refreshed instance."""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_role(self, user: User, role: RoleEnum) -> User:
        """Update a user's role and persist the change."""
        user.role = role
        self._db.commit()
        self._db.refresh(user)
        return user

    def deactivate(self, user: User) -> User:
        """Mark a user as inactive."""
        user.is_active = False
        self._db.commit()
        self._db.refresh(user)
        return user
