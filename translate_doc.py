import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import openai
from openai import OpenAI
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import threading

# Document processing libraries
from pptx import Presentation
from pptx.util import Inches, Pt
import PyPDF2
from docx import Document
import pdfplumber

class DocumentTranslator:
    """
    A comprehensive document translator that handles multiple file formats
    and translates content using OpenAI API with parallel processing support.

    Features:
    - Supports PDF, PPTX, DOCX, and TXT file formats
    - Parallel processing for improved performance on multi-page/multi-slide documents
    - Thread-safe implementation using separate OpenAI client instances
    - Configurable number of parallel workers
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini", max_workers: int = 16):
        """
        Initialize the translator with OpenAI API credentials.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use for translation (default: gpt-4.1-mini)
            max_workers: Maximum number of parallel workers for processing (default: 16
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_workers = max_workers
        
    def translate_text(self, text: str, target_language: str, 
                      source_language: str = "auto") -> str:
        """
        Translate text using OpenAI API.
        
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
                f"Translate to {target_language} with native, accurate, technical wording.\n"
                "Strictly preserve original formatting and layout: line breaks, indentation, spacing, bullet/numbered lists (markers and levels), tables, and code blocks.\n"
                "Do not add explanations. Do not change capitalization of proper nouns.\n"
                "Do not translate code, CLI commands, file paths, API names, or placeholders like {var}, <tag>, {{braces}}, [1], %s, or ${VAR}.\n"
                "Keep URLs and IDs unchanged.\n\n"
                "Text to translate:\n"
                f"{text}"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a professional technical translator. Translate into {target_language} with precise domain terminology and preserve formatting exactly."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=4000,
            )

            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text
    
    def translate_slide_content(self, slide_data: tuple) -> dict:
        """
        Translate content of a single slide. Helper method for parallel processing.

        Args:
            slide_data: Tuple containing (slide_index, slide_content, target_language, api_key, model)

        Returns:
            Dictionary with translated content for the slide
        """
        slide_idx, shapes_data, target_language, api_key, model = slide_data

        try:
            # Create a new client instance for thread safety
            client = OpenAI(api_key=api_key)
            translated_shapes = []

            def translate_runs_with_context(runs: List[str]) -> List[str]:
                if not runs:
                    return runs
                user_prompt = (
                    "Translate the following paragraph into "
                    f"{target_language} with native, accurate technical language.\n"
                    "Rules:\n"
                    "- Consider all runs together for context, but return the translation per run.\n"
                    "- Keep the number of runs identical and in the same order.\n"
                    "- Do not merge or split runs; do not drop whitespace.\n"
                    "- Preserve placeholders, code, variables, URLs, IDs unchanged.\n"
                    "- Output ONLY a JSON array of strings of the same length; no backticks, no extra text.\n\n"
                    f"Runs: {json.dumps(runs, ensure_ascii=False)}"
                )

                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a professional technical translator. Translate into {target_language} precisely and preserve formatting."
                            ),
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                    max_completion_tokens=4000,
                )
                content = resp.choices[0].message.content.strip()
                try:
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) == len(runs) and all(isinstance(x, str) for x in data):
                        return data
                except Exception:
                    pass
                return runs

            for shape_idx, shape_info in enumerate(shapes_data):
                shape_type, content = shape_info

                if shape_type == 'text':
                    if content and content.strip():
                        prompt = (
                            f"Translate to {target_language} with native, accurate, technical wording.\n"
                            "Strictly preserve original line breaks, indentation, and list markers.\n"
                            "Only return the translated text.\n\n"
                            f"Text to translate:\n{content}"
                        )

                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        f"You are a professional technical translator. Translate into {target_language} and preserve formatting."
                                    ),
                                },
                                {"role": "user", "content": prompt},
                            ],
                            max_completion_tokens=4000,
                        )
                        translated_shapes.append((shape_idx, response.choices[0].message.content.strip()))
                    else:
                        translated_shapes.append((shape_idx, content))

                elif shape_type == 'table':
                    # content is nested: rows -> cells -> paragraphs -> runs
                    translated_table = []
                    for row_idx, row_cells in enumerate(content):
                        translated_row_cells = []
                        for cell_idx, cell_paragraphs in enumerate(row_cells):
                            translated_cell_paragraphs = []
                            for para_idx, runs in enumerate(cell_paragraphs):
                                if runs and any(r.strip() for r in runs):
                                    translated_runs = translate_runs_with_context(runs)
                                else:
                                    translated_runs = runs
                                translated_cell_paragraphs.append(translated_runs)
                            translated_row_cells.append(translated_cell_paragraphs)
                        translated_table.append(translated_row_cells)
                    translated_shapes.append((shape_idx, translated_table))

                elif shape_type == 'paragraphs':
                    translated_paragraphs = []
                    for para_idx, runs_data in enumerate(content):
                        translated_runs = translate_runs_with_context(runs_data)
                        translated_paragraphs.append((
                            para_idx,
                            [(i, t) for i, t in enumerate(translated_runs)]
                        ))
                    translated_shapes.append((shape_idx, translated_paragraphs))

            return {'slide_idx': slide_idx, 'translated_shapes': translated_shapes}

        except Exception as e:
            print(f"Translation error on slide {slide_idx + 1}: {str(e)}")
            return {'slide_idx': slide_idx, 'error': str(e)}

    def translate_pptx(self, input_path: str, output_path: str,
                      target_language: str) -> bool:
        """
        Translate PowerPoint presentation.

        Args:
            input_path: Path to input PPTX file
            output_path: Path to save translated PPTX file
            target_language: Target language for translation

        Returns:
            Success status
        """
        try:
            prs = Presentation(input_path)

            # Extract content from all slides for parallel processing
            slides_data = []
            for slide_idx, slide in enumerate(prs.slides):
                shapes_data = []

                for shape_idx, shape in enumerate(slide.shapes):
                    # Handle tables first, then text frames to preserve bullets/styles
                    if shape.has_table:
                        table_data = []  # rows -> cells -> paragraphs -> runs
                        table = shape.table
                        for row in table.rows:
                            row_cells = []
                            for cell in row.cells:
                                cell_paragraphs = []
                                try:
                                    paragraphs = list(cell.text_frame.paragraphs)
                                except Exception:
                                    paragraphs = []
                                for paragraph in paragraphs:
                                    runs_data = [run.text for run in paragraph.runs]
                                    cell_paragraphs.append(runs_data)
                                row_cells.append(cell_paragraphs)
                            table_data.append(row_cells)
                        shapes_data.append(('table', table_data))
                    elif shape.has_text_frame:
                        paragraphs_data = []
                        for paragraph in shape.text_frame.paragraphs:
                            runs_data = [run.text for run in paragraph.runs]
                            paragraphs_data.append(runs_data)
                        shapes_data.append(('paragraphs', paragraphs_data))
                    elif hasattr(shape, "text") and shape.text:
                        # Fallback for shapes exposing only plain text
                        shapes_data.append(('text', shape.text))
                    else:
                        shapes_data.append(('empty', None))

                if shapes_data:  # Only process slides that have content
                    slides_data.append((slide_idx, shapes_data, target_language, self.client.api_key, self.model))

            if not slides_data:
                print("No text content found in PPTX")
                prs.save(output_path)
                return True

            print(f"Processing {len(slides_data)} slides with text content using {min(self.max_workers, len(slides_data))} parallel workers...")

            # Process slides in parallel
            translated_results = {}
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(slides_data))) as executor:
                future_to_slide = {
                    executor.submit(self.translate_slide_content, slide_data): slide_data[0]
                    for slide_data in slides_data
                }

                for future in concurrent.futures.as_completed(future_to_slide):
                    slide_idx = future_to_slide[future]
                    try:
                        result = future.result()
                        if 'error' not in result:
                            translated_results[slide_idx] = result['translated_shapes']
                    except Exception as e:
                        print(f"Slide {slide_idx + 1} translation failed: {str(e)}")

            # Apply translations back to the presentation
            for slide_idx, slide in enumerate(prs.slides):
                if slide_idx in translated_results:
                    shape_translations = translated_results[slide_idx]
                    shape_translations.sort(key=lambda x: x[0])  # Sort by shape index

                    for shape_trans_idx, (shape_idx, translated_content) in enumerate(shape_translations):
                        if shape_idx < len(list(slide.shapes)):
                            shape = list(slide.shapes)[shape_idx]

                            # Prefer text_frame updates (preserves bullets and run formatting)
                            if shape.has_text_frame and isinstance(translated_content, list):
                                for para_trans in translated_content:
                                    if isinstance(para_trans, tuple) and len(para_trans) == 2:
                                        para_idx, translated_runs = para_trans
                                        if para_idx < len(list(shape.text_frame.paragraphs)):
                                            paragraph = list(shape.text_frame.paragraphs)[para_idx]
                                            for run_trans in translated_runs:
                                                if isinstance(run_trans, tuple) and len(run_trans) == 2:
                                                    run_idx, run_text = run_trans
                                                    if run_idx < len(list(paragraph.runs)):
                                                        list(paragraph.runs)[run_idx].text = run_text
                            elif shape.has_table and isinstance(translated_content, list):
                                # Apply nested table translations: rows -> cells -> paragraphs -> runs
                                table = shape.table
                                for row_idx, row_cells in enumerate(translated_content):
                                    if row_idx < len(list(table.rows)):
                                        row = list(table.rows)[row_idx]
                                        for cell_idx, cell_paragraphs in enumerate(row_cells):
                                            if cell_idx < len(list(row.cells)):
                                                cell = list(row.cells)[cell_idx]
                                                for para_idx, translated_runs in enumerate(cell_paragraphs):
                                                    if para_idx < len(list(cell.text_frame.paragraphs)):
                                                        paragraph = list(cell.text_frame.paragraphs)[para_idx]
                                                        for run_idx, run_text in enumerate(translated_runs):
                                                            if run_idx < len(list(paragraph.runs)):
                                                                list(paragraph.runs)[run_idx].text = run_text
                            elif hasattr(shape, "text") and isinstance(translated_content, str):
                                shape.text = translated_content

            # Save translated presentation
            prs.save(output_path)
            print(f"✓ Translated PPTX saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error translating PPTX: {str(e)}")
            return False
    
    def translate_pdf_page(self, page_data: tuple) -> str:
        """
        Translate a single PDF page. Helper method for parallel processing.

        Args:
            page_data: Tuple containing (page_number, page_text, target_language, api_key, model)

        Returns:
            Formatted translated page text
        """
        page_num, text, target_language, api_key, model = page_data

        if not text or not text.strip():
            return f"=== Page {page_num} ===\n\n"

        try:
            # Create a new client instance for thread safety
            client = OpenAI(api_key=api_key)

            prompt = (
                f"Translate to {target_language} with native, accurate, technical wording.\n"
                "Strictly preserve original layout: line breaks, indentation, spacing, bullet/numbered lists (markers and levels), tables (as text), and code blocks.\n"
                "Do not add explanations. Do not translate code, paths, or placeholders like {var}, <tag>, [1].\n\n"
                f"Text to translate:\n{text}"
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional technical translator. Translate into {target_language} precisely and preserve formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=4000
            )

            translated = response.choices[0].message.content.strip()
            return f"=== Page {page_num} ===\n{translated}\n"

        except Exception as e:
            print(f"Translation error on page {page_num}: {str(e)}")
            return f"=== Page {page_num} ===\n[Translation failed: {text}]\n"

    def translate_pdf(self, input_path: str, output_path: str,
                     target_language: str) -> bool:
        """
        Translate PDF document (creates a text file with translations).
        Note: PDFs are read-only, so we output translated text to a .txt file.

        Args:
            input_path: Path to input PDF file
            output_path: Path to save translated text file
            target_language: Target language for translation

        Returns:
            Success status
        """
        try:
            # Extract text from all pages first
            pages_data = []
            with pdfplumber.open(input_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_data.append((i, text, target_language, self.client.api_key, self.model))

            if not pages_data:
                print("No text found in PDF")
                return False

            print(f"Processing {len(pages_data)} pages with {min(self.max_workers, len(pages_data))} parallel workers...")

            # Process pages in parallel
            translated_pages = [None] * len(pages_data)
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(pages_data))) as executor:
                # Submit all translation tasks
                future_to_index = {
                    executor.submit(self.translate_pdf_page, page_data): idx
                    for idx, page_data in enumerate(pages_data)
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        translated_pages[idx] = future.result()
                    except Exception as e:
                        page_num = pages_data[idx][0]
                        translated_pages[idx] = f"=== Page {page_num} ===\n[Translation failed]\n"
                        print(f"Page {page_num} translation failed: {str(e)}")

            # Sort pages by page number to maintain order
            translated_pages.sort(key=lambda x: int(x.split('=== Page ')[1].split(' ===')[0]))

            # Save translated text
            output_txt = output_path.replace('.pdf', '_translated.txt')
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_pages))

            print(f"✓ Translated PDF text saved to: {output_txt}")
            print("Note: PDF structure cannot be preserved. Translation saved as text file.")
            return True

        except Exception as e:
            print(f"Error translating PDF: {str(e)}")
            return False
    
    def translate_paragraph_batch(self, batch_data: tuple) -> dict:
        """
        Translate a batch of paragraphs (run-aligned). Helper for parallel processing.

        Args:
            batch_data: Tuple containing (batch_index, paragraphs_runs_data, target_language, api_key, model)

        Returns:
            Dictionary with translated paragraphs for the batch
        """
        batch_idx, paragraphs_runs_data, target_language, api_key, model = batch_data

        try:
            client = OpenAI(api_key=api_key)
            results = []

            def translate_runs(runs: List[str]) -> List[str]:
                if not runs:
                    return runs
                prompt = (
                    f"Translate into {target_language} with native, accurate, technical wording.\n"
                    "Consider all runs together for context, but return the translation per run. Keep the same number of runs and order.\n"
                    "Do not merge or split runs; preserve whitespace.\n"
                    "Preserve placeholders, code, variables, URLs, and IDs unchanged.\n"
                    "Respond with ONLY a JSON array of strings of the same length.\n\n"
                    f"Runs: {json.dumps(runs, ensure_ascii=False)}"
                )
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a professional technical translator. Translate into {target_language} precisely and preserve formatting."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_completion_tokens=4000,
                )
                content = resp.choices[0].message.content.strip()
                try:
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) == len(runs) and all(isinstance(x, str) for x in data):
                        return data
                except Exception:
                    pass
                return runs

            for item in paragraphs_runs_data:
                para_idx, runs = item
                if runs and any(t.strip() for t in runs):
                    translated_runs = translate_runs(runs)
                else:
                    translated_runs = runs
                results.append((para_idx, [(i, t) for i, t in enumerate(translated_runs)]))

            return {"batch_idx": batch_idx, "translated_paragraphs": results}

        except Exception as e:
            print(f"Translation error in batch {batch_idx}: {str(e)}")
            return {"batch_idx": batch_idx, "error": str(e)}

    def translate_table_batch(self, batch_data: tuple) -> dict:
        """
        Translate a batch of table paragraph runs for DOCX.

        Args:
            batch_data: Tuple containing (batch_index, table_para_runs_data, target_language, api_key, model)

        Returns:
            Dictionary with translated table paragraphs for the batch
        """
        batch_idx, table_para_runs_data, target_language, api_key, model = batch_data

        try:
            client = OpenAI(api_key=api_key)
            results = []

            def translate_runs(runs: List[str]) -> List[str]:
                if not runs:
                    return runs
                prompt = (
                    f"Translate into {target_language} with native, accurate, technical wording.\n"
                    "Consider all runs together for context, but return the translation per run. Keep the same number of runs and order.\n"
                    "Do not merge or split runs; preserve whitespace.\n"
                    "Preserve placeholders, code, variables, URLs, and IDs unchanged.\n"
                    "Respond with ONLY a JSON array of strings of the same length.\n\n"
                    f"Runs: {json.dumps(runs, ensure_ascii=False)}"
                )
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a professional technical translator. Translate into {target_language} precisely and preserve formatting."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_completion_tokens=4000,
                )
                content = resp.choices[0].message.content.strip()
                try:
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) == len(runs) and all(isinstance(x, str) for x in data):
                        return data
                except Exception:
                    pass
                return runs

            for item in table_para_runs_data:
                key, runs = item  # key identifies (table_idx, row_idx, cell_idx, para_idx)
                if runs and any(t.strip() for t in runs):
                    translated_runs = translate_runs(runs)
                else:
                    translated_runs = runs
                results.append((key, [(i, t) for i, t in enumerate(translated_runs)]))

            return {"batch_idx": batch_idx, "translated_table_paragraphs": results}

        except Exception as e:
            print(f"Translation error in table batch {batch_idx}: {str(e)}")
            return {"batch_idx": batch_idx, "error": str(e)}

    def translate_docx(self, input_path: str, output_path: str,
                      target_language: str) -> bool:
        """
        Translate Word document.

        Args:
            input_path: Path to input DOCX file
            output_path: Path to save translated DOCX file
            target_language: Target language for translation

        Returns:
            Success status
        """
        try:
            doc = Document(input_path)

            # Gather paragraph runs for translation (document body)
            body_paragraphs = []  # list of (para_idx, [run_texts])
            for para_idx, paragraph in enumerate(doc.paragraphs):
                runs_texts = [r.text for r in paragraph.runs]
                body_paragraphs.append((para_idx, runs_texts))

            # Gather table cell paragraph runs for translation
            # Index by (table_idx, row_idx, cell_idx, para_idx)
            table_para_runs = []
            for table_idx, table in enumerate(doc.tables):
                for row_idx, row in enumerate(table.rows):
                    for cell_idx, cell in enumerate(row.cells):
                        for para_idx, paragraph in enumerate(cell.paragraphs):
                            runs_texts = [r.text for r in paragraph.runs]
                            table_para_runs.append(((table_idx, row_idx, cell_idx, para_idx), runs_texts))

            # Process body paragraphs in batches
            paragraph_batches = []
            if body_paragraphs:
                batch_size = max(1, len(body_paragraphs) // self.max_workers) if self.max_workers > 1 else len(body_paragraphs)
                for i in range(0, len(body_paragraphs), batch_size):
                    batch = body_paragraphs[i:i + batch_size]
                    paragraph_batches.append((len(paragraph_batches), batch, target_language, self.client.api_key, self.model))

            translated_body = {}
            if paragraph_batches:
                print(f"Processing {len(paragraph_batches)} paragraph batches with {min(self.max_workers, len(paragraph_batches))} parallel workers...")
                with ThreadPoolExecutor(max_workers=min(self.max_workers, len(paragraph_batches))) as executor:
                    future_to_batch = {
                        executor.submit(self.translate_paragraph_batch, batch): batch[0]
                        for batch in paragraph_batches
                    }

                    for future in concurrent.futures.as_completed(future_to_batch):
                        batch_idx = future_to_batch[future]
                        try:
                            result = future.result()
                            if 'error' not in result:
                                for para_idx, translated_runs in result['translated_paragraphs']:
                                    translated_body[para_idx] = translated_runs
                        except Exception as e:
                            print(f"Paragraph batch {batch_idx} translation failed: {str(e)}")

            # Process table paragraphs in batches
            table_batches = []
            if table_para_runs:
                batch_size = max(1, len(table_para_runs) // self.max_workers) if self.max_workers > 1 else len(table_para_runs)
                for i in range(0, len(table_para_runs), batch_size):
                    batch = table_para_runs[i:i + batch_size]
                    table_batches.append((len(table_batches), batch, target_language, self.client.api_key, self.model))

            translated_table = {}
            if table_batches:
                print(f"Processing {len(table_batches)} table batches with {min(self.max_workers, len(table_batches))} parallel workers...")
                with ThreadPoolExecutor(max_workers=min(self.max_workers, len(table_batches))) as executor:
                    future_to_batch = {
                        executor.submit(self.translate_table_batch, batch): batch[0]
                        for batch in table_batches
                    }

                    for future in concurrent.futures.as_completed(future_to_batch):
                        batch_idx = future_to_batch[future]
                        try:
                            result = future.result()
                            if 'error' not in result:
                                for key, translated_runs in result['translated_table_paragraphs']:
                                    translated_table[key] = translated_runs
                        except Exception as e:
                            print(f"Table batch {batch_idx} translation failed: {str(e)}")

            # Apply body paragraph translations (preserve run styles like underline/bold)
            for para_idx, paragraph in enumerate(doc.paragraphs):
                if para_idx in translated_body:
                    for run_idx, run_text in translated_body[para_idx]:
                        if run_idx < len(paragraph.runs):
                            paragraph.runs[run_idx].text = run_text

            # Apply table translations (preserve run styles)
            for table_idx, table in enumerate(doc.tables):
                for row_idx, row in enumerate(table.rows):
                    for cell_idx, cell in enumerate(row.cells):
                        for para_idx, paragraph in enumerate(cell.paragraphs):
                            key = (table_idx, row_idx, cell_idx, para_idx)
                            if key in translated_table:
                                for run_idx, run_text in translated_table[key]:
                                    if run_idx < len(paragraph.runs):
                                        paragraph.runs[run_idx].text = run_text

            # Save translated document
            doc.save(output_path)
            print(f"✓ Translated DOCX saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error translating DOCX: {str(e)}")
            return False
    
    def translate_txt(self, input_path: str, output_path: str, 
                     target_language: str) -> bool:
        """
        Translate plain text file.
        
        Args:
            input_path: Path to input text file
            output_path: Path to save translated text file
            target_language: Target language for translation
            
        Returns:
            Success status
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            translated = self.translate_text(text, target_language)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated)
            
            print(f"✓ Translated TXT saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error translating TXT: {str(e)}")
            return False
    
    def translate_document(self, input_path: str, output_path: Optional[str] = None,
                          target_language: str = "Spanish") -> bool:
        """
        Main method to translate any supported document format.
        
        Args:
            input_path: Path to input document
            output_path: Path to save translated document (optional)
            target_language: Target language for translation
            
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
            return self.translate_pptx(input_path, output_path, target_language)
        elif file_ext == '.pdf':
            return self.translate_pdf(input_path, output_path, target_language)
        elif file_ext == '.docx':
            return self.translate_docx(input_path, output_path, target_language)
        elif file_ext in ['.txt', '.text']:
            return self.translate_txt(input_path, output_path, target_language)
        else:
            print(f"Unsupported file format: {file_ext}")
            return False
    
    def batch_translate(self, input_folder: str, output_folder: str,
                       target_language: str, file_types: List[str] = None) -> Dict:
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
            file_types = ['.pptx', '.pdf', '.docx', '.txt']
        
        # Create output folder if it doesn't exist
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        results = {'success': [], 'failed': []}
        
        # Process each file
        for file_path in Path(input_folder).iterdir():
            if file_path.suffix.lower() in file_types:
                print(f"\nProcessing: {file_path.name}")
                output_path = str(Path(output_folder) / f"{file_path.stem}_translated{file_path.suffix}")
                
                if self.translate_document(str(file_path), output_path, target_language):
                    results['success'].append(file_path.name)
                else:
                    results['failed'].append(file_path.name)
        
        # Print summary
        print("\n" + "="*50)
        print("Translation Summary:")
        print(f"✓ Successfully translated: {len(results['success'])} files")
        if results['failed']:
            print(f"✗ Failed: {len(results['failed'])} files")
            for file in results['failed']:
                print(f"  - {file}")
        
        return results


# Example usage
if __name__ == "__main__":
    # Initialize translator with your OpenAI API key
    API_KEY = "you_api_key"  # Replace with your actual API key
    
    # Initialize translator with parallel processing (max_workers=32 for faster processing)
    translator = DocumentTranslator(api_key=API_KEY, max_workers=32)

    # Example 1: Translate a single PowerPoint presentation (uses parallel processing for slides)
    translator.translate_document(
        input_path="test.pptx",
        target_language="Chinese"
    )
    
    # # Example 2: Translate a PDF document (uses parallel processing for pages)
    # translator.translate_document(
    #     input_path="document.pdf",
    #     target_language="French"
    # )

    # # Example 3: Translate a Word document with custom output path (uses parallel processing for paragraphs)
    # translator.translate_document(
    #     input_path="report.docx",
    #     output_path="report_chinese.docx",
    #     target_language="Chinese"
    # )

    # # Example 4: Batch translate all documents in a folder (each file uses parallel processing)
    # translator.batch_translate(
    #     input_folder="documents/",
    #     output_folder="translated_documents/",
    #     target_language="Japanese",
    #     file_types=['.pptx', '.docx', '.pdf']
    # )
    
    # # Example 5: Translate with custom settings
    # # Use a different model for faster/cheaper translation
    # fast_translator = DocumentTranslator(api_key=API_KEY, model="gpt-3.5-turbo")
    # fast_translator.translate_document(
    #     input_path="quick_doc.txt",
    #     target_language="German"
    # )
