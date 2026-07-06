"""
Additional seed data -- run AFTER app/seed.py, adds more variety on top of it.

    python -m app.seed_more

Same idempotency pattern as seed.py: checks for existing rows by name before
creating anything, so it's safe to run multiple times without duplicating data,
and safe to run whether or not seed.py has already been run first.
"""

from app.database import SessionLocal
from app.models.category import Category
from app.models.product import Product


def seed_more() -> None:
    db = SessionLocal()
    try:
        # --- New categories ---
        category_names = ["Sports & Outdoors", "Toys & Games", "Beauty", "Stationery"]
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

        # Also grab existing categories from seed.py in case we want to add
        # more products to them too, without recreating them.
        for name in ["Electronics", "Books", "Clothing", "Home & Kitchen"]:
            existing = db.query(Category).filter(Category.name == name).first()
            if existing is not None:
                categories[name] = existing

        # --- New products ---
        # (name, description, price, stock, low_stock_threshold, category_name)
        sample_products = [
            ("Yoga Mat", "6mm non-slip yoga mat", 899.00, 35, 5, "Sports & Outdoors"),
            ("Football", "Size 5 match football", 1199.00, 20, 5, "Sports & Outdoors"),
            ("Dumbbell Set (10kg)", "Adjustable dumbbell pair", 2999.00, 4, 5, "Sports & Outdoors"),
            ("Rubik's Cube", "Classic 3x3 speed cube", 349.00, 60, 10, "Toys & Games"),
            ("Board Game: Strategy Classics", "4-player strategy board game", 1499.00, 12, 5, "Toys & Games"),
            ("Building Blocks Set", "250-piece creative building blocks", 1799.00, 18, 5, "Toys & Games"),
            ("Moisturizer", "Daily face moisturizer, 100ml", 599.00, 40, 8, "Beauty"),
            ("Shampoo", "Sulfate-free shampoo, 250ml", 449.00, 50, 8, "Beauty"),
            ("Notebook Set (3-pack)", "A5 ruled notebooks", 299.00, 80, 15, "Stationery"),
            ("Fountain Pen", "Classic steel-nib fountain pen", 799.00, 2, 5, "Stationery"),  # low stock
            ("Desk Organizer", "Wooden multi-compartment organizer", 999.00, 25, 5, "Stationery"),
            # A couple more in existing categories too, for depth
            ("Bluetooth Earbuds", "Noise-cancelling wireless earbuds", 4499.00, 15, 5, "Electronics"),
            ("Sci-Fi Novel: Beyond the Rings", "Award-winning space opera", 549.00, 22, 5, "Books"),
            ("Running Shoes", "Lightweight breathable running shoes", 3299.00, 10, 5, "Clothing"),
        ]

        for name, description, price, stock, threshold, category_name in sample_products:
            existing = db.query(Product).filter(Product.name == name).first()
            if existing is None:
                new_product = Product(
                    name=name,
                    description=description,
                    price=price,
                    stock_quantity=stock,
                    low_stock_threshold=threshold,
                    category_id=categories[category_name].id,
                )
                db.add(new_product)
                db.commit()
                print(f"Created product: {name} (stock={stock})")
            else:
                print(f"Product already exists, skipped: {name}")

        print("\nAdditional seeding complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_more()