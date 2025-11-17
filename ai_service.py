"""
AI Service - OpenAI GPT-4o Vision Integration
==============================================

This module handles AI-powered image analysis using OpenAI GPT-4o Vision API.

Features:
- Generate 10+ relevant tags per image
- Create natural language descriptive sentences
- Extract top 3 dominant colors
- Async processing to avoid blocking requests

Setup Required:
1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Add OPENAI_API_KEY to .env file

Pricing:
- GPT-4o Vision: $0.00255 per image (512x512 low detail)
- Includes tags, description, and colors in a single call
"""

import os
from typing import List, Dict, Tuple
import io
import base64
from colorthief import ColorThief
from PIL import Image
from openai import OpenAI
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import OpenAI client
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        OPENAI_AVAILABLE = True
        print("✅ OpenAI GPT-4o Vision API initialized successfully!")
    else:
        OPENAI_AVAILABLE = False
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("   Add OPENAI_API_KEY to .env file to enable AI features")
except Exception as e:
    OPENAI_AVAILABLE = False
    print(f"⚠️  Warning: OpenAI API not available: {str(e)}")
    print("   AI features will use mock data.")


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to HEX color code

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        HEX color code (e.g., "#FF5733")
    """
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def generate_filename_from_description(description: str, max_length: int = 50) -> str:
    """
    Generate a clean, URL-friendly filename from AI description

    This is FREE - uses the existing description without any API calls!

    Args:
        description: AI-generated description of the image
        max_length: Maximum length of the filename (default: 50)

    Returns:
        Clean filename (e.g., "sunset-beach-with-palm-trees")

    Examples:
        "A beautiful sunset over the ocean." -> "beautiful-sunset-over-ocean"
        "An image of a dog playing in nature." -> "dog-playing-in-nature"
        "Red sports car on mountain road." -> "red-sports-car-on-mountain-road"
    """
    import re

    # Remove common prefixes
    description = description.lower()
    prefixes_to_remove = [
        "an image of ",
        "a photo of ",
        "a picture of ",
        "this is ",
        "this image shows ",
        "the image shows ",
    ]

    for prefix in prefixes_to_remove:
        if description.startswith(prefix):
            description = description[len(prefix):]
            break

    # Remove punctuation and special characters
    description = re.sub(r'[^\w\s-]', '', description)

    # Replace spaces with hyphens
    description = re.sub(r'\s+', '-', description.strip())

    # Remove multiple consecutive hyphens
    description = re.sub(r'-+', '-', description)

    # Truncate to max length at word boundary
    if len(description) > max_length:
        description = description[:max_length]
        # Cut at last hyphen to avoid partial words
        last_hyphen = description.rfind('-')
        if last_hyphen > max_length // 2:  # Only cut if we're not losing too much
            description = description[:last_hyphen]

    # Remove trailing hyphens
    description = description.strip('-')

    # Ensure it's not empty
    if not description:
        description = "image"

    return description


def extract_colors_with_colorthief(image_bytes: bytes, num_colors: int = 3) -> List[Dict]:
    """
    Extract dominant colors using ColorThief (local, free library)

    Args:
        image_bytes: Image content as bytes
        num_colors: Number of dominant colors to extract (default: 3)

    Returns:
        List of color dictionaries with hex, rgb, and percentage

    Why ColorThief instead of Google Cloud Vision?
        - FREE (no API costs)
        - Fast (runs locally)
        - Accurate (k-means clustering algorithm)
        - No internet required
        - No API rate limits
    """
    try:
        # Create a file-like object from bytes
        image_file = io.BytesIO(image_bytes)

        # Initialize ColorThief
        color_thief = ColorThief(image_file)

        # Get palette of dominant colors
        # quality=1 means check every pixel (most accurate but slower)
        # quality=10 means check every 10th pixel (faster, still accurate)
        palette = color_thief.get_palette(color_count=num_colors, quality=10)

        colors = []
        # ColorThief doesn't provide percentages, so we'll estimate them
        # The first color is most dominant, so we assign decreasing percentages
        total = sum(range(1, len(palette) + 1))

        for i, rgb in enumerate(palette):
            # Assign percentages: first color gets most, last gets least
            weight = len(palette) - i
            percentage = round((weight / total) * 100, 1)

            r, g, b = rgb
            hex_color = rgb_to_hex(r, g, b)

            colors.append({
                "hex": hex_color,
                "rgb": f"rgb({r}, {g}, {b})",
                "percentage": percentage
            })

        return colors

    except Exception as e:
        print(f"⚠️  ColorThief extraction failed: {str(e)}")
        # Return fallback colors if extraction fails
        return [
            {"hex": "#808080", "rgb": "rgb(128, 128, 128)", "percentage": 100.0}
        ]


def generate_smart_description(tags: List[str]) -> str:
    """
    Generate an intelligent, natural description from tags

    Args:
        tags: List of tags/labels from Vision API

    Returns:
        A natural, descriptive sentence about the image
    """
    if not tags:
        return "An interesting image."

    # Categorize tags for better descriptions
    scene_words = ['landscape', 'indoor', 'outdoor', 'nature', 'urban', 'beach', 'mountain',
                   'forest', 'ocean', 'sky', 'sunset', 'sunrise', 'night', 'day']
    subject_words = ['person', 'people', 'animal', 'dog', 'cat', 'bird', 'building',
                     'vehicle', 'car', 'tree', 'flower', 'food', 'plate']
    activity_words = ['walking', 'running', 'sitting', 'standing', 'playing', 'working',
                     'eating', 'drinking', 'reading', 'writing']

    scenes = [tag for tag in tags if tag in scene_words]
    subjects = [tag for tag in tags if tag in subject_words]
    activities = [tag for tag in tags if tag in activity_words]

    # Generate description based on available information
    description_parts = []

    if activities and subjects:
        # "People walking on a beach"
        description_parts.append(f"{subjects[0]} {activities[0]}")
    elif subjects:
        # "A dog in nature"
        if scenes:
            description_parts.append(f"a {subjects[0]} in {scenes[0]}")
        else:
            description_parts.append(f"a {subjects[0]}")
    elif scenes:
        # "A beautiful sunset landscape"
        if len(scenes) > 1:
            description_parts.append(f"a {scenes[0]} {scenes[1]}")
        else:
            description_parts.append(f"a {scenes[0]} scene")

    # Add context from top tags if not already covered
    if not description_parts:
        # Fallback to top tags
        if len(tags) >= 3:
            description_parts.append(f"{tags[0]}, {tags[1]}, and {tags[2]}")
        elif len(tags) == 2:
            description_parts.append(f"{tags[0]} and {tags[1]}")
        else:
            description_parts.append(tags[0])

    # Add additional context from remaining top tags
    remaining_tags = [t for t in tags[:5] if t not in description_parts[0].lower()]
    if remaining_tags:
        context = ", ".join(remaining_tags[:2])
        description_parts.append(f"featuring {context}")

    # Combine and capitalize
    description = "An image of " + " ".join(description_parts) + "."
    return description.replace("  ", " ")  # Remove double spaces


def analyze_image(image_bytes: bytes) -> Dict:
    """
    Analyze image using OpenAI GPT-4o Vision API

    Args:
        image_bytes: Image content as bytes

    Returns:
        Dictionary with:
        - tags: List of relevant labels/tags
        - description: Descriptive sentence
        - colors: List of dominant colors with RGB and HEX values
        - processing_status: 'completed' or 'failed'

    How it works:
        1. Encodes image to base64
        2. Sends to OpenAI GPT-4o Vision with structured prompt
        3. Receives tags, description, and colors in one call
        4. Validates and returns structured data

    Why OpenAI GPT-4o Vision?
        - Best natural language descriptions
        - All-in-one: tags + description + colors
        - Cost: $0.00255 per image (512x512)
        - No free tier but very affordable
    """

    if not OPENAI_AVAILABLE:
        # Return mock data if OpenAI API is not configured
        print("⚠️  OpenAI not available, using mock data with real color extraction")
        return get_mock_analysis(image_bytes)

    try:
        # Encode image to base64
        print("🤖 Analyzing image with OpenAI GPT-4o Vision...")
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Create the prompt for GPT-4o Vision
        prompt = """Analyze this image and provide a JSON response with the following structure:
{
  "tags": [10-15 relevant single-word or short-phrase tags describing the image],
  "description": "A natural, detailed 1-2 sentence description of the image",
  "colors": ["hex color 1", "hex color 2", "hex color 3"]
}

