# Document Translation Suite

A powerful document translation system powered by Google Gemini AI, with both CLI and Web Application support. Features dynamic parallel processing with up to 256 workers for high-performance translation.

## Features

### Core Features
- 📄 **Multiple Format Support**: PDF, DOCX, PPTX, TXT, Markdown
- 🌍 **Powered by Google Gemini**: Fast and accurate translation with gemini-2.0-flash-lite model
- ⚡ **High Performance**: Dynamic parallel processing with up to 256 workers
- 🧠 **Smart Allocation**: Up to 16 pages/slides concurrently, 64 workers per page
- 🔄 **Batch Processing**: Translate entire folders of documents
- 📊 **Format Preservation**: Maintains document structure, formatting, and layout
- 🎯 **Markdown Smart**: Detects and protects code blocks during translation

### Two Usage Modes
1. **CLI Tool** (`translate_doc.py`): Direct Python script for quick translations
2. **Web Application**: Full-featured web UI with Redis-backed job queue and real-time progress tracking

## Installation

### Prerequisites
- Python 3.9+
- Node.js 18+ (for web application)
- Google Gemini API Key (get it from [https://ai.google.dev/](https://ai.google.dev/))

### 1. Clone the Repository
```bash
git clone https://github.com/wuwangzhang1216/translate-doc.git
cd translate-doc
```

### 2. Set Up Environment Variables

Copy the example file and configure:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=rediss://your_redis_url  # Only needed for web app
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `google-genai` - Google Gemini AI SDK
- `pymupdf` - Advanced PDF processing
- `python-pptx`, `python-docx` - Office document support
- `reportlab` - PDF generation
- Other supporting libraries

### Installation Options

The install script supports several options:

```bash
# Force rebuild the executable even if it exists
./install.sh --build
./install.sh -b

# Skip build and only install existing executable
./install.sh --skip-build
./install.sh -s

# Show help and available options
./install.sh --help
./install.sh -h
```

**Note**: The installer automatically handles common conflicts like the obsolete `pathlib` package that can interfere with PyInstaller builds.

### System Requirements

- **macOS**: 10.15 or later
- **OpenRouter API Key**: Required for translation services (supports multiple AI models)

## Configuration

### Setting up your API Key

You have three options to provide your OpenRouter API key:

1. **Using the config command** (Recommended):
```bash
doctrans config --set-key sk-your-api-key-here
```

2. **Environment variable**:
```bash
export OPENROUTER_API_KEY="sk-or-your-api-key-here"
# Or use OPENAI_API_KEY for compatibility
export OPENAI_API_KEY="sk-or-your-api-key-here"
```

3. **Command-line flag**:
```bash
doctrans translate document.pdf -l Spanish --api-key sk-your-api-key-here
```

## Usage

### Basic Commands

```bash
# Show help
doctrans --help

# List all supported languages
doctrans languages

# Translate a single document
doctrans translate document.pdf -l Chinese

# Translate with custom output name
doctrans translate report.docx -l French -o rapport_francais.docx

# Batch translate a folder
doctrans batch ./documents ./translated -l Spanish

# Batch translate specific file types only
doctrans batch ./input ./output -l German --types "pdf,docx"
```

### Supported Languages

Use either the language code or full name:

| Code | Language    | Code | Language    | Code | Language    |
|------|------------|------|------------|------|------------|
| en   | English    | ko   | Korean     | sv   | Swedish    |
| es   | Spanish    | zh   | Chinese    | pl   | Polish     |
| fr   | French     | ar   | Arabic     | tr   | Turkish    |
| de   | German     | hi   | Hindi      | he   | Hebrew     |
| it   | Italian    | nl   | Dutch      | no   | Norwegian  |
| pt   | Portuguese | da   | Danish     | th   | Thai       |
| ru   | Russian    | fi   | Finnish    | vi   | Vietnamese |
| ja   | Japanese   | cs   | Czech      | id   | Indonesian |

Run `doctrans languages` for the complete list.

### Examples

#### Translate a PDF to Chinese
```bash
doctrans translate research_paper.pdf -l zh
# Output: research_paper_zh.pdf
```

#### Batch translate Word documents to Spanish
```bash
doctrans batch ./english_docs ./spanish_docs -l Spanish --types docx
```

#### Translate a presentation with custom output
```bash
doctrans translate presentation.pptx -l Japanese -o プレゼンテーション.pptx
```

#### Process markdown files
```bash
doctrans translate README.md -l French -o LISEZ-MOI.md
```

## Advanced Options

### Global Flags

- `--api-key KEY`: Override the configured API key
- `-v, --verbose`: Enable detailed output
- `-q, --quiet`: Suppress non-error output

### Translate Command Options

- `-l, --language`: Target language (required)
- `-o, --output`: Custom output file path
- `--model`: AI model to use (default: google/gemini-2.0-flash-lite)
- `--preserve-formatting`: Maintain original formatting

### Batch Command Options

- `-l, --language`: Target language (required)
- `-t, --types`: File types to process (comma-separated)
- `--skip-existing`: Skip already translated files
- `--parallel`: Number of parallel translations

## File Format Support

| Format | Extension | Description |
|--------|-----------|-------------|
| PDF | .pdf | Full text extraction and translation |
| Word | .docx | Preserves formatting, styles, and layout |
| PowerPoint | .pptx | Translates slides while maintaining design |
| Excel | .xlsx | Translates cell contents, preserves formulas |
| Text | .txt | Plain text translation |
| Markdown | .md | Preserves markdown formatting |
| HTML | .html | Maintains HTML structure |

## Troubleshooting

### Command not found

If you get "command not found" after installation:

1. Ensure the installation completed successfully
2. Restart your terminal
3. Or manually add to PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### API Key Issues

If you get API key errors:

1. Verify your key is correct:
```bash
doctrans config --show-key
```

2. Ensure it starts with `sk-`
3. Check your OpenRouter account has credits

### Permission Denied

If you get permission errors:
```bash
chmod +x ~/.local/bin/doctrans
```

## Uninstallation

### Complete Uninstallation

To completely remove DocTrans CLI and all associated files:

```bash
chmod +x uninstall.sh
./uninstall.sh --clean-all
```

This will remove:
- The `doctrans` command from `~/.local/bin/`
- All build artifacts (`build/` and `dist/` directories)
- PyInstaller spec files
- Python cache directories (`__pycache__`)
- PATH modifications from shell config files (with backups)

### Uninstallation Options

The uninstall script supports several options:

```bash
# Basic uninstall (removes only the doctrans command)
./uninstall.sh

# Remove PATH modifications from shell configs
./uninstall.sh --clean-path

# Complete cleanup - removes everything
./uninstall.sh --clean-all
./uninstall.sh -a

# Show help and available options
./uninstall.sh --help
./uninstall.sh -h
```

### What Gets Removed

| Option | doctrans command | build/dist folders | PATH configs | Python caches |
|--------|-----------------|-------------------|--------------|---------------|
| Basic | ✓ | ✗ | ✗ | ✗ |
| --clean-path | ✓ | ✗ | ✓ | ✗ |
| --clean-all | ✓ | ✓ | ✓ | ✓ |

**Note**: When removing PATH modifications, the script creates timestamped backups of your shell config files before making changes.

### Manual Uninstallation

If you prefer to uninstall manually:
```bash
# Remove the CLI command
rm ~/.local/bin/doctrans

# Remove config directory
rm -rf ~/.doctranslator

# Remove build artifacts
rm -rf build/ dist/ DocTranslator.spec

# Remove PATH modification from shell config
# Edit ~/.bash_profile, ~/.zshrc, or ~/.bashrc and remove the DocTranslator section
```

## Development

### Building from Source

Requirements:
- Python 3.10-3.12
- pip
- No conflicting packages (installer handles this automatically)

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source
python app.py languages

# Build executable manually
pip install pyinstaller
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
```

### Build Scripts

The project includes automated build and installation scripts:

#### install.sh
Handles the complete build and installation process:
- Detects and removes conflicting packages
- Builds the standalone executable
- Installs to `~/.local/bin`
- Configures PATH if needed

#### uninstall.sh
Provides flexible uninstallation options:
- Basic: Removes just the CLI command
- `--clean-path`: Also removes PATH modifications
- `--clean-all`: Complete removal including build artifacts

### Project Structure

```
translate-doc/
├── app.py                 # Main CLI entry point
├── translate_doc.py       # Core translation logic
├── requirements.txt       # Python dependencies
├── install.sh            # Automated installation script
├── uninstall.sh          # Flexible uninstallation script
├── build/                # Build artifacts (generated)
│   └── DocTranslator/    # PyInstaller build files
├── dist/                 # Distribution directory (generated)
│   └── DocTranslator     # Standalone executable
└── DocTranslator.spec    # PyInstaller spec (generated)
```

### Common Build Issues

1. **pathlib conflict**: The installer automatically removes the obsolete pathlib package
2. **Permission denied**: Run `chmod +x install.sh` before installation
3. **Build fails**: Ensure you have Python 3.10-3.12 and all requirements installed

## Privacy & Security

- API keys are stored locally in `~/.doctranslator/config.json`
- Documents are processed locally and sent to OpenRouter API
- No documents are stored or cached by the tool
- All translations happen over secure HTTPS

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: [Report a bug](https://github.com/wuwangzhang1216/translate-doc/issues)
- Documentation: [This README](README.md)

## Credits

Built with:
- OpenRouter API for translations (supporting multiple AI models including Google Gemini)
- PyInstaller for standalone packaging
- Python libraries: pypdf2, python-docx, python-pptx, openpyxl

---

**Note**: This tool requires an active OpenRouter API key with available credits. Translation quality depends on the selected AI model and API capabilities. OpenRouter provides access to various models including Google Gemini, Claude, GPT-4, and more.
