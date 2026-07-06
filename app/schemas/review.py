from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)  # mirrors the DB CheckConstraint -- defense in depth
    comment: str | None = Field(default=None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductRatingSummary(BaseModel):
    """Not tied to a single DB row -- built from an aggregate query result."""

    product_id: int
    average_rating: float | None  # None if the product has zero reviews yet
    review_count: int