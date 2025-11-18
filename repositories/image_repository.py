from typing import Any, Dict, List, Optional

from supabase_client import supabase


def fetch_user_images_with_metadata(
    user_id: str,
    limit: int,
    offset: int,
    sort_by: str,
) -> Any:
    """
    Low-level data access for fetching a page of images
    with embedded metadata for a given user.
    """

    query = (
        supabase.table("images")
        .select(
            """
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
            """,
        )
        .eq("user_id", user_id)
    )

    if sort_by == "oldest":
        query = query.order("uploaded_at", desc=False)
    else:
        query = query.order("uploaded_at", desc=True)

    query = query.range(offset, offset + limit - 1)
    return query.execute()


def count_user_images(user_id: str) -> int:
    """
    Get total number of images for a user.

    This does not apply search/tag/color filters; it is used
    to populate `totalItems` in the paged `/images` endpoint.
    """
    response = (
        supabase.table("images")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    return getattr(response, "count", None) or 0


def fetch_image_by_id(user_id: str, image_id: int) -> Any:
    return (
        supabase.table("images")
        .select("id, filename, file_size, original_path, thumbnail_path, uploaded_at")
        .eq("id", image_id)
        .eq("user_id", user_id)
        .execute()
    )


def fetch_image_metadata(image_id: int) -> Any:
    return (
        supabase.table("image_metadata")
        .select("description, tags, colors, ai_generated_name, ai_processing_status")
        .eq("image_id", image_id)
        .execute()
    )


def delete_image_record(image_id: int) -> Any:
    return supabase.table("images").delete().eq("id", image_id).execute()


def fetch_image_owner(user_id: str, image_id: int) -> Any:
    return (
        supabase.table("images")
        .select("id, user_id")
        .eq("id", image_id)
        .eq("user_id", user_id)
        .execute()
    )


def fetch_metadata_id_for_image(image_id: int) -> Any:
    return supabase.table("image_metadata").select("id").eq("image_id", image_id).execute()


def upsert_image_metadata(image_id: int, data: Dict[str, Any]) -> None:
    """
    Update or insert image metadata depending on whether a record exists.

    This preserves the behavior from the original endpoint:
    - For updates: only provided fields are changed.
    - For inserts: missing description/tags/colors are defaulted.
    """
    existing = supabase.table("image_metadata").select("id").eq("image_id", image_id).execute()

    if existing.data:
        supabase.table("image_metadata").update(data).eq("image_id", image_id).execute()
    else:
        insert_data = dict(data)
        insert_data["image_id"] = image_id

        if "description" not in insert_data:
            insert_data["description"] = ""
        if "tags" not in insert_data:
            insert_data["tags"] = []
        if "colors" not in insert_data:
            insert_data["colors"] = []

        supabase.table("image_metadata").insert(insert_data).execute()


def fetch_reference_image_with_metadata(image_id: int) -> Any:
    return (
        supabase.table("images")
        .select("id, user_id, image_metadata(description, tags, colors)")
        .eq("id", image_id)
        .execute()
    )


def fetch_user_images_for_similarity(user_id: str, reference_image_id: int) -> List[Dict[str, Any]]:
    response = (
        supabase.table("images")
        .select(
            """
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
            """
        )
        .eq("user_id", user_id)
        .neq("id", reference_image_id)
        .execute()
    )
    return response.data or []


def fetch_images_with_tags(user_id: str) -> Any:
    return (
        supabase.table("images")
        .select("id, uploaded_at, image_metadata(tags)")
        .eq("user_id", user_id)
        .order("uploaded_at", desc=True)
        .execute()
    )


def fetch_images_with_colors(user_id: str) -> Any:
    return supabase.table("images").select("id, image_metadata(colors)").eq("user_id", user_id).execute()
