#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing DocTranslator CLI...${NC}"

# Check if executable exists
if [ ! -f "dist/DocTranslator" ]; then
    echo -e "${YELLOW}Executable not found. Building first...${NC}"
    if [ -f "build/build_macos.sh" ]; then
        chmod +x build/build_macos.sh
        ./build/build_macos.sh
    else
        echo -e "${RED}Build script not found. Please run the build process first.${NC}"
        exit 1
    fi
fi

# Create local bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Copy executable with shorter name
echo -e "${GREEN}Installing doctrans command...${NC}"
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