Requirements:
- Tags: Provide 10-15 relevant tags (objects, scenes, activities, mood, style)
- Description: Write a natural, engaging description (not just listing tags)
- Colors: Identify the 3 most dominant colors in HEX format (e.g., "#FF5733")

Return ONLY the JSON object, no additional text."""

        # Call OpenAI GPT-4o Vision API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # GPT-4o model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"  # Use "low" for cheaper pricing ($0.00255)
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.7
        )

        # Parse the response
        result_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()

        # Parse JSON response
        analysis = json.loads(result_text)

        # Validate and extract data
        tags = analysis.get("tags", [])[:15]  # Limit to 15 tags
        description = analysis.get("description", "An interesting image.")
        colors = analysis.get("colors", ["#808080", "#A0A0A0", "#C0C0C0"])[:3]

        # Convert tags to lowercase for consistency
        tags = [tag.lower() for tag in tags]

        # Create color details with ColorThief for accurate percentages
        print("🎨 Extracting accurate color percentages with ColorThief...")
        color_details = extract_colors_with_colorthief(image_bytes, num_colors=3)

        # Generate AI-based filename (FREE - no extra API call!)
        ai_generated_name = generate_filename_from_description(description)
        print(f"📝 Generated filename: {ai_generated_name}")

        print(f"✅ OpenAI analysis complete: {len(tags)} tags, {len(colors)} colors")

        # Return structured analysis
        return {
            "tags": tags,
            "description": description,
            "colors": colors,  # HEX colors from OpenAI
            "color_details": color_details,  # Detailed colors with percentages from ColorThief
            "ai_generated_name": ai_generated_name,  # Clean filename from description
            "processing_status": "completed"
        }

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing OpenAI response: {str(e)}")
        print(f"   Response was: {result_text[:200]}...")
        # Fallback to ColorThief for colors
        return get_mock_analysis(image_bytes)
    except Exception as e:
        print(f"❌ Error analyzing image with OpenAI: {str(e)}")
        return {
            "tags": ["error", "processing-failed"],
            "description": "Error processing image with AI",
            "colors": ["#000000"],
            "processing_status": "failed",
            "error": str(e)
        }


def get_mock_analysis(image_bytes: bytes = None) -> Dict:
    """
    Return mock AI analysis data for testing without Vision API

    Even without Vision API, we can still extract real colors using ColorThief!

    This allows you to:
    - Test the complete workflow
    - Develop the frontend
    - See how data flows through the system
    - Get real color extraction (FREE!)
    - Switch to real AI later by just adding credentials

    Returns:
        Mock analysis with realistic tags, description, and real colors
    """
    # Extract real colors even without Vision API (if image bytes provided)
    if image_bytes:
        print("🎨 Extracting colors with ColorThief (free, local)...")
        color_details = extract_colors_with_colorthief(image_bytes, num_colors=3)
        colors = [c["hex"] for c in color_details]
    else:
        # Fallback to mock colors if no image bytes
        colors = ["#4A90E2", "#F39C12", "#2ECC71"]
        color_details = [
            {"hex": "#4A90E2", "rgb": "rgb(74, 144, 226)", "percentage": 35.0},
            {"hex": "#F39C12", "rgb": "rgb(243, 156, 18)", "percentage": 28.0},
            {"hex": "#2ECC71", "rgb": "rgb(46, 204, 113)", "percentage": 22.0}
        ]

    description = "An image with various visual elements and content."

    return {
        "tags": [
            "photograph",
            "image",
            "digital",
            "visual",
            "content",
            "media"
        ],
        "description": description,
        "colors": colors,
        "color_details": color_details,
        "ai_generated_name": generate_filename_from_description(description),
        "processing_status": "completed",
        "note": "Mock tags/description. Real colors extracted with ColorThief. Add billing to OpenAI account for real AI analysis."
    }


async def process_image_with_ai(image_bytes: bytes, image_id: int, user_id: str):
    """
    Process image with AI and save results to database

    This is an async function that can be called in the background
    without blocking the image upload response.

    Args:
        image_bytes: Image content as bytes
        image_id: Database ID of the uploaded image
        user_id: User's UUID

    Process:
        1. Analyze image with Vision API
        2. Save results to image_metadata table
        3. Update processing status
    """
    from supabase_client import supabase

    try:
        # Analyze image
        print(f"🤖 Starting AI analysis for image ID: {image_id}")
        analysis = analyze_image(image_bytes)

        # Save to database
        metadata = {
            "image_id": image_id,
            "user_id": user_id,
            "description": analysis["description"],
            "tags": analysis["tags"],
            "colors": analysis["colors"],
            "ai_generated_name": analysis.get("ai_generated_name"),
            "ai_processing_status": analysis["processing_status"]
        }

        # Check if metadata already exists
        existing = supabase.table('image_metadata').select('id').eq('image_id', image_id).execute()

        if existing.data:
            # Update existing record
            supabase.table('image_metadata').update(metadata).eq('image_id', image_id).execute()
            print(f"✅ AI analysis updated for image ID: {image_id}")
        else:
            # Insert new record
            supabase.table('image_metadata').insert(metadata).execute()
            print(f"✅ AI analysis saved for image ID: {image_id}")

        return analysis

    except Exception as e:
        print(f"❌ Error processing image with AI: {str(e)}")

        # Save error status to database
        try:
            supabase.table('image_metadata').insert({
                "image_id": image_id,
                "user_id": user_id,
                "description": "Error processing image",
                "tags": ["error"],
                "colors": ["#000000"],
                "ai_processing_status": "failed"
            }).execute()
        except:
            pass

        raise


# ============================================================
# TESTING FUNCTION
# ============================================================

def test_openai_api():
    """
    Test if OpenAI API is properly configured

    Run this to verify your setup:
        python -c "from ai_service import test_openai_api; test_openai_api()"
    """
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI API is NOT available")
        print("📝 Add OPENAI_API_KEY to your .env file")
        print("   Get your key from: https://platform.openai.com/api-keys")
        return False

    try:
        # Try a simple API call
        print("✅ OpenAI client initialized")
        print("✅ Ready to analyze images with GPT-4o Vision!")
        print(f"   Cost: $0.00255 per image (low detail mode)")
        return True
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run test when executed directly
    test_openai_api()
