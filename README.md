# DocTrans CLI - Document Translator

A powerful command-line tool for translating documents using OpenAI's API. Supports multiple file formats including PDF, Word, PowerPoint, Excel, and more.

## Features

- **Multiple Format Support**: PDF, DOCX, PPTX, XLSX, TXT, MD, HTML
- **Batch Processing**: Translate entire folders of documents
- **40+ Languages**: Support for major world languages
- **Smart Formatting**: Preserves document structure and formatting
- **Progress Tracking**: Real-time progress bars and status updates
- **Standalone Binary**: No Python installation required

## Installation

### Quick Install (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/translate-doc.git
cd translate-doc
```

2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

This will:
- Build the standalone executable (if not already built)
- Install the `doctrans` command to `~/.local/bin`
- Add the directory to your PATH (if needed)
- Make the command available system-wide

3. Restart your terminal or run:
```bash
source ~/.bash_profile  # or ~/.zshrc for zsh users
```

### Manual Build

If you prefer to build manually:

```bash
# Make the build script executable
chmod +x build/build_macos.sh

# Build the executable
./build/build_macos.sh

# The executable will be at: dist/DocTranslator
```

### System Requirements

- **macOS**: 10.15 or later
- **OpenAI API Key**: Required for translation services

## Configuration

### Setting up your API Key

You have three options to provide your OpenAI API key:

1. **Using the config command** (Recommended):
```bash
doctrans config --set-key sk-your-api-key-here
```

2. **Environment variable**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
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
- `--model`: GPT model to use (default: gpt-4o-mini)
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
3. Check your OpenAI account has credits

### Permission Denied

If you get permission errors:
```bash
chmod +x ~/.local/bin/doctrans
```

## Uninstallation

To remove DocTrans CLI:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

Or manually:
```bash
rm ~/.local/bin/doctrans
rm -rf ~/.doctranslator  # Config directory
```

## Development

### Building from Source

Requirements:
- Python 3.10-3.12
- pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source
python app.py languages

# Build executable
pip install pyinstaller
./build/build_macos.sh
```

### Project Structure

```
translate-doc/
├── app.py                 # Main CLI entry point
├── translate_doc.py       # Core translation logic
├── requirements.txt       # Python dependencies
├── build/
│   └── build_macos.sh    # macOS build script
├── dist/
│   └── DocTranslator     # Built executable
├── install.sh            # Installation script
└── uninstall.sh          # Uninstallation script
```

## Privacy & Security

- API keys are stored locally in `~/.doctranslator/config.json`
- Documents are processed locally and sent to OpenAI API
- No documents are stored or cached by the tool
- All translations happen over secure HTTPS

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: [Report a bug](https://github.com/yourusername/translate-doc/issues)
- Documentation: [This README](README.md)

## Credits

Built with:
- OpenAI GPT API for translations
- PyInstaller for standalone packaging
- Python libraries: pypdf2, python-docx, python-pptx, openpyxl

---

**Note**: This tool requires an active OpenAI API key with available credits. Translation quality depends on the selected GPT model and API capabilities.