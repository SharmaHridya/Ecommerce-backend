from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """What the client sends to /register. Pydantic validates email format
    and password length BEFORE our code ever runs — bad input never reaches
    the database layer."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt's own hard limit is 72 bytes
    #Field() is a Pydantic function that lets you add validation rules,
    #metadata to a field in a BaseModel.
    
class UserResponse(BaseModel):
    """What we send back to the client. Notice: NO password field at all —
    this is what guarantees the hash never accidentally leaks in an API response,
    even if a developer later adds fields carelessly to the User model."""

    id: int
    email: EmailStr
    is_admin: bool
    created_at: datetime

    # Lets Pydantic build this schema directly from a SQLAlchemy User object
    # (model.id, model.email, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """What /login returns."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """What we decode OUT of a JWT payload — used internally by get_current_user."""

    user_id: int | None = None
