"""
Main document translator orchestrator.
Routes documents to appropriate translators based on file type.
"""

from typing import Optional, List, Dict
from pathlib import Path

from .core import TranslationClient
from .pdf_translator import PDFTranslator
from .pptx_translator import PPTXTranslator
from .docx_translator import DOCXTranslator
from .text_translator import TextTranslator


class DocumentTranslator:
    """
    Main document translator that routes to appropriate specialized translators.
    Supports PDF, PPTX, DOCX, TXT, and Markdown files.
    """

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "gemini-2.0-flash-lite",
                 max_workers: int = 256):
        """
        Initialize the document translator.

        Args:
            api_key: Google API key (optional, will use GEMINI_API_KEY env var if not provided)
            model: Gemini model to use for translation
            max_workers: Maximum total number of parallel workers
        """
        # Initialize core translation client
        self.translation_client = TranslationClient(api_key, model, max_workers)

        # Initialize specialized translators
        self.pdf_translator = PDFTranslator(self.translation_client)
        self.pptx_translator = PPTXTranslator(self.translation_client)
        self.docx_translator = DOCXTranslator(self.translation_client)
        self.text_translator = TextTranslator(self.translation_client)

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
        return self.translation_client.translate_text(text, target_language, source_language)

    def translate_document(self, input_path: str, output_path: Optional[str] = None,
                          target_language: str = "Spanish", method: str = "auto", progress_callback=None) -> bool:
        """
        Main method to translate any supported document format.

        Args:
            input_path: Path to input document
            output_path: Path to save translated document (optional)
            target_language: Target language for translation
            method: PDF translation method - "overlay", "redaction", or "auto"
            progress_callback: Optional callback function(progress: float) for progress updates (0.0 to 1.0)

        Returns:
            Success status
        """
        # Determine file type
        file_ext = Path(input_path).suffix.lower()

        # Generate output path if not provided
        if not output_path:
            base = Path(input_path).stem
            dir_path = Path(input_path).parent
            output_path = str(dir_path / f"{base}_translated_{target_language}{file_ext}")

        # Route to appropriate translator
        if file_ext == '.pptx':
            return self.pptx_translator.translate(input_path, output_path, target_language, progress_callback)
        elif file_ext == '.pdf':
            # Choose PDF translation method
            if method == "overlay":
                return self.pdf_translator.translate_with_overlay(input_path, output_path, target_language, progress_callback)
            elif method == "redaction":
                return self.pdf_translator.translate_with_redaction(input_path, output_path, target_language, progress_callback)
            else:  # auto
                return self.pdf_translator.translate_hybrid(input_path, output_path, target_language, progress_callback)
        elif file_ext == '.docx':
            return self.docx_translator.translate(input_path, output_path, target_language, progress_callback)
        elif file_ext in ['.txt', '.text']:
            return self.text_translator.translate_txt(input_path, output_path, target_language, progress_callback)
        elif file_ext in ['.md', '.markdown']:
            return self.text_translator.translate_markdown(input_path, output_path, target_language, progress_callback)
        else:
            print(f"Unsupported file format: {file_ext}")
            return False

    def batch_translate(self, input_folder: str, output_folder: str,
                       target_language: str, file_types: Optional[List[str]] = None) -> Dict:
        """
        Translate multiple documents in a folder.

        Args:
            input_folder: Path to folder containing documents
            output_folder: Path to save translated documents
            target_language: Target language for translation
            file_types: List of file extensions to process (default: all supported)

        Returns:
            Dictionary with translation results
        """
        if file_types is None:
            file_types = ['.pptx', '.pdf', '.docx', '.txt', '.md', '.markdown']

        # Create output folder if it doesn't exist
        Path(output_folder).mkdir(parents=True, exist_ok=True)

        results = {'success': [], 'failed': []}

        # Process each file
        for file_path in Path(input_folder).iterdir():
            if file_path.suffix.lower() in file_types:
                print(f"\n[FILE] Processing: {file_path.name}")
                output_path = str(Path(output_folder) / f"{file_path.stem}_translated{file_path.suffix}")

                if self.translate_document(str(file_path), output_path, target_language):
                    results['success'].append(file_path.name)
                else:
                    results['failed'].append(file_path.name)

        # Print summary
        print("\n" + "="*50)
        print("Translation Summary:")
        print(f"[SUCCESS] Successfully translated: {len(results['success'])} files")
        if results['failed']:
            print(f"[FAILED] Failed: {len(results['failed'])} files")
            for file in results['failed']:
                print(f"  - {file}")

        return results
