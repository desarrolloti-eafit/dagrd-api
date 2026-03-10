import enum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RoleEnum(str, enum.Enum):
    """Application-level roles.

    The value stored in the database is the enum name (e.g. "Community").
    Using ``str`` as a mixin makes the enum JSON-serialisable and allows
    direct comparison with plain strings.
    """

    Community = "Community"
    Operational = "Operational"
    Manager = "Manager"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(sa.String(150), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        sa.Enum(RoleEnum, name="roleenum"), nullable=False, default=RoleEnum.Community
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
