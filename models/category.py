from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product
from app.database import Base


class Category(Base):
    """A product category, e.g. 'Electronics', 'Books'."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # This does NOT create a database column. It's a Python-only convenience:
    # lets us write `category.products` to get a list of Product objects,
    # instead of manually querying `db.query(Product).filter(Product.category_id == category.id)`.
    # back_populates links this to Product.category below -- SQLAlchemy keeps
    # both sides in sync automatically.
    products: Mapped[list["Product"]] = relationship(back_populates="category")