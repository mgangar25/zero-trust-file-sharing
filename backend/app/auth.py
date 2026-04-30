"""
Authentication helper functions.

This file contains password hashing, password verification, JWT creation, and a
small dependency for finding the currently logged-in user.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db


# passlib gives us a safe wrapper around bcrypt.
# bcrypt is intentionally slow, which makes stolen password hashes harder to
# brute force compared with fast hashes like plain SHA-256.
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# This tells FastAPI how to read a Bearer token from the Authorization header:
# Authorization: Bearer <token>
#
# tokenUrl also tells Swagger UI which endpoint it should call when you click
# the top-right "Authorize" button. Swagger's OAuth2 password flow sends form
# fields named "username" and "password", so this points to /auth/token instead
# of our JSON-friendly /auth/login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def hash_password(password: str) -> str:
    """
    Convert a plain password into a bcrypt hash.

    We never save the plain password. During login, we hash-check the submitted
    password against this stored hash.
    """
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check whether a submitted password matches the stored hash.

    bcrypt includes a salt inside the hash, so the same password will not always
    produce the same hash string. passlib handles those details for us.
    """
    return password_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    A JWT is a small signed JSON document. The frontend stores it and sends it
    with future requests. Because it is signed, the backend can detect if someone
    tries to edit the token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Read the JWT from the request and return the matching database user.

    Routes can use this as a dependency when they should require login.
    If the token is missing, expired, invalid, or points to a deleted user, the
    request receives a 401 Unauthorized response.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_error

    return user
