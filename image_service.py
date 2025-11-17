"""
Image Service Module
====================

Handles all image-related operations:
- File validation (size, type, content)
- Upload to Supabase Storage
- Thumbnail generation
- Database record creation

Why a separate service file?
- Separation of concerns (main.py stays clean)
- Reusable functions
- Easier testing
- Better organization
"""

import uuid
import io
from typing import Tuple, BinaryIO
from fastapi import UploadFile, HTTPException, status
from PIL import Image
from supabase_client import supabase

# Try to import python-magic, but make it optional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️  Warning: python-magic not available. Skipping magic bytes validation.")
    print("   To enable full validation, install libmagic: brew install libmagic")

# ============================================================
# CONFIGURATION CONSTANTS
# ============================================================

# File validation
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
# Accept all image formats
ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/svg+xml",
    "image/x-icon",
    "image/heic",
    "image/heif"
]
ALLOWED_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".bmp", ".tiff", ".tif", ".svg", ".ico",
    ".heic", ".heif"
]

# Thumbnail settings
THUMBNAIL_SIZE = (300, 300)  # 300x300 pixels

# Storage bucket name
STORAGE_BUCKET = "images"


# ============================================================
# FILE VALIDATION FUNCTIONS
# ============================================================

async def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file

    Checks:
    1. File size (max 10MB)
    2. MIME type (must be image/jpeg or image/png)
    3. Actual file content (prevents fake extensions)

    Args:
        file: FastAPI UploadFile object

    Raises:
        HTTPException: If validation fails

    Why validate file content?
        Someone could rename virus.exe to virus.jpg
        We need to verify the file is actually an image
    """

    # Check 1: File size
    # Read file to get size (UploadFile doesn't have size property)
    contents = await file.read()
    file_size = len(contents)

    # Reset file pointer so we can read it again later
    await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )

    # Check 2: MIME type from Content-Type header
    # Accept any image/* MIME type
    if file.content_type and not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type '{file.content_type}'. Only image files are allowed."
        )

    # Check 3: Actual file content using python-magic (optional)
    # This checks the file's magic bytes (file signature)
    actual_mime_type = file.content_type  # Default to header content type
    if MAGIC_AVAILABLE:
        mime = magic.Magic(mime=True)
        actual_mime_type = mime.from_buffer(contents)

        # Verify it's an image type
        if actual_mime_type and not actual_mime_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File content doesn't match. Detected type: {actual_mime_type}. Only images are allowed."
            )
    else:
        # Skip magic bytes check if library not available
        print("⚠️  Skipping magic bytes validation (python-magic not available)")

    # Check 4: Can we open it as an image?
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # Verify it's a valid image
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )

    # All checks passed!
    print(f"✓ File validation passed: {file.filename}, {file_size} bytes, {actual_mime_type}")


# ============================================================
# THUMBNAIL GENERATION
# ============================================================

def create_thumbnail(image_bytes: bytes, size: Tuple[int, int] = THUMBNAIL_SIZE) -> bytes:
    """
    Create a thumbnail from image bytes

    Args:
        image_bytes: Original image as bytes
        size: Thumbnail size as (width, height) tuple

    Returns:
        Thumbnail image as bytes

    How it works:
        1. Open image from bytes
        2. Resize maintaining aspect ratio
        3. Center crop to exact size
        4. Convert back to bytes

    Why 300x300?
        - Fast loading in gallery view
        - Small file size
        - Good quality for preview
    """

    # Open image
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary (handles PNG transparency)
    if image.mode in ('RGBA', 'LA', 'P'):
        # Create white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # Calculate aspect ratio
    original_width, original_height = image.size
    target_width, target_height = size

    # Calculate scaling to fill the target size
    # We want to cover the entire thumbnail area
    width_ratio = target_width / original_width
    height_ratio = target_height / original_height

    # Use the larger ratio to ensure we fill the entire area
    ratio = max(width_ratio, height_ratio)

    # Calculate new size
    new_size = (int(original_width * ratio), int(original_height * ratio))

    # Resize image
    image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Center crop to exact size
    left = (image.width - target_width) // 2
    top = (image.height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    image = image.crop((left, top, right, bottom))

    # Save to bytes
    thumbnail_bytes = io.BytesIO()
    image.save(thumbnail_bytes, format='JPEG', quality=85, optimize=True)
    thumbnail_bytes.seek(0)

    return thumbnail_bytes.getvalue()


# ============================================================
# STORAGE UPLOAD FUNCTIONS
# ============================================================

async def upload_to_storage(
    file_bytes: bytes,
    user_id: str,
    filename: str,
    folder: str = "original"
) -> str:
    """
    Upload file to Supabase Storage

    Args:
        file_bytes: File content as bytes
        user_id: User's UUID
        filename: Original filename
        folder: Subfolder (original or thumbnail)

    Returns:
        Storage path of uploaded file

    Storage structure:
        images/
        ├── {user_id}/
        │   ├── original/
        │   │   ├── {uuid}.jpg
        │   │   └── {uuid}.png
        │   └── thumbnail/
        │       ├── {uuid}.jpg
        │       └── {uuid}.png

    Why UUIDs?
        - Prevent filename collisions
        - Obscure original filenames (security)
        - Consistent naming
    """

    # Generate unique filename
    file_extension = filename.lower().split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    # Build storage path
    # Format: user_id/folder/unique_filename.ext
    storage_path = f"{user_id}/{folder}/{unique_filename}"

    # Map file extensions to proper MIME types
    # This fixes issues like .jpg -> image/jpg (should be image/jpeg)
    mime_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
        'svg': 'image/svg+xml',
        'ico': 'image/x-icon',
        'heic': 'image/heic',
        'heif': 'image/heif'
    }

    # Get proper MIME type, default to image/extension if not in map
    content_type = mime_type_map.get(file_extension, f"image/{file_extension}")

    try:
        # Upload to Supabase Storage
        response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "cache-control": "3600",  # Cache for 1 hour
                "upsert": "false"  # Don't overwrite existing files
            }
        )

        print(f"✓ Uploaded to storage: {storage_path}")
        return storage_path

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload to storage: {str(e)}"
        )


async def delete_from_storage(storage_path: str) -> None:
    """
    Delete file from Supabase Storage

    Args:
        storage_path: Path to file in storage

    Used for:
        - Cleanup on upload failure
        - User deleting images
    """
    try:
        supabase.storage.from_(STORAGE_BUCKET).remove([storage_path])
        print(f"✓ Deleted from storage: {storage_path}")
    except Exception as e:
        # Log but don't raise - cleanup is best effort
        print(f"⚠ Failed to delete from storage: {storage_path}, Error: {str(e)}")


# ============================================================
# DATABASE OPERATIONS
# ============================================================

async def create_image_record(
    user_id: str,
    filename: str,
    file_size: int,
    mime_type: str,
    original_path: str,
    thumbnail_path: str
) -> dict:
    """
    Create database record for uploaded image

    Args:
        user_id: User's UUID
        filename: Original filename
        file_size: File size in bytes
        mime_type: MIME type (image/jpeg or image/png)
        original_path: Path to original image in storage
        thumbnail_path: Path to thumbnail in storage

    Returns:
        Created image record

    Why separate function?
        - Reusable
        - Easier to test
        - Can be called from background jobs
    """
    try:
        # Insert into images table
        response = supabase.table('images').insert({
            'user_id': user_id,
            'filename': filename,
            'file_size': file_size,
            'mime_type': mime_type,
            'original_path': original_path,
            'thumbnail_path': thumbnail_path
        }).execute()

        if not response.data:
            raise Exception("Failed to create database record")

        image_record = response.data[0]
        print(f"✓ Created image record: ID={image_record['id']}")

        # Create metadata record (for AI processing later)
        metadata_response = supabase.table('image_metadata').insert({
            'image_id': image_record['id'],
            'user_id': user_id,
            'ai_processing_status': 'pending'
        }).execute()

        print(f"✓ Created metadata record for image ID={image_record['id']}")

        return image_record

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create database record: {str(e)}"
        )


# ============================================================
# MAIN UPLOAD FUNCTION
# ============================================================

async def process_image_upload(file: UploadFile, user_id: str) -> dict:
    """
    Main function to process image upload

    This orchestrates the entire upload process:
    1. Validate file
    2. Read file contents
    3. Generate thumbnail
    4. Upload original to storage
    5. Upload thumbnail to storage
    6. Create database record
    7. Return success response

    Args:
        file: Uploaded file
        user_id: User's UUID

    Returns:
        dict with image info

    Error handling:
        If any step fails, we cleanup (delete uploaded files)
        This prevents orphaned files in storage
    """

    original_path = None
    thumbnail_path = None

    try:
        # Step 1: Validate file
        await validate_image_file(file)

        # Step 2: Read file contents
        file_contents = await file.read()
        file_size = len(file_contents)

        # Step 3: Generate thumbnail
        print("Generating thumbnail...")
        thumbnail_bytes = create_thumbnail(file_contents)
        print(f"✓ Thumbnail generated: {len(thumbnail_bytes)} bytes")

        # Step 4: Upload original image
        print("Uploading original image...")
        original_path = await upload_to_storage(
            file_bytes=file_contents,
            user_id=user_id,
            filename=file.filename,
            folder="original"
        )

        # Step 5: Upload thumbnail
        print("Uploading thumbnail...")
        thumbnail_path = await upload_to_storage(
            file_bytes=thumbnail_bytes,
            user_id=user_id,
            filename=file.filename,
            folder="thumbnail"
        )

        # Step 6: Create database record
        print("Creating database record...")
        image_record = await create_image_record(
            user_id=user_id,
            filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type,
            original_path=original_path,
            thumbnail_path=thumbnail_path
        )

        # Step 7: Process with AI (async, doesn't block response)
        print(f"Starting AI analysis for image ID={image_record['id']}...")
        try:
            from ai_service import process_image_with_ai
            # Process AI in background without blocking the response
            import asyncio
            asyncio.create_task(
                process_image_with_ai(
                    image_bytes=file_contents,
                    image_id=image_record['id'],
                    user_id=user_id
                )
            )
            print("✓ AI processing queued")
        except Exception as e:
            print(f"⚠️  AI processing failed to queue: {str(e)}")
            # Don't fail the upload if AI fails

        # Step 8: Success!
        return {
            "id": image_record['id'],
            "filename": image_record['filename'],
            "file_size": image_record['file_size'],
            "original_path": original_path,
            "thumbnail_path": thumbnail_path,
            "uploaded_at": image_record['uploaded_at'],
            "message": "Image uploaded successfully. AI processing will begin shortly."
        }

    except HTTPException:
        # Re-raise HTTP exceptions (already have proper status codes)
        # But first cleanup any uploaded files
        if original_path:
            await delete_from_storage(original_path)
        if thumbnail_path:
            await delete_from_storage(thumbnail_path)
        raise

    except Exception as e:
        # Cleanup uploaded files
        if original_path:
            await delete_from_storage(original_path)
        if thumbnail_path:
            await delete_from_storage(thumbnail_path)

        # Raise generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )


# ============================================================
# GET IMAGE URL FUNCTIONS
# ============================================================

def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate signed URL for private image

    Args:
        storage_path: Path to file in storage
        expires_in: URL expiration time in seconds (default: 1 hour)

    Returns:
        Temporary signed URL

    Why signed URLs?
        - Bucket is private (RLS protected)
        - Need temporary access tokens
        - URLs expire for security

    When to use:
        - Displaying images to authenticated users
        - Downloading images
    """
    try:
        response = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return response['signedURL']
    except Exception as e:
        print(f"⚠ Failed to generate signed URL for {storage_path}: {str(e)}")
        return None


async def get_user_images(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    search: str = None,
    tags: list = None,
    colors: list = None,
    sort_by: str = "recent"
) -> dict:
    """
    Get user's images with signed URLs, filtering, and sorting

    Args:
        user_id: User's UUID
        limit: Number of images to return
        offset: Pagination offset
        search: Text search in description, tags, and filename
        tags: List of tags to filter by
        colors: List of colors to filter by
        sort_by: Sort order (recent, oldest, a-z, z-a)

    Returns:
        Dict with images list and total count

    Uses:
        - Gallery view with filters
        - Image listing
        - Search functionality
    """
    try:
        # Build base query for images with metadata join
        # Use left join (!left) to include images without metadata
        query = supabase.table('images').select(
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
            ''',
            count='exact'
        ).eq('user_id', user_id)

        # NOTE: We don't apply database-level filters for tags/colors/search here
        # because the left join with image_metadata might return null values
        # We'll filter in Python after fetching the data

        # Apply sorting
        if sort_by == "oldest":
            query = query.order('uploaded_at', desc=False)
        elif sort_by == "recent":
            query = query.order('uploaded_at', desc=True)
        # For a-z and z-a, we'll sort in Python after adding display_name
        else:
            # Default to recent for now, will sort by display_name later
            query = query.order('uploaded_at', desc=True)

        # Apply pagination and execute query (count is included in response)
        query = query.range(offset, offset + limit - 1)
        response = query.execute()

        # Get total count from response
        total_count = response.count if hasattr(response, 'count') else len(response.data)
        images = response.data

        # Extract metadata from nested structure and flatten
        # Handle both list and dict embeds from Supabase
        for image in images:
            meta = image.get('image_metadata')

            # Normalize metadata to dict (handle list, dict, or None)
            if isinstance(meta, list):
                meta = meta[0] if meta else None
            elif not isinstance(meta, dict):
                meta = None

            # Extract metadata fields with fallbacks
            meta = meta or {}
            image['description'] = meta.get('description', '')
            image['tags'] = meta.get('tags') or []
            image['colors'] = meta.get('colors') or []
            image['ai_generated_name'] = meta.get('ai_generated_name')

            # Remove the nested metadata structure
            image.pop('image_metadata', None)

        # Apply filters in Python (after fetching data)
        filtered_images = images

        # Apply tags filter (image must have ALL specified tags)
        if tags and len(tags) > 0:
            filtered_images = [
                img for img in filtered_images
                if img.get('tags') and all(tag in img.get('tags', []) for tag in tags)
            ]

        # Apply colors filter (image must have ALL specified colors)
        if colors and len(colors) > 0:
            filtered_images = [
                img for img in filtered_images
                if img.get('colors') and all(color in img.get('colors', []) for color in colors)
            ]

        # Apply text search filter
        if search:
            search_lower = search.lower()
            search_filtered = []
            for image in filtered_images:
                # Search in description (handle None)
                description = image.get('description') or ''
                if search_lower in description.lower():
                    search_filtered.append(image)
                    continue
                # Search in tags (handle None and empty arrays)
                tags = image.get('tags') or []
                if any(search_lower in (tag or '').lower() for tag in tags):
                    search_filtered.append(image)
                    continue
                # Search in filename (handle None)
                filename = image.get('filename') or ''
                if search_lower in filename.lower():
                    search_filtered.append(image)
                    continue
                # Search in AI-generated name (handle None)
                ai_name = image.get('ai_generated_name') or ''
                if ai_name and search_lower in ai_name.lower():
                    search_filtered.append(image)
                    continue
            filtered_images = search_filtered

        # Update images and total count after all filters
        images = filtered_images
        total_count = len(images)

        # Add signed URLs and display names
        for image in images:
            image['thumbnail_url'] = get_signed_url(image['thumbnail_path'])
            image['original_url'] = get_signed_url(image['original_path'])

            # Add display_name: AI-generated name if available, otherwise original filename
            if image.get('ai_generated_name'):
                image['display_name'] = image['ai_generated_name']
            else:
                # Use original filename without extension as fallback
                filename_without_ext = image['filename'].rsplit('.', 1)[0]
                image['display_name'] = filename_without_ext

        # Apply alphabetical sorting by display_name if requested
        if sort_by == "a-z":
            images = sorted(images, key=lambda x: x['display_name'].lower())
        elif sort_by == "z-a":
            images = sorted(images, key=lambda x: x['display_name'].lower(), reverse=True)

        return {
            "images": images,
            "total": total_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch images: {str(e)}"
        )
