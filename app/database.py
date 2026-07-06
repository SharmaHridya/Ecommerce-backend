from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Engine: manages the actual connection pool to PostgreSQL.
# Created ONCE when this module is first imported, reused for the app's entire lifetime.
engine = create_engine(settings.database_url)

# SessionLocal is a *factory* for creating new Session objects.
# We don't create the session itself here — we create it per-request in get_db().
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class that all our SQLAlchemy models will inherit from.
    SQLAlchemy uses this to know which Python classes map to database tables,
    and Alembic uses it later to autodetect schema changes.
    """

    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to a route,
    and guarantees it's closed afterward — even if the route raises an exception.

    Usage in a route:
        def some_route(db: Session = Depends(get_db)):
            ...

    The `yield` here is what makes this a generator-based dependency:
    code before `yield` runs before the route handler, code after `yield`
    (the `finally` block) runs after the route handler finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
