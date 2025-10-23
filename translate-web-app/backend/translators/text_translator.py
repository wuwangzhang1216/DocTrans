"""
Plain text and Markdown translation module.
Preserves code blocks, links, and formatting in Markdown files.
"""

import os
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from google import genai

from .core import TranslationClient


class TextTranslator:
    """
    Translator for plain text and Markdown files.
    """

    def __init__(self, translation_client: TranslationClient):
        """
        Initialize text translator.

        Args:
            translation_client: Core translation client instance
        """
        self.client = translation_client

    def _translate_text_block(self, block_data: tuple) -> dict:
        """
        Translate a single text block.

        Args:
            block_data: Tuple containing (block_index, block_text, target_language, api_key, model)

        Returns:
            Dictionary with translated content
        """
        block_idx, block_text, target_language, api_key, model = block_data

        try:
            if api_key:
                os.environ['GEMINI_API_KEY'] = api_key
            genai_client = genai.Client()

            prompt = (
                f"You are a professional technical translator. Translate into {target_language} with precise domain terminology and preserve formatting exactly.\n\n"
                f"Translate to {target_language} with native, accurate, technical wording.\n"
                "Strictly preserve original formatting and layout: line breaks, indentation, spacing, bullet/numbered lists (markers and levels), tables, and code blocks.\n"
                "Do not add explanations. Do not change capitalization of proper nouns.\n"
                "Do not translate code, CLI commands, file paths, API names, or placeholders like {var}, <tag>, {{braces}}, [1], %s, or ${VAR}.\n"
                "Keep URLs and IDs unchanged.\n\n"
                "Text to translate:\n"
                f"{block_text}"
            )

            response = genai_client.models.generate_content(
                model=model,
                contents=prompt
            )

            return {'block_idx': block_idx, 'translated_text': response.text.strip()}

        except Exception as e:
            print(f"Translation error on block {block_idx}: {str(e)}")
            return {'block_idx': block_idx, 'translated_text': block_text, 'error': str(e)}

    def translate_txt(self, input_path: str, output_path: str,
                     target_language: str, progress_callback=None) -> bool:
        """
        Translate plain text file.

        Args:
            input_path: Path to input text file
            output_path: Path to save translated text file
            target_language: Target language for translation
            progress_callback: Optional callback function(progress: float) for progress updates (0.0 to 1.0)

        Returns:
            Success status
        """
        try:
            if progress_callback:
                progress_callback(0.1)

            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()

            if progress_callback:
                progress_callback(0.3)

            translated = self.client.translate_text(text, target_language)

            if progress_callback:
                progress_callback(0.8)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated)

            if progress_callback:
                progress_callback(1.0)

            print(f"[SUCCESS] Translated TXT saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error translating TXT: {str(e)}")
            return False

    def translate_markdown(self, input_path: str, output_path: str,
                          target_language: str, progress_callback=None) -> bool:
        """
        Translate Markdown file while preserving formatting, code blocks, and links.

        Args:
            input_path: Path to input Markdown file
            output_path: Path to save translated Markdown file
            target_language: Target language for translation
            progress_callback: Optional callback function(progress: float) for progress updates (0.0 to 1.0)

        Returns:
            Success status
        """
        try:
            if progress_callback:
                progress_callback(0.05)

            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split content into blocks
            lines = content.split('\n')
            blocks = []
            current_block = []
            in_code_block = False

            for line in lines:
                stripped = line.strip()
                is_fence = stripped.startswith('```') or stripped.startswith('~~~')

                if is_fence:
                    if not in_code_block:
                        if current_block:
                            blocks.append(('text', '\n'.join(current_block)))
                            current_block = []
                        in_code_block = True
                        current_block = [line]
                    else:
                        current_block.append(line)
                        blocks.append(('code', '\n'.join(current_block)))
                        current_block = []
                        in_code_block = False
                elif in_code_block:
                    current_block.append(line)
                else:
                    current_block.append(line)

            if current_block:
                block_type = 'code' if in_code_block else 'text'
                blocks.append((block_type, '\n'.join(current_block)))

            # Prepare text blocks for translation
            text_blocks_to_translate = []
            # Use API key from the translation client
            api_key = self.client.api_key if hasattr(self.client, 'api_key') and self.client.api_key else os.environ.get('GEMINI_API_KEY', None)

            for idx, (block_type, block_content) in enumerate(blocks):
                if block_type == 'text' and block_content.strip():
                    text_blocks_to_translate.append((
                        idx,
                        block_content,
                        target_language,
                        api_key,
                        self.client.model
                    ))

            # Use maximum parallelism for translation
            max_workers = min(self.client.max_workers, len(text_blocks_to_translate))

            print(f"Processing Markdown with maximum parallelism:")
            print(f"  - Total blocks: {len(blocks)}")
            print(f"  - Text blocks to translate: {len(text_blocks_to_translate)}")
            print(f"  - Concurrent workers: {max_workers}")

            if progress_callback:
                progress_callback(0.1)

            # Translate in parallel
            translated_blocks = {}
            completed_blocks = 0
            total_blocks = len(text_blocks_to_translate)
            if text_blocks_to_translate:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_block = {
                        executor.submit(self._translate_text_block, block_data): block_data[0]
                        for block_data in text_blocks_to_translate
                    }

                    for future in concurrent.futures.as_completed(future_to_block):
                        block_idx = future_to_block[future]
                        try:
                            result = future.result()
                            if 'error' not in result:
                                translated_blocks[block_idx] = result['translated_text']
                            completed_blocks += 1
                            # Report progress from 10% to 80%
                            if progress_callback and total_blocks > 0:
                                progress = 0.1 + (completed_blocks / total_blocks) * 0.7
                                progress_callback(progress)
                        except Exception as e:
                            print(f"Block {block_idx} translation failed: {str(e)}")
                            completed_blocks += 1
                            if progress_callback and total_blocks > 0:
                                progress = 0.1 + (completed_blocks / total_blocks) * 0.7
                                progress_callback(progress)

            # Reconstruct markdown
            translated_content_parts = []
            for idx, (block_type, block_content) in enumerate(blocks):
                if block_type == 'code':
                    translated_content_parts.append(block_content)
                elif idx in translated_blocks:
                    translated_content_parts.append(translated_blocks[idx])
                else:
                    translated_content_parts.append(block_content)

            translated_content = '\n'.join(translated_content_parts)

            if progress_callback:
                progress_callback(0.9)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)

            if progress_callback:
                progress_callback(1.0)

            print(f"[SUCCESS] Translated Markdown saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error translating Markdown: {str(e)}")
            return False
