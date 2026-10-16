from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class SLAPolicy(Base, TimestampMixin):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    first_response_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    resolution_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )