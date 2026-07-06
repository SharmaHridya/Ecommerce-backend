"""
Seed script -- populates the database with sample data for local development.

Run this AFTER `alembic upgrade head` has created the tables:
    python -m app.seed

Safe to run multiple times: it checks for existing rows before creating
new ones, so it won't create duplicates if you run it twice.
"""

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.user import User


def seed() -> None:
    db = SessionLocal()
    try:
        # --- Admin user ---
        admin_email = "admin@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if admin is None:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("adminpass123"),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"Created admin user: {admin_email} / adminpass123")
        else:
            print(f"Admin user already exists: {admin_email}")

        # --- Categories ---
        category_names = ["Electronics", "Books", "Clothing", "Home & Kitchen"]
        categories: dict[str, Category] = {}
        for name in category_names:
            existing = db.query(Category).filter(Category.name == name).first()
            if existing is None:
                existing = Category(name=name)
                db.add(existing)
                db.commit()
                db.refresh(existing)
                print(f"Created category: {name}")
            categories[name] = existing

        # --- Products ---
        sample_products = [
            ("Laptop", "A fast 14-inch laptop", 74999.00, 15, "Electronics"),
            ("Wireless Mouse", "Ergonomic wireless mouse", 799.00, 50, "Electronics"),
            ("Mechanical Keyboard", "RGB mechanical keyboard", 3499.00, 25, "Electronics"),
            ("The Pragmatic Programmer", "Classic software engineering book", 899.00, 30, "Books"),
            ("Clean Code", "Book on writing maintainable code", 749.00, 20, "Books"),
            ("Cotton T-Shirt", "Plain cotton crew-neck t-shirt", 499.00, 100, "Clothing"),
            ("Denim Jacket", "Classic blue denim jacket", 2499.00, 3, "Clothing"),  # low stock on purpose
            ("Non-Stick Pan", "10-inch non-stick frying pan", 1299.00, 40, "Home & Kitchen"),
        ]

        for name, description, price, stock, category_name in sample_products:
            existing = db.query(Product).filter(Product.name == name).first()
            if existing is None:
                new_product = Product(
                    name=name,
                    description=description,
                    price=price,
                    stock_quantity=stock,
                    category_id=categories[category_name].id,
                )
                db.add(new_product)
                db.commit()
                print(f"Created product: {name} (stock={stock})")

        print("\nSeeding complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()