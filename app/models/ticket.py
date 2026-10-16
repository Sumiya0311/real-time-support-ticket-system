from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    ticket_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )

    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id"),
        nullable=True,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        Enum(
            "Low",
            "Medium",
            "High",
            "Urgent",
            name="ticket_priority",
        ),
        default="Medium",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "Open",
            "Assigned",
            "In Progress",
            "Waiting on Customer",
            "Resolved",
            "Closed",
            name="ticket_status",
        ),
        default="Open",
        nullable=False,
    )

    first_response_due: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolution_due: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    first_response_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    sla_breached: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    reopen_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    customer = relationship("User", foreign_keys=[customer_id])
    category = relationship("Category")
    assigned_agent = relationship("Agent")