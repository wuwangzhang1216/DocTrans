#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     DocTranslator CLI - Build & Install Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Function to build the executable
build_executable() {
    echo -e "${BLUE}Building DocTranslator for macOS...${NC}"

    # Check for conflicting pathlib package
    if pip show pathlib &>/dev/null; then
        echo -e "${YELLOW}⚠ Found obsolete 'pathlib' package that conflicts with PyInstaller${NC}"
        echo -e "${YELLOW}Attempting to uninstall it...${NC}"
        pip uninstall -y pathlib 2>/dev/null || {
            echo -e "${RED}Warning: Could not remove pathlib package.${NC}"
            echo -e "${RED}You may need to manually run: pip uninstall pathlib${NC}"
            echo -e "${RED}or: conda remove pathlib${NC}"
            echo -e "${YELLOW}Attempting to continue anyway...${NC}"
        }
    fi

    # Install dependencies
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip3 install -r requirements.txt
    pip3 install pyinstaller

    # Create standalone executable with PyInstaller
    echo -e "${YELLOW}Creating standalone executable with PyInstaller...${NC}"
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

    echo -e "${GREEN}✓ Build complete! Executable created at: dist/DocTranslator${NC}"
}

# Function to install the CLI
install_cli() {
    echo -e "${BLUE}Installing DocTranslator CLI...${NC}"

    # Create local bin directory if it doesn't exist
    mkdir -p ~/.local/bin

    # Copy executable with shorter name
    echo -e "${YELLOW}Installing doctrans command...${NC}"
    cp dist/DocTranslator ~/.local/bin/doctrans
    chmod +x ~/.local/bin/doctrans

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}Adding ~/.local/bin to PATH...${NC}"

        # Detect shell and update appropriate config file
        if [ -n "$ZSH_VERSION" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        elif [ -n "$BASH_VERSION" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
            # Also update .bash_profile for macOS
            if [ -f "$HOME/.bash_profile" ]; then
                SHELL_CONFIG="$HOME/.bash_profile"
            fi
        else
            SHELL_CONFIG="$HOME/.profile"
        fi

        # Add PATH export to shell config
        echo '' >> "$SHELL_CONFIG"
        echo '# DocTranslator CLI' >> "$SHELL_CONFIG"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"

        echo -e "${GREEN}✓ Added ~/.local/bin to PATH in $SHELL_CONFIG${NC}"
        echo -e "${YELLOW}Please run: source $SHELL_CONFIG${NC}"
        echo -e "${YELLOW}Or restart your terminal for changes to take effect${NC}"
    else
        echo -e "${GREEN}✓ ~/.local/bin is already in PATH${NC}"
    fi
}

# Parse command line arguments
FORCE_BUILD=false
SKIP_BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|--rebuild|-b)
            FORCE_BUILD=true
            shift
            ;;
        --skip-build|-s)
            SKIP_BUILD=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build, -b      Force rebuild even if executable exists"
            echo "  --skip-build, -s Skip build step and only install existing executable"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "By default, the script will build if executable doesn't exist,"
            echo "then install the CLI command."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
if [ "$SKIP_BUILD" = false ]; then
    # Check if we need to build
    if [ ! -f "dist/DocTranslator" ] || [ "$FORCE_BUILD" = true ]; then
        if [ "$FORCE_BUILD" = true ]; then
            echo -e "${YELLOW}Force rebuild requested...${NC}"
        else
            echo -e "${YELLOW}Executable not found. Building...${NC}"
        fi
        build_executable
    else
        echo -e "${GREEN}✓ Executable already exists. Skipping build.${NC}"
        echo -e "${YELLOW}  (Use --build to force rebuild)${NC}"
    fi
else
    # Check if executable exists when skipping build
    if [ ! -f "dist/DocTranslator" ]; then
        echo -e "${RED}Error: Executable not found and --skip-build was specified.${NC}"
        echo -e "${RED}Please run without --skip-build to build the executable first.${NC}"
        exit 1
    fi
fi

# Install the CLI
echo ""
install_cli

# Print success message and usage instructions
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DocTranslator CLI installed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "You can now use the ${GREEN}doctrans${NC} command from anywhere:"
echo ""
echo -e "  ${GREEN}doctrans${NC} --help                    Show help"
echo -e "  ${GREEN}doctrans${NC} languages                 List supported languages"
echo -e "  ${GREEN}doctrans${NC} translate file.pdf -l zh  Translate to Chinese"
echo -e "  ${GREEN}doctrans${NC} batch ./in ./out -l es    Batch translate to Spanish"
echo -e "  ${GREEN}doctrans${NC} config --set-key sk-...   Set OpenAI API key"
echo ""

# Test if it works immediately (if PATH is already set)
if command -v doctrans &> /dev/null; then
    echo -e "${GREEN}✓ Command 'doctrans' is ready to use!${NC}"
else
    echo -e "${YELLOW}ℹ Restart your terminal or run 'source $SHELL_CONFIG' to use 'doctrans'${NC}"
fi