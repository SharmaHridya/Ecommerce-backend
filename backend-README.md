# E-Commerce API (Backend)

A production-quality e-commerce backend built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy 2.x**. Provides authentication, product/category catalog management, cart, orders, and admin operations via a fully typed, validated REST API.

## Tech Stack

| Layer            | Technology              |
|-------------------|--------------------------|
| Framework         | FastAPI                 |
| Language          | Python 3.11+             |
| Database          | PostgreSQL               |
| ORM               | SQLAlchemy 2.x (async)   |
| Migrations        | Alembic                  |
| Validation        | Pydantic v2               |
| Auth              | JWT (access/refresh tokens) |
| Server            | Uvicorn                  |

## Features

- **Authentication** — JWT-based login/register with hashed passwords, access + refresh token flow
- **Categories** — CRUD for product categories
- **Products** — CRUD, filtering by category, pagination, stock tracking
- **Cart** — Per-user cart with add/update/remove, server-side stock validation on every mutation
- **Orders** — Cart-to-order checkout flow
- **Admin** — Elevated endpoints for inventory management, including low-stock reporting
- **Role-based access control** — Regular users vs. admin-only routes

## Project Structure

```
backend/
├── alembic/                  # Migration scripts
│   └── versions/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routes/
│   │       │   ├── auth.py
│   │       │   ├── categories.py
│   │       │   ├── products.py
│   │       │   ├── cart.py
│   │       │   ├── orders.py
│   │       │   └── admin.py
│   │       └── deps.py       # Shared dependencies (get_db, get_current_user, etc.)
│   ├── core/
│   │   ├── config.py         # Settings (env-driven via Pydantic)
│   │   ├── security.py       # Password hashing, JWT encode/decode
│   │   └── database.py       # Engine/session setup
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── crud/                   # DB access logic, separated from routes
│   ├── services/                # Business logic (stock checks, order totals, etc.)
│   └── main.py                 # App entrypoint
├── tests/
├── alembic.ini
├── requirements.txt
└── .env.example
```

> Adjust the tree above if your actual folder names differ — this reflects the standard layered structure (routes → schemas → crud → models) used throughout the project.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- `pip` / `venv`

### Setup

```bash
# Clone and enter the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# then fill in your actual DB credentials and secret key
```

### Environment Variables

| Variable                | Description                              |
|---------------------------|--------------------------------------------|
| `DATABASE_URL`            | PostgreSQL connection string (e.g. `postgresql+asyncpg://user:pass@localhost:5432/ecommerce`) |
| `SECRET_KEY`               | JWT signing secret                        |
| `ALGORITHM`                | JWT algorithm (e.g. `HS256`)               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime                  |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token lifetime                  |

### Run Migrations

```bash
alembic upgrade head
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs (Swagger UI): `http://localhost:8000/docs`
Alternative docs (ReDoc): `http://localhost:8000/redoc`

## Running Tests

```bash
pytest
```

## Development Notes

- Stock checks happen **server-side, on every cart mutation** — the frontend never trusts local state for quantity/stock correctness; it always refetches after a write.
- New migrations: after changing a model, generate a revision with:
  ```bash
  alembic revision --autogenerate -m "describe your change"
  alembic upgrade head
  ```

## Roadmap / Phases Completed

- [x] Phase 0 — Project scaffolding & config
- [x] Phase 1 — Database models & Alembic setup
- [x] Phase 2 — Auth (JWT register/login)
- [x] Phase 3 — Categories CRUD
- [x] Phase 4 — Products CRUD & filtering
- [x] Phase 5 — Cart endpoints
- [x] Phase 6 — Orders / checkout
- [x] Phase 7 — Admin endpoints
- [x] Phase 8 — Low-stock reporting & polish
- [ ] Phase 9+ — (in progress on the frontend)

## License

Add your license here (e.g. MIT).
