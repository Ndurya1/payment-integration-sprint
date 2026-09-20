from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import String, Integer, Numeric, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    account_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    checkout_request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    merchant_request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    mpesa_receipt_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    result_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    result_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )