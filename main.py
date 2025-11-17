"""
AI Image Gallery - FastAPI Backend
===================================

This is the main entry point for the FastAPI application.
It handles authentication, image uploads, AI processing, and search.

Run with: uvicorn main:app --reload
API Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException,  status, UploadFile, File, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from supabase_client import supabase
from image_service import process_image_upload, get_user_images, get_signed_url

security = HTTPBearer()

# ============================================================
# FASTAPI APP INITIALIZATION
# ============================================================

app = FastAPI(
    title="AI Image Gallery API",
    description="Backend API for AI-powered image gallery with tagging and search",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
)

# ============================================================
# CORS MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ============================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================

class SignupRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
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
                    "email": "user@example.com"
                },
                "expires_in": 3600
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
                "colors": ["#FF6B35", "#F39C12", "#4A90E2"]
            }
        }


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    details: Optional[str] = None


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post(
    "/auth/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    summary="Create new user account",
)
async def signup(auth: SignupRequest):
    try:
        # Sign up user with Supabase
        response = supabase.auth.sign_up({
            "email": auth.email,
            "password": auth.password
        })

        # Check if signup was successful
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed. Email might already be registered."
            )

        return {
            "message": "User created successfully",
            "access_token": response.session.access_token if response.session else "",
            "refresh_token": response.session.refresh_token if response.session else "",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "expires_in": response.session.expires_in if response.session else 3600
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(e)}"
        )


@app.post(
    "/auth/login",
    response_model=AuthResponse,
    tags=["Authentication"],
    summary="Login to existing account",
)
async def login(auth: LoginRequest):
    try:
        # Sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": auth.email,
            "password": auth.password
        })

        # Check if login was successful
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        return {
            "message": "Login successful",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
            "expires_in": response.session.expires_in
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


@app.post(
    "/auth/logout",
    tags=["Authentication"],
    summary="Logout current user",
    description="Invalidate the current session and access token"
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    try:
        from auth_middleware import verify_jwt_token

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)

        # Supabase handles session invalidation
        supabase.auth.sign_out()

        return {
            "message": "Logged out successfully",
            "user_id": user["sub"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )


@app.get(
    "/auth/me",
    tags=["Authentication"],
    summary="Get current user info",
    description="Returns information about the currently authenticated user"
)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    from auth_middleware import verify_jwt_token

    # Verify token and get user info
    user = await verify_jwt_token(credentials.credentials)

    return {
        "user_id": user["sub"],
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "user_metadata": user.get("user_metadata", {}),
    }


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["Health"],
    summary="API health check",
    description="Check if the API is running"
)
async def root():
    return {
        "status": "online",
        "message": "AI Image Gallery API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


# ============================================================
# IMAGE UPLOAD ENDPOINTS
# ============================================================

@app.post(
    "/images/upload",
    tags=["Images"],
    summary="Upload an image",
    
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    from auth_middleware import verify_jwt_token

    # Verify token and get user info
    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    result = await process_image_upload(file, user_id)
    return result


@app.post(
    "/images/upload/bulk",
    tags=["Images"],
    summary="Upload multiple images",
   
)
async def upload_multiple_images(
    files: List[UploadFile] = File(..., description="Multiple image files to upload"),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    from auth_middleware import verify_jwt_token

    # Verify token and get user info
    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    results = {
        "successful": [],
        "failed": [],
        "total": len(files),
        "success_count": 0,
        "failure_count": 0
    }

    # Process each file
    for file in files:
        try:
            result = await process_image_upload(file, user_id)
            results["successful"].append({
                "filename": file.filename,
                "id": result["id"],
                "message": "Upload successful"
            })
            results["success_count"] += 1
        except HTTPException as e:
            results["failed"].append({
                "filename": file.filename,
                "error": e.detail,
                "status_code": e.status_code
            })
            results["failure_count"] += 1
        except Exception as e:
            results["failed"].append({
                "filename": file.filename,
                "error": str(e),
                "status_code": 500
            })
            results["failure_count"] += 1

    return results


@app.get(
    "/images",
    tags=["Images"],
    summary="Get user's images with filters and sorting",
   
)
async def get_images(
    limit: int = 20,
    offset: int = 0,
    search: str = None,
    tags: str = None,
    colors: str = None,
    sort_by: str = "recent",
    credentials: HTTPAuthorizationCredentials = Security(security)
):
   
    from auth_middleware import verify_jwt_token

    # Verify token and get user info
    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    # Validate limit parameter
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid limit parameter. Must be between 1 and 100"
        )

    # Validate offset parameter
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid offset parameter. Must be 0 or greater"
        )

    # Parse comma-separated tags and colors into lists
    tags_list = [t.strip() for t in tags.split(',')] if tags else None
    colors_list = [c.strip() for c in colors.split(',')] if colors else None

    # Validate sort_by parameter
    valid_sort_options = ["recent", "oldest", "a-z", "z-a"]
    if sort_by not in valid_sort_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by parameter. Must be one of: {', '.join(valid_sort_options)}"
        )

    # Get filtered and sorted images
    result = await get_user_images(
        user_id=user_id,
        limit=limit,
        offset=offset,
        search=search,
        tags=tags_list,
        colors=colors_list,
        sort_by=sort_by
    )

    # Calculate page number and total pages
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (result['total'] + limit - 1) // limit if limit > 0 else 1

    return {
        "images": result['images'],
        "total": result['total'],
        "count": len(result['images']),
        "page": page,
        "limit": limit,
        "offset": offset,
        "total_pages": total_pages
    }


@app.get(
    "/images/{image_id}",
    tags=["Images"],
    summary="Get single image details",
    description="Retrieve details for a specific image by ID"
)
async def get_image_by_id(
    image_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    
    try:
        from auth_middleware import verify_jwt_token
        from image_service import get_signed_url

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]

        # Fetch image from database
        response = supabase.table('images').select(
            'id, filename, file_size, original_path, thumbnail_path, uploaded_at'
        ).eq('id', image_id).eq('user_id', user_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        image = response.data[0]

        # Add signed URLs
        image['thumbnail_url'] = get_signed_url(image['thumbnail_path'])
        image['original_url'] = get_signed_url(image['original_path'])

        # Fetch metadata
        metadata_response = supabase.table('image_metadata').select(
            'description, tags, colors, ai_generated_name, ai_processing_status'
        ).eq('image_id', image_id).execute()

        if metadata_response.data:
            image['metadata'] = metadata_response.data[0]

        # Add display_name: AI-generated name if available, otherwise original filename
        if metadata_response.data and metadata_response.data[0].get('ai_generated_name'):
            image['display_name'] = metadata_response.data[0]['ai_generated_name']
        else:
            # Use original filename without extension as fallback
            filename_without_ext = image['filename'].rsplit('.', 1)[0]
            image['display_name'] = filename_without_ext

        return image

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch image: {str(e)}"
        )


@app.delete(
    "/images/{image_id}",
    tags=["Images"],
    summary="Delete an image",
    description="Delete an image and all associated data"
)
async def delete_image(
    image_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    
    try:
        from auth_middleware import verify_jwt_token
        from image_service import delete_from_storage

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]

        # Fetch image to get storage paths
        response = supabase.table('images').select(
            'id, original_path, thumbnail_path'
        ).eq('id', image_id).eq('user_id', user_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        image = response.data[0]

        # Delete from storage
        await delete_from_storage(image['original_path'])
        await delete_from_storage(image['thumbnail_path'])

        # Delete from database (metadata will cascade delete)
        supabase.table('images').delete().eq('id', image_id).execute()

        return {
            "message": "Image deleted successfully",
            "image_id": image_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}"
        )


@app.patch(
    "/images/{image_id}",
    tags=["Images"],
    summary="Update image metadata",
    description="Update description, tags, and colors for an image"
)
async def update_image_metadata(
    image_id: int,
    request: UpdateImageMetadataRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    
    try:
        from auth_middleware import verify_jwt_token

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]

        # Check if at least one field is provided
        if request.description is None and request.tags is None and request.colors is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field (description, tags, or colors) must be provided"
            )

        # Verify image exists and belongs to user
        image_response = supabase.table('images').select('id, user_id').eq(
            'id', image_id
        ).eq('user_id', user_id).execute()

        if not image_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Check if metadata record exists
        metadata_response = supabase.table('image_metadata').select('id').eq(
            'image_id', image_id
        ).execute()

        # Build update data (only include provided fields)
        update_data = {}
        if request.description is not None:
            update_data['description'] = request.description
        if request.tags is not None:
            # Validate tags
            if not isinstance(request.tags, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tags must be an array of strings"
                )
            update_data['tags'] = request.tags
        if request.colors is not None:
            # Validate colors
            if not isinstance(request.colors, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Colors must be an array of strings"
                )
            # Basic hex color validation
            for color in request.colors:
                if not color.startswith('#') or len(color) not in [4, 7]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid color format: {color}. Expected hex format like #FF6B35"
                    )
            update_data['colors'] = request.colors

        # Update or insert metadata
        if metadata_response.data:
            # Update existing metadata
            result = supabase.table('image_metadata').update(update_data).eq(
                'image_id', image_id
            ).execute()
        else:
            # Insert new metadata record
            update_data['image_id'] = image_id
            # Set defaults for missing fields
            if 'description' not in update_data:
                update_data['description'] = ''
            if 'tags' not in update_data:
                update_data['tags'] = []
            if 'colors' not in update_data:
                update_data['colors'] = []

            result = supabase.table('image_metadata').insert(update_data).execute()

        # Fetch updated metadata
        updated_metadata = supabase.table('image_metadata').select(
            'description, tags, colors, ai_generated_name'
        ).eq('image_id', image_id).execute()

        if not updated_metadata.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch updated metadata"
            )

        return {
            "message": "Image metadata updated successfully",
            "image_id": image_id,
            "metadata": updated_metadata.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update image metadata: {str(e)}"
        )


@app.get(
    "/images/{image_id}/similar",
    tags=["Images"],
    summary="Find similar images",
    description="Find images similar to the given image based on tags, colors, and description"
)
async def get_similar_images(
    image_id: int,
    limit: int = 6,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    
    try:
        from auth_middleware import verify_jwt_token

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]

        # Validate limit
        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 50"
            )

        # Get the reference image with metadata
        ref_response = supabase.table('images').select(
            'id, user_id, image_metadata(description, tags, colors)'
        ).eq('id', image_id).execute()

        if not ref_response.data or len(ref_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference image not found"
            )

        ref_image = ref_response.data[0]

        # Check ownership
        if ref_image['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this image"
            )

        # Extract reference image metadata
        ref_meta = ref_image.get('image_metadata')
        if isinstance(ref_meta, list):
            ref_meta = ref_meta[0] if ref_meta else None
        elif not isinstance(ref_meta, dict):
            ref_meta = None

        ref_meta = ref_meta or {}
        ref_tags = set(ref_meta.get('tags') or [])
        ref_colors = set(ref_meta.get('colors') or [])
        ref_description = (ref_meta.get('description') or '').lower()

        # Extract keywords from description (simple approach: split by space and filter)
        ref_keywords = set([
            word for word in ref_description.split()
            if len(word) > 3  # Only words longer than 3 characters
        ])

        # Get all user's images except the reference image
        all_images_response = supabase.table('images').select(
            '''
            id,
            filename,
            file_size,
            original_path,
            thumbnail_path,
            uploaded_at,
            image_metadata(
                description,
                tags,
                colors,
                ai_generated_name
            )
            '''
        ).eq('user_id', user_id).neq('id', image_id).execute()

        images = all_images_response.data

        # Calculate similarity for each image
        similar_images = []

        for image in images:
            # Extract metadata
            meta = image.get('image_metadata')
            if isinstance(meta, list):
                meta = meta[0] if meta else None
            elif not isinstance(meta, dict):
                meta = None

            meta = meta or {}
            tags = set(meta.get('tags') or [])
            colors = set(meta.get('colors') or [])
            description = (meta.get('description') or '').lower()

            # Calculate similarity components
            # 1. Tag similarity (most important)
            if ref_tags:
                tag_matches = len(ref_tags.intersection(tags))
                tag_similarity = (tag_matches / len(ref_tags)) * 100
            else:
                tag_similarity = 0

            # 2. Color similarity
            if ref_colors:
                color_matches = len(ref_colors.intersection(colors))
                color_similarity = (color_matches / len(ref_colors)) * 100
            else:
                color_similarity = 0

            # 3. Description keyword similarity
            if ref_keywords:
                keywords = set([
                    word for word in description.split()
                    if len(word) > 3
                ])
                keyword_matches = len(ref_keywords.intersection(keywords))
                keyword_similarity = (keyword_matches / len(ref_keywords)) * 100
            else:
                keyword_similarity = 0

            # Calculate weighted similarity percentage
            # Tags: 50%, Colors: 30%, Keywords: 20%
            similarity_percentage = (
                (tag_similarity * 0.5) +
                (color_similarity * 0.3) +
                (keyword_similarity * 0.2)
            )

            # Only include images with some similarity (>0%)
            if similarity_percentage > 0:
                # Flatten metadata
                image['description'] = meta.get('description', '')
                image['tags'] = meta.get('tags') or []
                image['colors'] = meta.get('colors') or []
                image['ai_generated_name'] = meta.get('ai_generated_name')
                image.pop('image_metadata', None)

                # Add signed URLs and display name
                image['thumbnail_url'] = get_signed_url(image['thumbnail_path'])
                image['original_url'] = get_signed_url(image['original_path'])

                if image.get('ai_generated_name'):
                    image['display_name'] = image['ai_generated_name']
                else:
                    filename_without_ext = image['filename'].rsplit('.', 1)[0]
                    image['display_name'] = filename_without_ext

                # Add similarity percentage (rounded to 1 decimal)
                image['similarity_percentage'] = round(similarity_percentage, 1)

                similar_images.append(image)

        # Sort by similarity percentage (highest first)
        similar_images.sort(key=lambda x: x['similarity_percentage'], reverse=True)

        # Limit results
        similar_images = similar_images[:limit]

        return {
            "reference_image_id": image_id,
            "similar_images": similar_images,
            "count": len(similar_images)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar images: {str(e)}"
        )


# ============================================================
# TAGS AND COLORS ENDPOINTS
# ============================================================

@app.get(
    "/tags/recent",
    tags=["Tags"],
    summary="Get 6 most recent tags",
    description="Returns the 6 most recently used tags from user's images"
)
async def get_recent_tags(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    try:
        from auth_middleware import verify_jwt_token

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]

        # Fetch images with metadata, ordered by upload date (most recent first)
        response = supabase.table('images').select(
            'id, uploaded_at, image_metadata(tags)'
        ).eq('user_id', user_id).order(
            'uploaded_at', desc=True
        ).execute()

        # Extract unique tags in order (most recent first)
        seen_tags = set()
        recent_tags = []

        for image in response.data:
            # Handle metadata (can be dict, list, or None)
            metadata = image.get('image_metadata')
            if isinstance(metadata, list):
                metadata = metadata[0] if metadata else None
            elif not isinstance(metadata, dict):
                metadata = None

            tags = (metadata or {}).get('tags') or []

            for tag in tags:
                if tag not in seen_tags:
                    seen_tags.add(tag)
                    recent_tags.append(tag)
                    if len(recent_tags) >= 6:
                        break
            if len(recent_tags) >= 6:
                break

        return {
            "tags": recent_tags,
            "count": len(recent_tags)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent tags: {str(e)}"
        )


@app.get(
    "/colors/popular",
    tags=["Colors"],
    summary="Get 8 most used colors",
    description="Returns the 8 most frequently used colors from user's images"
)
async def get_popular_colors(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    try:
        from auth_middleware import verify_jwt_token
        from collections import Counter

        # Verify token and get user info
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]

        # Fetch images with metadata for this user
        response = supabase.table('images').select(
            'id, image_metadata(colors)'
        ).eq('user_id', user_id).execute()

        # Count color occurrences
        color_counter = Counter()
        for image in response.data:
            # Handle metadata (can be dict, list, or None)
            metadata = image.get('image_metadata')
            if isinstance(metadata, list):
                metadata = metadata[0] if metadata else None
            elif not isinstance(metadata, dict):
                metadata = None

            colors = (metadata or {}).get('colors') or []
            for color in colors:
                color_counter[color] += 1

        # Get top 8 most common colors
        top_colors = color_counter.most_common(8)

        return {
            "colors": [
                {
                    "color": color,
                    "count": count
                }
                for color, count in top_colors
            ],
            "total": len(top_colors)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch popular colors: {str(e)}"
        )
