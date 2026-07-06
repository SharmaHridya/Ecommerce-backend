import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.database import Base

if TYPE_CHECKING:
    from app.models.order import Order

class PaymentStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOTE: order_id is NOT globally unique anymore -- a failed payment attempt
    # must be retryable, which means a second (or third...) Payment row for the
    # SAME order needs to be allowed. What we actually want to prevent is two
    # SUCCEEDED payments for the same order -- that's enforced below with a
    # partial unique index instead of a plain column-level unique constraint.
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship()

    __table_args__ = (
        # A PARTIAL unique index: the uniqueness rule only applies to rows
        # where status = 'succeeded'. Postgres allows unlimited FAILED rows
        # per order_id, but will reject a second SUCCEEDED row for the same
        # order_id. This is the correct fix for the retry bug we found live --
        # our idempotency check and our schema constraint now agree with
        # each other, instead of silently contradicting each other.
        Index(
            "uq_one_succeeded_payment_per_order",
            "order_id",
            unique=True,
            postgresql_where=(status == PaymentStatus.SUCCEEDED),
        ),
    )