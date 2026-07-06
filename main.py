from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, cart, categories, orders, payments, products, reviews

app = FastAPI(
    title="E-Commerce API",
    description="A production-quality e-commerce backend built with FastAPI.",
    version="0.1.0",
)

# CORS: without this, a browser running your frontend on a DIFFERENT origin
# (e.g. https://your-app.vercel.app) would have every API response silently
# blocked by the browser itself, even though the backend responded correctly.
# allow_credentials=True is needed because we send the JWT in an Authorization
# header on requests the browser treats as needing credentials-aware handling.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(reviews.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Simple liveness check. Useful for confirming the server is up,
    and later for deployment platforms (Render/Railway) to verify the app started.
    """
    return {"status": "ok"}