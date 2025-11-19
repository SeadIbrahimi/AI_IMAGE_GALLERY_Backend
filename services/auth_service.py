from typing import Any, Dict

from fastapi import HTTPException, status

from auth_middleware import verify_jwt_token
from schemas import LoginRequest, RefreshTokenRequest, SignupRequest
from supabase_client import supabase


async def signup_user(auth: SignupRequest) -> Dict[str, Any]:
    try:
        response = supabase.auth.sign_up({"email": auth.email, "password": auth.password})

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed. Email might already be registered.",
            )

        return {
            "message": "User created successfully",
            "access_token": response.session.access_token if response.session else "",
            "refresh_token": response.session.refresh_token if response.session else "",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "expires_in": response.session.expires_in if response.session else 3600,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(e)}",
        )


async def login_user(auth: LoginRequest) -> Dict[str, Any]:
    try:
        response = supabase.auth.sign_in_with_password({"email": auth.email, "password": auth.password})

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return {
            "message": "Login successful",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "expires_in": response.session.expires_in,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}",
        )


async def refresh_access_token(refresh_token_req: RefreshTokenRequest) -> Dict[str, Any]:
    """
    Refresh the access token using the provided refresh token.
    """
    try:
        response = supabase.auth.refresh_session(refresh_token_req.refresh_token)

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        return {
            "message": "Token refreshed successfully",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "expires_in": response.session.expires_in,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        )


async def logout_user(access_token: str) -> Dict[str, Any]:
    """
    Invalidate the current Supabase session using the provided access token.
    """
    try:
        user = await verify_jwt_token(access_token)
        supabase.auth.sign_out()

        return {
            "message": "Logged out successfully",
            "user_id": user["sub"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}",
        )
