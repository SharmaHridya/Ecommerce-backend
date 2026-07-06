from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=list[CartItemResponse])
def view_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CartItem]:
    """Every cart route requires login -- there's no such thing as a public cart."""
    return db.query(CartItem).filter(CartItem.user_id == current_user.id).all()


@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item_in: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartItem:
    product = db.get(Product, item_in.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if item_in.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock_quantity} units of '{product.name}' are in stock",
        )

    # UPSERT LOGIC: check if this (user, product) pair already has a cart_item row.
    existing_item = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == item_in.product_id)
        .first()
    )

    if existing_item is not None:
        # Already in cart -- increase quantity instead of creating a duplicate row.
        new_quantity = existing_item.quantity + item_in.quantity
        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock_quantity} units of '{product.name}' are in stock",
            )
        existing_item.quantity = new_quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item

    # Not in cart yet -- create a new row.
    new_item = CartItem(
        user_id=current_user.id,
        product_id=item_in.product_id,
        quantity=item_in.quantity,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartItem:
    # THE IDOR-PREVENTION LINE: filter by BOTH the item's own id AND user_id.
    # If we only filtered by CartItem.id, any logged-in user could update
    # ANY other user's cart item just by guessing/incrementing item_id.
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if item is None:
        # Deliberately the SAME error whether the item doesn't exist at all,
        # or exists but belongs to someone else -- don't leak which case it is.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    if item_in.quantity > item.product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {item.product.stock_quantity} units of '{item.product.name}' are in stock",
        )

    item.quantity = item_in.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    db.delete(item)
    db.commit()
    return None