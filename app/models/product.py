from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.category import Category
from app.database import Base


class Product(Base):
    __tablename__ = "products"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
 
    # THE FOREIGN KEY: this is the actual database column that links a product
    # to its category. "categories.id" means "must match an id that exists
    # in the categories table" -- Postgres itself will reject a product with
    # a category_id that doesn't correspond to a real category.
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
 
    # Per-product threshold: when stock_quantity falls at or below this number,
    # the product shows up in the admin low-stock report. Different products
    # naturally need different thresholds (a ₹500 t-shirt vs a ₹75,000 laptop
    # have very different reorder economics) -- hence per-product, not global.
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
 
    # Python-side convenience: product.category gives the actual Category object,
    # not just its id.
    category: Mapped["Category"] = relationship(back_populates="products")
 