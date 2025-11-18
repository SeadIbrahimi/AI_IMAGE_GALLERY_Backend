from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials

from image_service import get_popular_colors_for_user, get_recent_tags_for_user
from security import security


router = APIRouter()


@router.get(
    "/tags/recent",
    tags=["Tags"],
    summary="Get 6 most recent tags",
    description="Returns the 6 most recently used tags from user's images",
)
async def get_recent_tags(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    return await get_recent_tags_for_user(user_id=user_id, limit=6)


@router.get(
    "/colors/popular",
    tags=["Colors"],
    summary="Get 8 most used colors",
    description="Returns the 8 most frequently used colors from user's images",
)
async def get_popular_colors(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    return await get_popular_colors_for_user(user_id=user_id, limit=8)

