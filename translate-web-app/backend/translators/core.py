"""
Core translation utilities and base client.
"""

import os
from typing import Optional
from google import genai
from dataclasses import dataclass


@dataclass
class TextBlock:
    """Data class to store text block information"""
    bbox: tuple  # (x0, y0, x1, y1)
    text: str
    font: str = None
    font_size: float = None
    flags: int = 0
    color: int = 0
    block_no: int = 0
    block_type: int = 0


class TranslationClient:
    """
    Core translation client for Google Generative AI.
    Handles basic translation operations and worker allocation.
    """

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "gemini-2.0-flash-lite",
                 max_workers: int = 256):
        """
        Initialize the translation client.

        Args:
            api_key: Google API key (optional, will use GEMINI_API_KEY env var if not provided)
            model: Gemini model to use for translation
            max_workers: Maximum total number of parallel workers
        """
        # Store API key for use in translators
        self.api_key = api_key

        # Set environment variable and initialize client
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
        self.client = genai.Client()
        self.model = model
        self.max_workers = max_workers
        self.max_concurrent_pages = 16
        self.max_workers_per_page = 64

    def calculate_workers_per_page(self, total_pages: int) -> tuple:
        """
        Calculate dynamic worker allocation based on total pages.

        Args:
            total_pages: Total number of pages to process

        Returns:
            Tuple of (workers_per_page, concurrent_pages)
        """
        concurrent_pages = min(total_pages, self.max_concurrent_pages)
        workers_per_page = min(
            self.max_workers_per_page,
            self.max_workers // concurrent_pages
        )
        return workers_per_page, concurrent_pages

    def translate_text(self, text: str, target_language: str,
                      source_language: str = "auto") -> str:
        """
        Translate text using Google Generative AI.

        Args:
            text: Text to translate
            target_language: Target language for translation
            source_language: Source language (default: auto-detect)

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        try:
            prompt = (
                f"You are a professional technical translator. Translate into {target_language} with precise domain terminology and preserve formatting exactly.\n\n"
                f"Translate to {target_language} with native, accurate, technical wording.\n"
                "Strictly preserve original formatting and layout: line breaks, indentation, spacing, bullet/numbered lists (markers and levels), tables, and code blocks.\n"
                "Do not add explanations. Do not change capitalization of proper nouns.\n"
                "Do not translate code, CLI commands, file paths, API names, or placeholders like {var}, <tag>, {{braces}}, [1], %s, or ${VAR}.\n"
                "Keep URLs and IDs unchanged.\n\n"
                "Text to translate:\n"
                f"{text}"
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            return response.text.strip()

        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text

    def int_to_rgb(self, color_int: int) -> tuple:
        """Convert integer color to RGB tuple."""
        if color_int == 0:
            return (0, 0, 0)
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return (r, g, b)
