from datetime import datetime, timezone
from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """
    The User table. Every other table (cart, orders, reviews...) will
    eventually have a foreign key pointing back to this table.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    '''mapped_column()
    This creates a database column. 
    Equivalent SQL:id INTEGER PRIMARY KEY'''
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # We NEVER store the raw password — only its bcrypt hash.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
