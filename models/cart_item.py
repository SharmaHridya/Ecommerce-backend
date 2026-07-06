from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.models.product import Product
from app.database import Base



class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Python-side convenience: cart_item.product gives the full Product object.
    # We don't need a reverse `user.cart_items` relationship yet -- add it later
    # only if something actually needs it (YAGNI: don't add relationships "just in case").
    product: Mapped["Product"] = relationship()

    __table_args__ = (
        # Composite unique constraint: this (user_id, product_id) PAIR must be
        # unique across the whole table. A single user CAN have many cart_items
        # (different products), and a single product CAN be in many users' carts --
        # what can't happen is the SAME user having TWO rows for the SAME product.
        UniqueConstraint("user_id", "product_id", name="uq_user_product_cart_item"),
    )