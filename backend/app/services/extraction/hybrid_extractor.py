"""
Hybrid extraction: unstructured.io for parsing + Gemini for structuring.
Falls back to this when LLM-only extraction has low confidence.
"""
import json
import os
from typing import Optional
from app.config import get_settings
from app.utils.prompts import HYBRID_FINANCIAL_RECORD_PROMPT

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


def parse_document_with_unstructured(file_path: str) -> str:
    """
    Parse a document using unstructured.io to extract text and table data.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Extracted text content as a string
    """
    try:
        from unstructured.partition.auto import partition
        
        elements = partition(filename=file_path)
        
        # Build structured text from elements
        text_parts = []
        for element in elements:
            element_type = type(element).__name__
            text = str(element)
            
            if element_type == "Table":
                text_parts.append(f"[TABLE]\n{text}\n[/TABLE]")
            elif element_type == "Title":
                text_parts.append(f"[TITLE] {text}")
            elif element_type == "NarrativeText":
                text_parts.append(text)
            elif element_type == "ListItem":
                text_parts.append(f"  • {text}")
            else:
                text_parts.append(text)
        
        return "\n".join(text_parts)
        
    except ImportError:
        raise RuntimeError(
            "unstructured package not installed. "
            "Install with: pip install 'unstructured[pdf]'"
        )
    except Exception as e:
        raise RuntimeError(f"Document parsing failed: {str(e)}")


async def extract_with_hybrid(file_path: str) -> dict:
    """
    Extract financial record data using hybrid approach:
    1. Parse document with unstructured.io
    2. Send parsed text to Gemini for classification, categorization, and structuring
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Extracted financial record data as a dictionary
    """
    # Step 1: Parse with unstructured
    extracted_text = parse_document_with_unstructured(file_path)
    
    if not extracted_text.strip():
        raise ValueError("No text could be extracted from the document")
    
    # Step 2: Structure with Gemini
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    category_list = _get_category_list()
    prompt = HYBRID_FINANCIAL_RECORD_PROMPT.format(
        extracted_text=extracted_text,
        categories=category_list,
    )
    
    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=4096,
        ),
    )
    
    # Parse the response
    response_text = response.text.strip()
    
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]
    
    try:
        extracted_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {str(e)}")
    
    # Add metadata
    extracted_data["extraction_method"] = "hybrid"
    extracted_data["raw_text"] = extracted_text
    
    return extracted_data
