#!/bin/bash
set -e

echo "Building DocTranslator for macOS..."

cd "$(dirname "$0")/.."

echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

echo "Creating standalone executable with PyInstaller..."
pyinstaller --onefile \
    --name DocTranslator \
    --add-data "translate_doc.py:." \
    --hidden-import openai \
    --hidden-import tiktoken \
    --hidden-import pymupdf \
    --hidden-import docx \
    --hidden-import openpyxl \
    --hidden-import pptx \
    --hidden-import markdown \
    --hidden-import bs4 \
    --hidden-import aiohttp \
    --hidden-import certifi \
    --clean \
    --noconfirm \
    app.py

echo "Build complete! Executable is at: dist/DocTranslator"
echo "Test with: ./dist/DocTranslator languages"