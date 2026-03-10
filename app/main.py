"""
Application entry point.

Responsibilities:
- Create the FastAPI application instance with OpenAPI metadata.
- Register all routers.
- Define the startup lifecycle event that:
    1. Creates all ORM tables (idempotent).
    2. Seeds test users when the table is empty.
"""

import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import get_settings
# Import all models so SQLAlchemy registers them before create_all()
from app.models import user as _user_models  # noqa: F401
from app.database import Base, engine, SessionLocal
from app.api.routers.auth import router as auth_router
from app.api.routers.auth import users_router
from app.api.routers.dummy import router as dummy_router
from app.services.user_service import UserService

settings = get_settings()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data — one test user per role
# ---------------------------------------------------------------------------

SEED_USERS = [
    {
        "username": "user_community",
        "email": "community@example.com",
        "password": "Community123!",
        "role": "Community",
    },
    {
        "username": "user_operational",
        "email": "operational@example.com",
        "password": "Operational123!",
        "role": "Operational",
    },
    {
        "username": "user_manager",
        "email": "manager@example.com",
        "password": "Manager123!",
        "role": "Manager",
    },
]


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed DB.  Shutdown: nothing to clean up."""
    logger.info("Starting up — creating database tables...")

    # PostgreSQL does not support `CREATE TYPE IF NOT EXISTS`.
    # The idiomatic workaround is a PL/pgSQL DO block that silently ignores
    # `duplicate_object` errors, making it safe for multi-worker starts and
    # container restarts against an existing database.
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'roleenum'
                ) THEN
                    CREATE TYPE roleenum AS ENUM (
                        'Community', 'Operational', 'Manager'
                    );
                END IF;
            END
            $$;
            """
        ))

    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        logger.info("Checking whether seed users are needed...")
        UserService(db).seed_if_empty(SEED_USERS)
        logger.info("Seed check complete.")
    finally:
        db.close()

    yield  # application is now running

    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "DAGRD API — FastAPI baseline with layered architecture, "
            "stateless JWT auth, PostgreSQL and Docker support."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — restrict origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(dummy_router)

    @app.get("/health", tags=["Health"])
    def health_check() -> dict:
        """Simple liveness probe."""
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
