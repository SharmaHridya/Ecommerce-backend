import enum
from datetime import datetime, timezone

from alembic.environment import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.order_item import OrderItem
from app.database import Base


class OrderStatus(str, enum.Enum):
    """
    A Python enum -- restricts `status` to only these exact values.
    Inheriting from `str` as well as `enum.Enum` means it behaves like a
    string everywhere (easy to compare, easy to serialize to JSON) while
    still being restricted to this fixed set of options.
    """

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING
    )
    # Stored directly on the order rather than always summing order_items live --
    # a common, deliberate denormalization: fast to read, and matches what the
    # customer actually saw/agreed to pay at checkout time.
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # One order has many order_items. cascade="all, delete-orphan" means:
    # if an Order is deleted, its OrderItems are automatically deleted too --
    # an order_item should never exist without its parent order.
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    '''all: Operations performed on the Order (such as save, update, delete) are also applied to its OrderItems.
    * delete-orphan: If an OrderItem is removed from order.items and no longer belongs to any Order, SQLAlchemy automatically deletes it from the database.'''