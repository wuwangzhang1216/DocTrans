# DocTrans CLI - Repository Details

## 📋 Project Overview

**DocTrans CLI** is a powerful command-line tool that translates documents using OpenAI's GPT API. It provides professional-grade translation for multiple document formats while preserving formatting and structure.

### Key Features
- 🌍 **40+ Languages**: Comprehensive language support for global communication
- 📄 **Multiple Formats**: PDF, DOCX, PPTX, XLSX, TXT, MD, HTML
- ⚡ **Batch Processing**: Translate entire folders with parallel processing
- 🎯 **Format Preservation**: Maintains original document structure and styling
- 💻 **Standalone Binary**: No Python required for end users
- 🔧 **Easy Installation**: Simple CLI setup similar to popular tools like Claude Code

## 🏗️ Architecture

### Technology Stack
- **Language**: Python 3.10-3.12
- **AI Model**: OpenAI GPT-4/GPT-3.5
- **Build Tool**: PyInstaller
- **Document Processing Libraries**:
  - PyPDF2 & pdfplumber (PDF)
  - python-docx (Word)
  - python-pptx (PowerPoint)
  - openpyxl (Excel)
  - BeautifulSoup4 (HTML)
  - markdown (Markdown)

### Project Structure
```
translate-doc/
├── app.py                 # CLI entry point and command handler
├── translate_doc.py       # Core translation engine
├── requirements.txt       # Python dependencies
├── build/
│   └── build_macos.sh    # macOS build script
├── dist/
│   └── DocTranslator     # Standalone executable (generated)
├── install.sh            # System installation script
├── uninstall.sh          # Removal script
├── README.md             # User documentation
├── LICENSE               # MIT License
└── BUILDING.md           # Build instructions
```

## 🚀 Installation & Usage

### Quick Start
```bash
# Clone and install
git clone https://github.com/wuwangzhang1216/translate-doc.git
cd translate-doc
./install.sh

# Use the CLI
doctrans translate document.pdf -l Chinese
doctrans batch ./docs ./translated -l Spanish
```

### Command Examples
```bash
# Configure API key
doctrans config --set-key sk-your-api-key

# List supported languages
doctrans languages

# Translate with custom output
doctrans translate report.docx -l French -o rapport.docx

# Batch process specific file types
doctrans batch ./input ./output -l German --types "pdf,docx"
```

## 🔑 Key Components

### 1. **app.py** - CLI Interface
- Argument parsing and command routing
- Configuration management
- User interaction and progress display
- API key handling (env, config, CLI args)

### 2. **translate_doc.py** - Translation Engine
- Document parsing and extraction
- OpenAI API integration
- Parallel processing with ThreadPoolExecutor
- Format-specific translation strategies
- Progress tracking with tqdm

### 3. **Build System**
- PyInstaller configuration for standalone binary
- Platform-specific build scripts
- Dependency bundling
- Code signing preparation

## 📊 Performance

- **Parallel Processing**: Up to 32 concurrent workers
- **Batch Optimization**: Smart chunking for API efficiency
- **Memory Efficient**: Streaming for large documents
- **Progress Tracking**: Real-time status updates

## 🔐 Security & Privacy

- **Local Processing**: Documents processed on user's machine
- **Secure API Storage**: Keys stored in protected config file
- **No Data Retention**: No document caching or storage
- **HTTPS Only**: All API communications encrypted

## 📈 Future Enhancements

### Planned Features
- [ ] Windows and Linux builds
- [ ] Additional language models support
- [ ] Custom translation glossaries
- [ ] Translation quality metrics
- [ ] Incremental translation for large documents
- [ ] GUI version
- [ ] Cloud deployment option

### Potential Improvements
- [ ] Support for more file formats (RTF, ODT, etc.)
- [ ] Translation memory/caching
- [ ] Batch translation resume capability
- [ ] Custom formatting rules
- [ ] API usage tracking and reporting

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional file format support
- Translation quality enhancements
- Performance optimizations
- Documentation improvements
- Bug fixes and testing

## 📝 Development Notes

### Building from Source
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Run from source
python app.py translate file.pdf -l Chinese

# Build executable
./build/build_macos.sh
```

### Testing
```bash
# Test basic functionality
./dist/DocTranslator languages
./dist/DocTranslator --help

# Test translation (requires API key)
./dist/DocTranslator translate test.txt -l Spanish
```

## 📊 Repository Statistics

- **Primary Language**: Python
- **License**: MIT
- **Dependencies**: 10+ specialized libraries
- **Executable Size**: ~154MB (includes Python runtime)
- **Supported Platforms**: macOS (Windows/Linux planned)

## 🔗 Links

- **Repository**: https://github.com/wuwangzhang1216/translate-doc
- **Issues**: https://github.com/wuwangzhang1216/translate-doc/issues
- **Documentation**: See README.md

## 👤 Author

- **GitHub**: wuwangzhang1216
- **Project**: DocTrans CLI
- **Year**: 2024

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

*Built with ❤️ using Python and OpenAI API*