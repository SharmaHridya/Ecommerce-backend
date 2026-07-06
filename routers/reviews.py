from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ProductRatingSummary, ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Review:
    product = db.get(Product, review_in.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # VERIFIED PURCHASE CHECK: a multi-table query, joining OrderItem -> Order,
    # confirming this user has at least one PAID order containing this product.
    # This is the kind of query that's genuinely new compared to earlier phases --
    # everything before this only ever filtered a single table by user_id.
    has_purchased = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == review_in.product_id,
            Order.status == OrderStatus.PAID,
        )
        .first()
        is not None
    )
    if not has_purchased:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review products you have purchased and paid for",
        )

    # ONE-REVIEW-PER-PRODUCT CHECK: pre-check for a clean error message,
    # same pattern as the cart's upsert check in Phase 3 -- the DB's
    # UniqueConstraint is the real safety net either way.
    existing_review = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.product_id == review_in.product_id)
        .first()
    )
    if existing_review is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product",
        )

    new_review = Review(
        user_id=current_user.id,
        product_id=review_in.product_id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


@router.get("/product/{product_id}", response_model=list[ReviewResponse])
def list_reviews_for_product(product_id: int, db: Session = Depends(get_db)) -> list[Review]:
    """Public route -- anyone can read reviews, no login required."""
    return db.query(Review).filter(Review.product_id == product_id).all()


@router.get("/product/{product_id}/summary", response_model=ProductRatingSummary)
def get_product_rating_summary(product_id: int, db: Session = Depends(get_db)) -> ProductRatingSummary:
    """
    AGGREGATE QUERY: func.avg() and func.count() run INSIDE Postgres --
    we never pull individual review rows into Python just to average them.
    This scales the same whether the product has 3 reviews or 3 million.
    """
    result = (
        db.query(
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .filter(Review.product_id == product_id)
        .one()
    )
    return ProductRatingSummary(
        product_id=product_id,
        average_rating=round(result.average_rating, 2) if result.average_rating else None,
        review_count=result.review_count,
    )