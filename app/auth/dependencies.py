from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models.user import User

# This tells FastAPI/Swagger: "clients get a token from POST /auth/login,
# and must send it as 'Authorization: Bearer <token>' on protected routes."
# It does NOT do the verification itself — it just extracts the token string
# from the request header for us, and powers the "Authorize" button in /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    The dependency every protected route will use:

        @router.get("/me")
        def read_me(current_user: User = Depends(get_current_user)):
            return current_user

    FastAPI resolves dependencies in order: first it runs oauth2_scheme
    (pulls the token out of the header), then get_db (opens a session),
    then this function uses both to look up and return the real User row.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    user = db.get(User, int(user_id_str))
    if user is None:
        raise credentials_exception

    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Builds ON TOP of get_current_user rather than duplicating its logic.
    FastAPI resolves get_current_user first (so we know the token is valid
    and the user exists), THEN this function adds one more check: is this
    user actually an admin?
 
    Usage in a route:
        @router.post("/products")
        def create_product(..., admin: User = Depends(get_current_admin_user)):
            ...
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires admin privileges",
        )
    return current_user