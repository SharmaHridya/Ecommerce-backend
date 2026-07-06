from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin_user
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, RestockRequest

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductResponse])
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),  # le=100 -- prevents someone requesting 1,000,000 at once
    category_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Product]:
    """
    Public route. Supports pagination (skip/limit) and optional filtering by category.
    Example: GET /products?skip=20&limit=10&category_id=1
    """
    query = db.query(Product)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()


@router.get("/low-stock", response_model=list[ProductResponse])
def list_low_stock_products(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
) -> list[Product]:
    """
    Admin-only report: products at or below their own low_stock_threshold.
    MUST be defined BEFORE the /{product_id} route below -- otherwise FastAPI
    would try to interpret "low-stock" as a product_id and fail with a 422,
    since /{product_id} is registered first and matches ANY path segment there.
    """
    return db.query(Product).filter(Product.stock_quantity <= Product.low_stock_threshold).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
) -> Product:
    # Validate the referenced category actually exists BEFORE hitting the DB's
    # foreign key constraint -- this lets us return a clean 404 with a helpful
    # message, instead of a raw database IntegrityError leaking to the client.
    category = db.get(Category, product_in.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {product_in.category_id} does not exist",
        )

    new_product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock_quantity=product_in.stock_quantity,
        category_id=product_in.category_id,
        low_stock_threshold=product_in.low_stock_threshold,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.patch("/{product_id}/restock", response_model=ProductResponse)
def restock_product(
    product_id: int,
    restock_in: RestockRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
) -> Product:
    """
    Adds to existing stock rather than replacing it -- e.g. restocking 20 more
    units of a product that already has 3 in stock results in 23, not 20.
    This is a deliberate design choice: "restock" should mean "add inventory
    that arrived," not "overwrite my current count" (which could accidentally
    erase units that were legitimately sold since the admin last checked).
    """
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.stock_quantity += restock_in.quantity
    db.commit()
    db.refresh(product)
    return product