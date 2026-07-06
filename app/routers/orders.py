from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.cart_item import CartItem
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    """
    Converts the current user's cart into a permanent Order.
    This entire function is ONE transaction: either everything below
    succeeds and we commit once at the end, or ANYTHING fails and we
    roll back everything -- no half-finished orders ever get saved.
    """
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    try:
        # STEP 1: Re-validate stock for EVERY item -- and THIS TIME, actually
        # lock each product row with .with_for_update() while we do it.
        #
        # This closes the gap we flagged (but deferred) in Phase 4: without
        # the lock, two simultaneous checkouts could both read the same
        # stock_quantity before either one writes back a decrement, both
        # "pass" the check, and both succeed -- overselling stock.
        #
        # With .with_for_update(), the moment THIS transaction reads a
        # product row, Postgres locks it. A second, concurrent transaction
        # trying to read that same row (also with FOR UPDATE) has to WAIT
        # until this transaction finishes (commits or rolls back) before it
        # can even read the row -- by which point it will see the updated,
        # correct stock_quantity, not the stale value from before our decrement.
        locked_products: dict[int, Product] = {}
        for cart_item in cart_items:
            product = (
                db.query(Product)
                .filter(Product.id == cart_item.product_id)
                .with_for_update()
                .first()
            )
            if product is None or product.stock_quantity < cart_item.quantity:
                raise ValueError(
                    f"'{cart_item.product.name}' no longer has enough stock "
                    f"(requested {cart_item.quantity}, available "
                    f"{product.stock_quantity if product else 0})"
                )
            locked_products[cart_item.product_id] = product

        # STEP 2: Everything validated -- now build the order.
        total_amount = sum(
            locked_products[cart_item.product_id].price * cart_item.quantity
            for cart_item in cart_items
        )
        new_order = Order(
            user_id=current_user.id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
        )
        db.add(new_order)
        db.flush()  # assigns new_order.id WITHOUT committing yet -- we need
        # that id to create order_items below, but we're not ready to
        # permanently save anything until every step below also succeeds.

        for cart_item in cart_items:
            locked_product = locked_products[cart_item.product_id]
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price_at_purchase=locked_product.price,  # SNAPSHOT taken here
            )
            db.add(order_item)

            # Decrement stock as part of the SAME transaction, on the LOCKED
            # row -- no other transaction could have changed it underneath us.
            locked_product.stock_quantity -= cart_item.quantity

        # STEP 3: Clear the cart -- also part of the same transaction.
        for cart_item in cart_items:
            db.delete(cart_item)

        # STEP 4: Only NOW, after every single step above succeeded without
        # raising, do we commit. This one line is what makes everything
        # above permanent, all at once.
        db.commit()
        db.refresh(new_order)
        return new_order

    except ValueError as e:
        # Something failed validation (e.g. insufficient stock).
        # Undo EVERYTHING staged above -- the flush()'d order, any order_items
        # added, any stock decrements -- none of it gets saved.
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        # Let our own deliberate HTTPExceptions pass through unchanged.
        raise
    except Exception:
        # THE FIX flagged in Phase 4: a broader safety net for anything else
        # that could go wrong mid-transaction (e.g. a dropped DB connection).
        # Without this, such an error would propagate as a raw, unhandled 500
        # with a leaked stack trace instead of a clean, generic message.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Checkout failed unexpectedly. Please try again.",
        )


@router.get("/", response_model=list[OrderResponse])
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Order]:
    return db.query(Order).filter(Order.user_id == current_user.id).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    # Same IDOR-safe pattern as cart: scope by BOTH id and user_id.
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order