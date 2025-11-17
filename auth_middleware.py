"""
Authentication Middleware for FastAPI
======================================

This module provides authentication and authorization for protected endpoints.

How it works:
1. Client logs in → Gets JWT access_token from Supabase
2. Client sends requests with header: Authorization: Bearer <access_token>
3. Middleware verifies token and extracts user_id
4. User_id is made available to endpoint via dependency injection

Why dependency injection instead of global middleware?
- More flexible (some endpoints don't need auth)
- Better error messages (401 for specific endpoints)
- Easier testing
"""

from fastapi import Header, HTTPException, Depends, status
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from supabase_client import supabase
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase JWT secret (from your dashboard)
# Go to: Settings > API > JWT Settings > JWT Secret
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_JWT_SECRET:
    raise ValueError(
        "SUPABASE_JWT_SECRET not found in environment variables!\n"
        "Please add it to your .env file.\n"
        "Get it from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api"
    )


class AuthError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code


async def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract JWT token from Authorization header

    Args:
        authorization: Header value (e.g., "Bearer eyJhbGc...")

    Returns:
        str: JWT token string

    Raises:
        HTTPException: If header missing or malformed

    Example:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header. Please login first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Split "Bearer <token>"
    parts = authorization.split()

    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Expected: Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode Supabase JWT token

    Args:
        token: JWT token string from Supabase

    Returns:
        Dict containing token payload with user_id, email, etc.

    Raises:
        HTTPException: If token invalid, expired, or malformed

    Token structure:
        {
            "sub": "user-uuid-here",  # This is the user_id
            "email": "user@example.com",
            "aud": "authenticated",
            "exp": 1234567890,
            "iat": 1234567890,
            ...
        }
    """
    try:
        # Decode and verify JWT token
        # algorithm='HS256' - Supabase uses HMAC-SHA256
        # audience='authenticated' - Ensures token is for authenticated users
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",  # Supabase sets this
        )

        # Extract user ID from 'sub' (subject) claim
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID (sub claim)",
            )

        return payload

    except jwt.ExpiredSignatureError:
        # Token has expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.JWTClaimsError as e:
        # Invalid claims (wrong audience, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError as e:
        # Any other JWT error (malformed, invalid signature, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(get_token_from_header)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user

    This is the main function you'll use in your endpoints!

    Args:
        token: JWT token (automatically injected by FastAPI)

    Returns:
        Dict with user information from token payload

    Usage:
        @app.get("/protected-endpoint")
        async def protected_route(user: dict = Depends(get_current_user)):
            user_id = user["sub"]  # Get user ID
            email = user["email"]   # Get user email
            return {"message": f"Hello {email}!"}

    Why use Depends?
        - FastAPI automatically calls this function before your endpoint
        - If authentication fails, endpoint is never called
        - Clean separation of auth logic from business logic
        - Easy to test (can mock the dependency)
    """
    payload = await verify_jwt_token(token)
    return payload


async def get_current_user_id(
    user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Convenience dependency to get just the user ID

    Instead of getting full user dict and extracting ID every time,
    use this dependency for cleaner code.

    Args:
        user: User payload (automatically injected)

    Returns:
        str: User UUID

    Usage:
        @app.get("/my-images")
        async def get_my_images(user_id: str = Depends(get_current_user_id)):
            # Use user_id directly!
            images = supabase.table('images').select('*').eq('user_id', user_id).execute()
            return images.data
    """
    return user["sub"]


# Optional: Admin-only dependency
async def get_admin_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency for admin-only endpoints

    Supabase stores user role in user_metadata or app_metadata.
    This is a basic implementation - customize based on your needs.

    Usage:
        @app.delete("/admin/delete-user/{user_id}")
        async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
            # Only admins can reach here
            pass
    """
    # Check if user has admin role
    # Adjust this based on how you store roles in Supabase
    user_metadata = user.get("user_metadata", {})
    app_metadata = user.get("app_metadata", {})

    is_admin = (
        user_metadata.get("role") == "admin" or
        app_metadata.get("role") == "admin"
    )

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


# Optional: Refresh token validation
async def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Refresh an expired access token using refresh token

    Args:
        refresh_token: Refresh token from Supabase

    Returns:
        Dict with new access_token and refresh_token

    Usage:
        @app.post("/auth/refresh")
        async def refresh(refresh_token: str):
            tokens = await refresh_access_token(refresh_token)
            return tokens
    """
    try:
        # Use Supabase client to refresh session
        response = supabase.auth.refresh_session(refresh_token)

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_in": response.session.expires_in,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh token: {str(e)}"
        )


# ============================================================
# USAGE EXAMPLES
# ============================================================

"""
Example 1: Protected endpoint with full user info
--------------------------------------------------
from fastapi import FastAPI, Depends
from auth_middleware import get_current_user

app = FastAPI()

@app.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["sub"],
        "email": user["email"],
        "role": user.get("user_metadata", {}).get("role", "user")
    }


Example 2: Protected endpoint with just user ID
------------------------------------------------
from auth_middleware import get_current_user_id

@app.get("/my-images")
async def get_my_images(user_id: str = Depends(get_current_user_id)):
    images = supabase.table('images').select('*').eq('user_id', user_id).execute()
    return {"images": images.data}


Example 3: Admin-only endpoint
-------------------------------
from auth_middleware import get_admin_user

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    # Only admins can access this
    # Delete user logic here
    return {"message": f"User {user_id} deleted"}


Example 4: Mixed public/protected endpoints
--------------------------------------------
@app.get("/public-endpoint")
async def public():
    # No authentication required
    return {"message": "Hello world"}

@app.get("/protected-endpoint")
async def protected(user_id: str = Depends(get_current_user_id)):
    # Authentication required
    return {"message": f"Hello user {user_id}"}


Example 5: Error handling in your main app
-------------------------------------------
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )
"""
