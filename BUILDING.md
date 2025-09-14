DocTranslator — Building Standalone Binaries

Overview

- Produces a single-file executable per OS with PyInstaller.
- No dependencies required for end users; all libs are bundled.
- macOS and Windows builds must be made on their respective OSes.

Prerequisites

- Python 3.10–3.12 installed on the build machine.
- Internet access to install dependencies.

Windows

- Build: powershell -ExecutionPolicy Bypass -File build/build_win.ps1
- Output: dist/DocTranslator.exe
- Quick check: dist/DocTranslator.exe languages

macOS

- Make executable: chmod +x build/build_macos.sh
- Build: ./build/build_macos.sh
- Output: dist/DocTranslator
- Quick check: ./dist/DocTranslator languages

Usage

- Translate one file: DocTranslator translate path/to/file.pdf -l Chinese
- Batch translate: DocTranslator batch ./input ./output -l Spanish
- List languages: DocTranslator languages
- Configure API key: DocTranslator config --set-key sk-...

Notes

- API key is read from: --api-key flag, OPENAI_API_KEY env var, or saved config.
- Cross-compiling isn’t supported by PyInstaller. Build on each target OS.
- If corporate AV blocks the exe, code-sign the binary and mark it as trusted.

Security

- Avoid hardcoding secrets in source files; prefer the config or env var.
- If distributing, consider code-signing and Apple notarization for macOS.

