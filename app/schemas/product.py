from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryResponse


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: float = Field(gt=0)  # gt=0 -- a product can't cost 0 or negative
    stock_quantity: int = Field(ge=0)  # ge=0 -- can't have negative stock
    category_id: int
    low_stock_threshold: int = Field(default=5, ge=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    stock_quantity: int
    low_stock_threshold: int
    category: CategoryResponse  # nested schema -- returns the full category, not just its id

    model_config = ConfigDict(from_attributes=True)

class RestockRequest(BaseModel):
    quantity: int = Field(gt=0)  # you can only ADD stock through this endpoint, never subtract