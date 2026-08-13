"""
FinanceIQ — Turn messy financial documents into structured, queryable data.

FastAPI application entry point.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routers import upload_router, records_router, query_router, analytics_router, categories_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


async def seed_categories():
    """Seed default categories on first run."""
    from app.database import async_session
    from app.models.financial_record import Category
    from app.models.enums import SEED_CATEGORIES
    from sqlalchemy import select, func

    async with async_session() as db:
        # Check if system categories already exist
        count = await db.scalar(
            select(func.count(Category.id)).where(Category.is_system == True)
        )
        if count and count > 0:
            logger.info(f"System categories already seeded ({count} found)")
            return

        # Seed categories
        for group, cats in SEED_CATEGORIES.items():
            for cat in cats:
                category = Category(
                    session_id=None,  # system-wide
                    name=cat["name"],
                    group=group.value,
                    icon=cat["icon"],
                    color=cat["color"],
                    is_system=True,
                )
                db.add(category)

        await db.commit()
        logger.info("Seeded default categories")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Initialize database tables
    await init_db()
    logger.info("Database initialized")
    
    # Seed default categories
    await seed_categories()
    
    yield
    
    logger.info("Shutting down")


# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Turn messy financial documents into structured, queryable data",
    lifespan=lifespan,
)

# CORS middleware
cors_origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload_router)
app.include_router(records_router)
app.include_router(categories_router)
app.include_router(query_router)
app.include_router(analytics_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
