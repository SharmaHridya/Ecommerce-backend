from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    product: Mapped["Product"] = relationship()

    __table_args__ = (
        # Same pattern as CartItem in Phase 3: this (user_id, product_id) PAIR
        # must be unique -- a user can review a product at most once. Unlike
        # the Payment fix in Phase 5, this one really IS a plain, unconditional
        # unique constraint -- there's no "retry after failure" concept here.
        UniqueConstraint("user_id", "product_id", name="uq_one_review_per_user_per_product"),
        # CheckConstraint: a NEW kind of constraint -- enforces a rule on a
        # SINGLE column's value, at the database level, regardless of what
        # any application code does. Even a bug in our Pydantic validation
        # could never result in a rating of 0 or 6 actually landing in the DB.
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
    )