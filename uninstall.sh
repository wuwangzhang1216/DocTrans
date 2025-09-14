#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Uninstalling DocTranslator CLI...${NC}"

# Remove the executable
if [ -f "$HOME/.local/bin/doctrans" ]; then
    rm "$HOME/.local/bin/doctrans"
    echo -e "${GREEN}✓ Removed doctrans command${NC}"
else
    echo -e "${YELLOW}doctrans command not found in ~/.local/bin${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DocTranslator CLI uninstalled${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Note: PATH modification in your shell config was not removed.${NC}"
echo -e "${YELLOW}You can manually remove the DocTranslator section from:${NC}"

if [ -f "$HOME/.zshrc" ]; then
    echo -e "  - $HOME/.zshrc"
fi
if [ -f "$HOME/.bashrc" ]; then
    echo -e "  - $HOME/.bashrc"
fi
if [ -f "$HOME/.bash_profile" ]; then
    echo -e "  - $HOME/.bash_profile"
fi