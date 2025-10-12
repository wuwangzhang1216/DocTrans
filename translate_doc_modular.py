"""
Document Translation Tool - Modular version using translator modules.

This is the main entry point that uses the refactored translator modules.
For better organization, the translation logic has been split into:
- translators/core.py - Core translation client and utilities
- translators/pdf_translator.py - PDF translation (100% identical to original)
- translators/pptx_translator.py - PowerPoint translation
- translators/docx_translator.py - Word translation
- translators/text_translator.py - Text and Markdown translation
- translators/document_translator.py - Main orchestrator
"""

import argparse
from pathlib import Path
from dotenv import load_dotenv
from translators import DocumentTranslator

# Load environment variables from .env file
load_dotenv()


# CLI interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate documents to different languages')
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-t', '--target', default='Chinese', help='Target language (default: Chinese)')
    parser.add_argument('-s', '--source', default='auto', help='Source language (default: auto)')
    parser.add_argument('-m', '--method', default='auto', help='Translation method (default: auto)')

    args = parser.parse_args()

    # Create translator
    translator = DocumentTranslator()

    # Translate document
    translator.translate_document(
        input_path=args.input,
        output_path=args.output,
        target_language=args.target,
        method=args.method
    )

    print(f"Translation completed. Output saved to: {args.output or 'default location'}")
