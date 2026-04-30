"""
Authentication routes.

These endpoints let users register and log in using our own JWT-based auth
system. Supabase is used only as PostgreSQL, not as Supabase Auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db


router = APIRouter(prefix="/auth", tags=["Authentication"])


def authenticate_user(email: str, password: str, db: Session) -> models.User:
    """
    Shared login helper for both JSON login and Swagger form login.

    We keep the actual email/password verification in one function so both
    endpoints follow the same rules:
    - normalize the email to lowercase
    - find the user by email
    - compare the submitted password against the saved bcrypt hash
    - return the user only when the credentials are valid
    """
    normalized_email = email.lower()

    user = (
        db.query(models.User)
        .filter(models.User.email == normalized_email)
        .first()
    )

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def build_token_response(user: models.User) -> schemas.TokenResponse:
    """
    Create the response returned after any successful login.

    The token stores the user's id in the JWT subject claim ("sub"). Future
    protected routes decode that id and look up the user again. We never place
    password_hash or other sensitive database fields in the response.
    """
    access_token = create_access_token({"sub": user.id})
    return schemas.TokenResponse(access_token=access_token)


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> models.User:
    """
    Create a new user account.

    Security steps:
    1. Normalize email to lowercase so test@example.com and TEST@example.com
       are treated as the same account.
    2. Check whether the email is already registered.
    3. Hash the password before saving the user.
    """
    normalized_email = user_data.email.lower()

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == normalized_email)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    new_user = models.User(
        email=normalized_email,
        password_hash=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db),
) -> schemas.TokenResponse:
    """
    JSON login endpoint for frontend apps and normal API clients.

    This endpoint accepts JSON shaped like:
    {
        "email": "test@example.com",
        "password": "Test12345"
    }

    Keeping JSON login is beginner-friendly for React/Axios because frontend
    code commonly sends JSON request bodies.
    """
    user = authenticate_user(login_data.email, login_data.password, db)
    return build_token_response(user)


@router.post("/token", response_model=schemas.TokenResponse)
def login_for_swagger_authorize(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> schemas.TokenResponse:
    """
    Swagger-compatible OAuth2 login endpoint.

    FastAPI's Swagger UI follows the OAuth2 password-flow standard. That
    standard sends form data fields named "username" and "password", not JSON
    fields named "email" and "password".

    In this project, the OAuth2 "username" is simply the user's email address.
    This lets the top-right Authorize button in /docs get a JWT while our normal
    /auth/login JSON endpoint continues working for the frontend.
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    return build_token_response(user)
