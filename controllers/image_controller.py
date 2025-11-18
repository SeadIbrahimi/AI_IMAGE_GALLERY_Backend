from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Security, UploadFile, File, status
from fastapi.security import HTTPAuthorizationCredentials

from image_service import (
    delete_user_image,
    get_image_details,
    get_similar_images_for_user,
    get_user_images,
    process_image_upload,
    update_image_metadata_for_user,
)
from schemas import UpdateImageMetadataRequest
from security import security


router = APIRouter(tags=["Images"])


@router.post(
    "/images/upload",
    summary="Upload an image",
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    try:
        user = await verify_jwt_token(credentials.credentials)
        user_id = user["sub"]
        result = await process_image_upload(file, user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.post(
    "/images/upload/bulk",
    summary="Upload multiple images",
)
async def upload_multiple_images(
    files: List[UploadFile] = File(..., description="Multiple image files to upload"),
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    results: Dict[str, Any] = {
        "successful": [],
        "failed": [],
        "total": len(files),
        "success_count": 0,
        "failure_count": 0,
    }

    for file in files:
        try:
            result = await process_image_upload(file, user_id)
            results["successful"].append(
                {
                    "filename": file.filename,
                    "id": result["id"],
                    "message": "Upload successful",
                }
            )
            results["success_count"] += 1
        except HTTPException as e:
            results["failed"].append(
                {
                    "filename": file.filename,
                    "error": e.detail,
                    "status_code": e.status_code,
                }
            )
            results["failure_count"] += 1
        except Exception as e:
            results["failed"].append(
                {
                    "filename": file.filename,
                    "error": str(e),
                    "status_code": 500,
                }
            )
            results["failure_count"] += 1

    return results


@router.get(
    "/images",
    summary="Get user's images with filters and sorting",
)
async def get_images(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    colors: Optional[str] = None,
    sort_by: str = "recent",
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid limit parameter. Must be between 1 and 100",
        )

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid offset parameter. Must be 0 or greater",
        )

    tags_list = [t.strip() for t in tags.split(",")] if tags else None
    colors_list = [c.strip() for c in colors.split(",")] if colors else None

    valid_sort_options = ["recent", "oldest", "a-z", "z-a"]
    if sort_by not in valid_sort_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by parameter. Must be one of: {', '.join(valid_sort_options)}",
        )

    result = await get_user_images(
        user_id=user_id,
        limit=limit,
        offset=offset,
        search=search,
        tags=tags_list,
        colors=colors_list,
        sort_by=sort_by,
    )

    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (result["total"] + limit - 1) // limit if limit > 0 else 1

    return {
        "images": result["images"],
        "total": result["total"],
        "count": len(result["images"]),
        "page": page,
        "limit": limit,
        "offset": offset,
        "total_pages": total_pages,
    }


@router.get(
    "/images/{image_id}",
    summary="Get single image details",
    description="Retrieve details for a specific image by ID",
)
async def get_image_by_id(
    image_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    return await get_image_details(user_id=user_id, image_id=image_id)


@router.delete(
    "/images/{image_id}",
    summary="Delete an image",
    description="Delete an image and all associated data",
)
async def delete_image(
    image_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    return await delete_user_image(user_id=user_id, image_id=image_id)


@router.patch(
    "/images/{image_id}",
    summary="Update image metadata",
    description="Update description, tags, and colors for an image",
)
async def update_image_metadata(
    image_id: int,
    request: UpdateImageMetadataRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    return await update_image_metadata_for_user(
        user_id=user_id,
        image_id=image_id,
        description=request.description,
        tags=request.tags,
        colors=request.colors,
    )


@router.get(
    "/images/{image_id}/similar",
    summary="Find similar images",
    description="Find images similar to the given image based on tags, colors, and description",
)
async def get_similar_images(
    image_id: int,
    limit: int = 6,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    from auth_middleware import verify_jwt_token

    user = await verify_jwt_token(credentials.credentials)
    user_id = user["sub"]

    return await get_similar_images_for_user(user_id=user_id, image_id=image_id, limit=limit)

