"""
LLM-only extraction using Gemini 2.0 Flash with vision capabilities.
Sends the document image directly to the LLM for classification, categorization,
and structured extraction in a single call.
"""
import json
import os
from app.config import get_settings
from app.utils.prompts import FINANCIAL_RECORD_EXTRACTION_PROMPT

settings = get_settings()


def _get_category_list() -> str:
    """Build a formatted category list string for the prompt."""
    from app.models.enums import SEED_CATEGORIES, CategoryGroup
    lines = []
    for group, cats in SEED_CATEGORIES.items():
        group_label = group.value.title()
        for cat in cats:
            lines.append(f"- {cat['name']} ({group_label})")
    lines.append("- Uncategorized")
    return "\n".join(lines)


async def extract_with_llm(file_path: str) -> dict:
    """
    Extract financial record data using Gemini 2.0 Flash vision.
    
    Sends the document (PDF/image) directly to the LLM and gets
    structured JSON output with classification, categorization, and
    field extraction in one shot.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Extracted data as a dictionary
        
    Raises:
        Exception: If extraction fails
    """
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Read the file
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    # Determine MIME type
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")
    
    # Create the content parts
    file_part = types.Part.from_bytes(
        data=file_bytes,
        mime_type=mime_type,
    )
    
    # Build prompt with category list
    category_list = _get_category_list()
    prompt = FINANCIAL_RECORD_EXTRACTION_PROMPT.format(categories=category_list)
    
    # Send to Gemini
    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            types.Content(
                parts=[
                    file_part,
                    types.Part.from_text(text=prompt),
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for precise extraction
            max_output_tokens=4096,
        ),
    )
    
    # Parse the response
    response_text = response.text.strip()
    
    # Remove markdown code fences if present
    if response_text.startswith("```"):
        # Remove first line (```json or ```)
        response_text = response_text.split("\n", 1)[1]
        # Remove last ``` 
        response_text = response_text.rsplit("```", 1)[0]
    
    try:
        extracted_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {str(e)}\nResponse: {response_text[:500]}")
    
    # Add extraction method
    extracted_data["extraction_method"] = "llm_only"
    
    return extracted_data
