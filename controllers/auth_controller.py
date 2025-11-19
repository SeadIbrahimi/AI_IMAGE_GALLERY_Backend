from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials

from schemas import AuthResponse, LoginRequest, RefreshTokenRequest, SignupRequest
from security import security
from services.auth_service import login_user, logout_user, refresh_access_token, signup_user


router = APIRouter(tags=["Authentication"])


@router.post(
    "/auth/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
)
async def signup(auth: SignupRequest) -> Dict[str, Any]:
    return await signup_user(auth)


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Login to existing account",
)
async def login(auth: LoginRequest) -> Dict[str, Any]:
    return await login_user(auth)


@router.post(
    "/auth/refresh",
    response_model=AuthResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token",
)
async def refresh_token(refresh_req: RefreshTokenRequest) -> Dict[str, Any]:
    return await refresh_access_token(refresh_req)


@router.post(
    "/auth/logout",
    summary="Logout current user",
    description="Invalidate the current session and access token",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    return await logout_user(credentials.credentials)


@router.get(
    "/auth/me",
    summary="Get current user info",
    description="Returns information about the currently authenticated user",
)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)

    return {
        "user_id": user["sub"],
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "user_metadata": user.get("user_metadata", {}),
    }


@router.get(
    "/auth/test",
    summary="Test authentication",
    description="Test if authentication is working",
)
async def test_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    try:
        user = await verify_jwt_token(credentials.credentials)
        return {
            "status": "success",
            "message": "Authentication working correctly",
            "user_id": user["sub"],
            "email": user.get("email"),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Authentication failed: {str(e)}",
            "error_type": type(e).__name__,
        }

