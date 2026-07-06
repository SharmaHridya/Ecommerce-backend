from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)  # ge=1 -- can't add 0 or negative quantity


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)  # setting quantity to 0 should DELETE the item, not "update to 0"


class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse  # nested -- same idea as ProductResponse.category in Phase 2

    model_config = ConfigDict(from_attributes=True)