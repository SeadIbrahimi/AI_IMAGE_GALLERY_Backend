"""
AI Image Gallery - FastAPI Backend
===================================

This is the main entry point for the FastAPI application.
It handles authentication, image uploads, AI processing, and search.

Run with: uvicorn main:app --reload
API Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.auth_controller import router as auth_router
from controllers.health_controller import router as health_router
from controllers.image_controller import router as image_router
from controllers.meta_controller import router as meta_router


# ============================================================
# FASTAPI APP INITIALIZATION
# ============================================================

app = FastAPI(
    title="AI Image Gallery API",
    description="Backend API for AI-powered image gallery with tagging and search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# CORS MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS (CONTROLLERS)
# ============================================================

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(image_router)
app.include_router(meta_router)
