#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DocTrans Frontend - Heroku Deployment${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed${NC}"
    echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Get app name from argument or prompt
if [ -z "$1" ]; then
    echo -e "${BLUE}Enter your Heroku frontend app name:${NC}"
    read -p "App name: " APP_NAME
else
    APP_NAME="$1"
fi

echo -e "${GREEN}Deploying to: $APP_NAME${NC}"
echo ""

# Get backend URL
if [ -z "$2" ]; then
    echo -e "${BLUE}Enter your backend API URL (e.g., https://doctrans-backend.herokuapp.com):${NC}"
    read -p "Backend URL: " BACKEND_URL
else
    BACKEND_URL="$2"
fi

# Check if app exists
if ! heroku apps:info -a "$APP_NAME" &> /dev/null; then
    echo -e "${BLUE}App doesn't exist. Creating new app...${NC}"
    heroku create "$APP_NAME" --region us

    echo -e "${BLUE}Setting backend URL...${NC}"
    heroku config:set NEXT_PUBLIC_API_URL="$BACKEND_URL" -a "$APP_NAME"
fi

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}Error: Please run this script from the translate-web-app directory${NC}"
    exit 1
fi

# Copy necessary files
echo -e "${BLUE}Preparing frontend files...${NC}"
cd frontend

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial frontend deployment"
fi

# Add Heroku remote
if ! git remote | grep -q heroku; then
    heroku git:remote -a "$APP_NAME"
fi

# Deploy
echo -e "${BLUE}Deploying to Heroku...${NC}"
git push heroku main --force

# Scale dynos
echo -e "${BLUE}Scaling dynos...${NC}"
heroku ps:scale web=1 -a "$APP_NAME"

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Frontend deployed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo -e "App URL: ${BLUE}$(heroku info -a "$APP_NAME" | grep "Web URL" | cut -d: -f2-)${NC}"
echo ""
echo -e "${BLUE}View logs with:${NC} heroku logs --tail -a $APP_NAME"
echo -e "${BLUE}Check status with:${NC} heroku ps -a $APP_NAME"
echo ""
