from typing import Any, Dict

from fastapi import APIRouter


router = APIRouter(tags=["Health"])


@router.get(
    "/",
    summary="API health check",
    description="Check if the API is running",
)
async def root() -> Dict[str, Any]:
    import os

    return {
        "status": "online",
        "message": "AI Image Gallery API is running",
        "docs": "/docs",
        "version": "1.0.0",
        "env_check": {
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "missing",
            "SUPABASE_KEY": "set" if os.getenv("SUPABASE_KEY") else "missing",
            "SUPABASE_JWT_SECRET": "set" if os.getenv("SUPABASE_JWT_SECRET") else "missing",
            "OPENAI_API_KEY": "set" if os.getenv("OPENAI_API_KEY") else "missing",
        },
    }

