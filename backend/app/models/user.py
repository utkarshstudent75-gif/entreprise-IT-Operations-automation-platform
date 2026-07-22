from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    entra_oid: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )

    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    entra_tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    roles: Mapped[str] = mapped_column(String(255), default="HelpDesk", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
