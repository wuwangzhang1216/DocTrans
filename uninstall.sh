#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     DocTranslator CLI - Uninstall Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Parse command line arguments
CLEAN_PATH=false
CLEAN_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean-path)
            CLEAN_PATH=true
            shift
            ;;
        --clean-all|-a)
            CLEAN_ALL=true
            CLEAN_PATH=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean-path     Remove PATH modifications from shell configs"
            echo "  --clean-all, -a  Remove everything including build artifacts"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "By default, removes the CLI command and optionally build artifacts."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Uninstalling DocTranslator CLI...${NC}"
echo ""

# Remove the executable
if [ -f "$HOME/.local/bin/doctrans" ]; then
    rm "$HOME/.local/bin/doctrans"
    echo -e "${GREEN}✓ Removed doctrans command${NC}"
else
    echo -e "${YELLOW}⚠ doctrans command not found in ~/.local/bin${NC}"
fi

# Clean up build artifacts if requested
if [ "$CLEAN_ALL" = true ]; then
    echo ""
    echo -e "${BLUE}Cleaning build artifacts...${NC}"

    # Remove PyInstaller build directories
    if [ -d "build" ]; then
        rm -rf build
        echo -e "${GREEN}✓ Removed build directory${NC}"
    fi

    if [ -d "dist" ]; then
        rm -rf dist
        echo -e "${GREEN}✓ Removed dist directory${NC}"
    fi

    # Remove PyInstaller spec file
    if [ -f "DocTranslator.spec" ]; then
        rm DocTranslator.spec
        echo -e "${GREEN}✓ Removed DocTranslator.spec${NC}"
    fi

    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}✓ Removed Python cache directories${NC}"
fi

# Remove PATH modifications if requested
if [ "$CLEAN_PATH" = true ]; then
    echo ""
    echo -e "${BLUE}Removing PATH modifications from shell configs...${NC}"

    # Function to remove DocTranslator section from config file
    remove_from_config() {
        local config_file="$1"
        if [ -f "$config_file" ]; then
            # Create backup
            cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"

            # Remove DocTranslator section (comment and export line)
            sed -i '' '/# DocTranslator CLI/,+1d' "$config_file" 2>/dev/null || \
            sed -i '/# DocTranslator CLI/,+1d' "$config_file" 2>/dev/null || true

            echo -e "${GREEN}✓ Cleaned $config_file${NC}"
        fi
    }

    # Clean all shell configs
    remove_from_config "$HOME/.zshrc"
    remove_from_config "$HOME/.bashrc"
    remove_from_config "$HOME/.bash_profile"
    remove_from_config "$HOME/.profile"

    echo -e "${YELLOW}Note: Backups of modified files created with .backup extension${NC}"
else
    echo ""
    echo -e "${YELLOW}Note: PATH modifications in shell configs were not removed.${NC}"
    echo -e "${YELLOW}To remove them, run: ./uninstall.sh --clean-path${NC}"
    echo ""
    echo -e "${YELLOW}The DocTranslator section can be found in:${NC}"

    if [ -f "$HOME/.zshrc" ] && grep -q "DocTranslator CLI" "$HOME/.zshrc" 2>/dev/null; then
        echo -e "  - $HOME/.zshrc"
    fi
    if [ -f "$HOME/.bashrc" ] && grep -q "DocTranslator CLI" "$HOME/.bashrc" 2>/dev/null; then
        echo -e "  - $HOME/.bashrc"
    fi
    if [ -f "$HOME/.bash_profile" ] && grep -q "DocTranslator CLI" "$HOME/.bash_profile" 2>/dev/null; then
        echo -e "  - $HOME/.bash_profile"
    fi
    if [ -f "$HOME/.profile" ] && grep -q "DocTranslator CLI" "$HOME/.profile" 2>/dev/null; then
        echo -e "  - $HOME/.profile"
    fi
fi

# Show cleanup options if not used
if [ "$CLEAN_ALL" = false ]; then
    echo ""
    echo -e "${YELLOW}To also remove build artifacts, run: ./uninstall.sh --clean-all${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DocTranslator CLI uninstalled${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""