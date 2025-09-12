import logging
from contextlib import asynccontextmanager

import uvicorn
from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import chat
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Phoenix AI Assistant")

    # Startup events
    yield

    # Shutdown events
    logger.info("Shutting down Phoenix AI Assistant")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI Assistant for Phoenix, Arizona public safety and city information",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# Include routers
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Phoenix AI Assistant API",
        "version": "1.0.0",
        "status": "active",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
