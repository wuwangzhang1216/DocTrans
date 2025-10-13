#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}  DocTrans Backend - Heroku Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed${NC}"
    echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Get app name from argument or prompt
if [ -z "$1" ]; then
    echo -e "${BLUE}Enter your Heroku backend app name:${NC}"
    read -p "App name: " APP_NAME
else
    APP_NAME="$1"
fi

echo -e "${GREEN}Deploying to: $APP_NAME${NC}"
echo ""

# Check if app exists
if ! heroku apps:info -a "$APP_NAME" &> /dev/null; then
    echo -e "${BLUE}App doesn't exist. Creating new app...${NC}"
    heroku create "$APP_NAME" --region us

    echo -e "${BLUE}Adding Redis addon...${NC}"
    heroku addons:create heroku-redis:mini -a "$APP_NAME"

    echo -e "${BLUE}Please set your GEMINI_API_KEY:${NC}"
    read -sp "Enter your Gemini API key: " API_KEY
    echo ""
    heroku config:set GEMINI_API_KEY="$API_KEY" -a "$APP_NAME"
fi

# Check if we're in the right directory
if [ ! -f "backend/server.js" ]; then
    echo -e "${RED}Error: Please run this script from the translate-web-app directory${NC}"
    exit 1
fi

# Copy necessary files
echo -e "${BLUE}Preparing backend files...${NC}"
cd backend

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial backend deployment"
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
heroku ps:scale web=1 worker=1 -a "$APP_NAME"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Backend deployed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "App URL: ${BLUE}$(heroku info -a "$APP_NAME" | grep "Web URL" | cut -d: -f2-)${NC}"
echo ""
echo -e "${BLUE}View logs with:${NC} heroku logs --tail -a $APP_NAME"
echo -e "${BLUE}Check status with:${NC} heroku ps -a $APP_NAME"
echo ""
