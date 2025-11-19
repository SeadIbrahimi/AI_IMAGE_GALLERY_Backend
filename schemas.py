from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token received during login/signup")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class AuthResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: Dict[str, Any]
    expires_in: int

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Login successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                },
                "expires_in": 3600,
            }
        }


class UpdateImageMetadataRequest(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    colors: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "description": "A beautiful sunset over the beach",
                "tags": ["sunset", "beach", "ocean", "nature"],
                "colors": ["#FF6B35", "#F39C12", "#4A90E2"],
            }
        }


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    details: Optional[str] = None

