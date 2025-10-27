#!/usr/bin/env python3
"""
Ultra-simplified PDF Translator - Direct wrapper around pdf2zh with Gemini support
100% compatible with pdf2zh - just adds Gemini translator and convenience API
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path to import pdf2zh
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use pdf2zh's translate function directly (100% compatible)
from pdf2zh.high_level import translate
from pdf2zh.doclayout import OnnxModel, ModelInstance

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def translate_pdf(
    input_path: str,
    api_key: str,
    output_dir: Optional[str] = None,
    lang_in: str = "en",
    lang_out: str = "zh",
    model: str = "gemini-2.0-flash-lite",
    thread: int = 64,
    model_path: Optional[str] = None,
    **kwargs
) -> Tuple[str, str]:
    """
    Translate PDF using pdf2zh with Gemini API

    Args:
        input_path: Path to input PDF
        api_key: Gemini API key
        output_dir: Output directory (default: same as input)
        lang_in: Source language code
        lang_out: Target language code
        model: Gemini model name
        thread: Number of parallel workers (pdf2zh's thread parameter)
        model_path: Path to layout detection model
        **kwargs: Additional arguments passed to pdf2zh

    Returns:
        (mono_output_path, dual_output_path)
    """

    # Validate input
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"PDF not found: {input_path}")

    # Setup output directory
    if output_dir is None:
        output_dir = str(input_file.parent)
    else:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load layout model
    log.info("Loading DocLayout model...")
    if model_path:
        ModelInstance.value = OnnxModel(model_path)
    else:
        ModelInstance.value = OnnxModel.load_available()

    # Setup Gemini service string
    service = f"gemini:{model}" if model else "gemini"

    # Set environment variable for Gemini API key
    os.environ["GEMINI_API_KEY"] = api_key

    log.info(f"Translating PDF: {input_path}")
    log.info(f"  Service: {service}")
    log.info(f"  Language: {lang_in} → {lang_out}")
    log.info(f"  Workers: {thread}")

    # Call pdf2zh's translate function directly (100% compatible)
    result_files = translate(
        files=[input_path],
        output=output_dir,
        lang_in=lang_in,
        lang_out=lang_out,
        service=service,
        thread=thread,
        model=ModelInstance.value,
        envs={"GEMINI_API_KEY": api_key},
        skip_subset_fonts=True,  # Skip font subsetting to avoid PyMuPDF bug
        **kwargs
    )

    # Extract paths
    mono_path, dual_path = result_files[0]

    log.info(f"Translation complete!")
    log.info(f"  Mono: {mono_path}")
    log.info(f"  Dual: {dual_path}")

    return mono_path, dual_path


# ==================== Module Wrapper for Integration ====================

class PDFTranslator:
    """Wrapper class for modular architecture (compatible with existing code)"""

    def __init__(self, translation_client):
        self.client = translation_client

    def translate(
        self,
        input_path: str,
        output_path: str,
        target_language: str,
        model_path: Optional[str] = None,
        font_path: Optional[str] = None
    ) -> Tuple[str, str]:
        """Translate PDF using Gemini API"""

        # Get API key
        api_key = getattr(self.client, 'api_key', None) or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        # Get configuration
        model = getattr(self.client, 'model', 'gemini-2.0-flash-lite')
        # Use max_workers (total workers) instead of max_workers_per_page for maximum speed
        max_workers = getattr(self.client, 'max_workers', 256)

        # Get output directory
        output_dir = Path(output_path).parent if output_path else None

        return translate_pdf(
            input_path=input_path,
            api_key=api_key,
            output_dir=str(output_dir) if output_dir else None,
            lang_in="en",
            lang_out=target_language,
            model=model,
            thread=max_workers,  # pdf2zh's thread parameter - use full worker count for max speed
            model_path=model_path
        )

    def translate_with_overlay(self, input_path: str, output_path: str, target_language: str):
        """Returns tuple of (mono_path, dual_path) on success"""
        try:
            mono, dual = self.translate(input_path, output_path, target_language)
            print(f"[SUCCESS] Translated PDF saved to: {mono}")
            return (mono, dual)
        except Exception as e:
            print(f"Error: {e}")
            return False

    def translate_with_redaction(self, input_path: str, output_path: str, target_language: str):
        return self.translate_with_overlay(input_path, output_path, target_language)

    def translate_hybrid(self, input_path: str, output_path: str, target_language: str):
        return self.translate_with_overlay(input_path, output_path, target_language)


# ==================== Direct Execution with Local Variables ====================

if __name__ == "__main__":
    import sys

    # ==================== Configuration (Edit these variables) ====================

    # Input PDF file path
    input_pdf = "test.pdf"  # Change this to your PDF path

    # Output directory (None = same directory as input)
    output_directory = None

    # Gemini API key (or set GEMINI_API_KEY environment variable)
    api_key = os.environ.get("GEMINI_API_KEY")  # Set via environment variable
    # api_key = "your-api-key-here"  # Or uncomment and set directly

    # Source and target languages
    source_lang = "en"
    target_lang = "zh"

    # Gemini model
    gemini_model = "gemini-2.0-flash-lite"

    # Number of parallel workers (higher = faster, but more API calls)
    parallel_workers = 64

    # Custom layout detection model path (optional)
    custom_model_path = None  # Or set to your ONNX model path

    # ==================== End Configuration ====================

    # Validate API key
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required")
        print("Set it with: export GEMINI_API_KEY='your-api-key'")
        sys.exit(1)

    # Run translation
    try:
        print(f"\n🚀 Starting PDF translation...")
        print(f"   Input: {input_pdf}")
        print(f"   Language: {source_lang} → {target_lang}")
        print(f"   Model: {gemini_model}")
        print(f"   Workers: {parallel_workers}")
        print()

        mono, dual = translate_pdf(
            input_path=input_pdf,
            api_key=api_key,
            output_dir=output_directory,
            lang_in=source_lang,
            lang_out=target_lang,
            model=gemini_model,
            thread=parallel_workers,
            model_path=custom_model_path
        )

        print(f"\n✓ Translation complete!")
        print(f"  Mono: {mono}")
        print(f"  Dual: {dual}")
    except Exception as e:
        log.exception("Translation failed")
        sys.exit(1)
