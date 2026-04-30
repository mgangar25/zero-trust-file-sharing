"""
Main FastAPI application file.

This file is the entry point for the backend API. When you run:

    uvicorn app.main:app --reload

Uvicorn imports this file, finds the variable named `app`, and starts serving it.
"""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import create_database_tables, get_db
from app.routes import audit_routes, auth_routes, file_routes, share_routes


def build_allowed_cors_origins() -> list[str]:
    """
    Return the browser origins allowed to call this API.

    Local development commonly uses Next.js on port 5173 in this project, while
    port 3000 is Next.js's default. In production, Render should receive the
    deployed Vercel origin through FRONTEND_ORIGIN.
    """
    local_dev_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    configured_origins = [
        settings.FRONTEND_ORIGIN,
        # Backward-compatible support for older local .env files.
        settings.FRONTEND_URL,
    ]

    allowed_origins: list[str] = []
    for origin in [*local_dev_origins, *configured_origins]:
        cleaned_origin = origin.strip().rstrip("/") if origin else ""
        if cleaned_origin and cleaned_origin not in allowed_origins:
            allowed_origins.append(cleaned_origin)

    return allowed_origins


# FastAPI creates the web application object.
# It handles incoming HTTP requests, validates data with Pydantic, and sends
# JSON responses back to the client.
app = FastAPI(
    title="Zero-Trust File Sharing System API",
    description="Backend API for a secure portfolio file-sharing project.",
    version="0.1.0",
)


# CORS means "Cross-Origin Resource Sharing".
# Browsers block frontend apps from calling a backend on a different origin
# unless the backend explicitly allows it.
#
# During development, the frontend runs on localhost. In production, set
# FRONTEND_ORIGIN to the deployed Vercel URL. We avoid "*" here because this API
# uses Authorization headers and should only accept browser calls from known
# frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=build_allowed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers keep routes organized by feature area.
# Instead of putting every endpoint in this one file, each route file owns one
# group of related endpoints: auth, files, share links, or audit logs.
app.include_router(auth_routes.router)
app.include_router(file_routes.router)
app.include_router(share_routes.router)
app.include_router(audit_routes.router)


@app.on_event("startup")
def on_startup() -> None:
    """
    Create database tables when the app starts.

    This is useful for the early portfolio/development stage because you can set
    DATABASE_URL to Supabase PostgreSQL and start the app without manually
    writing SQL table creation commands.
    Later, when the schema changes become more serious, Alembic migrations are a
    better professional approach because they track each database change.
    """
    create_database_tables()


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Simple root endpoint.

    This is useful for quickly checking that the API is running in a browser.
    """
    return {
        "message": "Zero-Trust File Sharing System backend is running.",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Deployment platforms and developers often use health checks to confirm that
    the API process is alive. This route intentionally avoids touching the
    database so it can still respond while database setup is in progress.
    """
    return {
        "status": "healthy",
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Safely check database connectivity.

    This route only runs SELECT 1 and returns a generic status. It never prints
    or exposes DATABASE_URL, passwords, usernames, or other secrets.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not reachable.",
        ) from exc

    return {
        "status": "database connected",
    }
