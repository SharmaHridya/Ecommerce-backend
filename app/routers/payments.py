import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


def simulate_gateway_call(amount: float) -> bool:
    """
    Stands in for calling a real payment gateway's API (Stripe, Razorpay...).
    A real version of this function would make an HTTP request to the gateway
    and return based on ITS response. We simulate a 90% success rate so you
    can see both the success and failure paths behave correctly.
    """
    return random.random() < 0.9
'''Since 90% of numbers between 0 and 1 are less than 0.9:

* 90% chance → True
* 10% chance → False

So this function simulates a payment gateway that succeeds about 90% of the time.'''


@router.post("/pay/{order_id}", response_model=PaymentResponse)
def pay_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Payment:
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # STATE MACHINE CHECK: only a PENDING order can be paid.
    # Trying to pay an already-paid, shipped, or cancelled order is invalid.
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for an order with status '{order.status.value}'",
        )

    # IDEMPOTENCY CHECK: has this order already been successfully paid?
    # (Belt-and-suspenders with the status check above -- this also protects
    # against a rare edge case where status and payment history could
    # otherwise drift out of sync.)
    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order_id, Payment.status == PaymentStatus.SUCCEEDED)
        .first()
    )
    if existing_payment is not None:
        # Same operation, called twice -- return the SAME result instead of
        # processing a second charge. This is what "idempotent" means in practice.
        return existing_payment

    try:
        payment_succeeded = simulate_gateway_call(order.total_amount)

        new_payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            status=PaymentStatus.SUCCEEDED if payment_succeeded else PaymentStatus.FAILED,
        )
        db.add(new_payment)

        if payment_succeeded:
            order.status = OrderStatus.PAID

        db.commit()
        db.refresh(new_payment)

        if not payment_succeeded:
            # The Payment row is saved (we DO want a record of failed attempts),
            # but we tell the client clearly that it failed, with a 402 status
            # (Payment Required) -- more specific than a generic 400.
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment was declined. Please try again.",
            )

        return new_payment

    except HTTPException:
        # Let our OWN deliberate HTTPExceptions (like the 402 above) pass through
        # unchanged -- don't let the broader except below swallow them.
        raise
    except Exception:
        # THE FIX from last session's gap: catch broader failures too (e.g. a
        # dropped DB connection during commit), not just one specific exception
        # type. Roll back whatever was staged, and return a clean, generic
        # error instead of leaking a raw stack trace to the client.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing failed unexpectedly. Please try again.",
        )


@router.get("/order/{order_id}", response_model=PaymentResponse)
def get_payment_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Payment:
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No payment found for this order"
        )
    return payment