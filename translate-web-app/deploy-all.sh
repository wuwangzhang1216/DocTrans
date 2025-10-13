#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DocTrans - Complete Heroku Deployment${NC}"
echo -e "${BLUE}══════════════════════════════════════════════${NC}"
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed${NC}"
    echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Login to Heroku
echo -e "${YELLOW}Checking Heroku authentication...${NC}"
if ! heroku auth:whoami &> /dev/null; then
    echo -e "${BLUE}Please login to Heroku:${NC}"
    heroku login
fi

echo -e "${GREEN}✓ Logged in as: $(heroku auth:whoami)${NC}"
echo ""

# Get app names
echo -e "${BLUE}═══ Step 1: App Configuration ═══${NC}"
echo ""
read -p "Enter backend app name (e.g., doctrans-backend): " BACKEND_APP
read -p "Enter frontend app name (e.g., doctrans-frontend): " FRONTEND_APP
echo ""

# Get API key
read -sp "Enter your Gemini API key: " GEMINI_KEY
echo ""
echo ""

# Deploy Backend
echo -e "${BLUE}═══ Step 2: Deploying Backend ═══${NC}"
echo ""

# Create backend app if it doesn't exist
if ! heroku apps:info -a "$BACKEND_APP" &> /dev/null; then
    echo -e "${YELLOW}Creating backend app...${NC}"
    heroku create "$BACKEND_APP" --region us

    echo -e "${YELLOW}Adding Redis addon...${NC}"
    heroku addons:create heroku-redis:mini -a "$BACKEND_APP"

    echo -e "${YELLOW}Setting environment variables...${NC}"
    heroku config:set GEMINI_API_KEY="$GEMINI_KEY" -a "$BACKEND_APP"
    heroku config:set NODE_ENV=production -a "$BACKEND_APP"

    echo -e "${GREEN}✓ Backend app created${NC}"
else
    echo -e "${GREEN}✓ Backend app already exists${NC}"
fi

# Get backend URL
BACKEND_URL="https://$BACKEND_APP.herokuapp.com"
echo -e "${GREEN}Backend URL: $BACKEND_URL${NC}"
echo ""

# Deploy Frontend
echo -e "${BLUE}═══ Step 3: Deploying Frontend ═══${NC}"
echo ""

# Create frontend app if it doesn't exist
if ! heroku apps:info -a "$FRONTEND_APP" &> /dev/null; then
    echo -e "${YELLOW}Creating frontend app...${NC}"
    heroku create "$FRONTEND_APP" --region us

    echo -e "${YELLOW}Setting environment variables...${NC}"
    heroku config:set NEXT_PUBLIC_API_URL="$BACKEND_URL" -a "$FRONTEND_APP"
    heroku config:set NODE_ENV=production -a "$FRONTEND_APP"

    echo -e "${GREEN}✓ Frontend app created${NC}"
else
    echo -e "${GREEN}✓ Frontend app already exists${NC}"
    echo -e "${YELLOW}Updating backend URL...${NC}"
    heroku config:set NEXT_PUBLIC_API_URL="$BACKEND_URL" -a "$FRONTEND_APP"
fi

echo ""
echo -e "${BLUE}═══ Step 4: Deployment Instructions ═══${NC}"
echo ""
echo -e "${YELLOW}Apps have been created and configured. To deploy:${NC}"
echo ""
echo -e "${GREEN}1. Deploy Backend:${NC}"
echo -e "   cd backend"
echo -e "   git init"
echo -e "   git add ."
echo -e "   git commit -m \"Initial commit\""
echo -e "   heroku git:remote -a $BACKEND_APP"
echo -e "   git push heroku main"
echo -e "   heroku ps:scale web=1 worker=1 -a $BACKEND_APP"
echo ""
echo -e "${GREEN}2. Deploy Frontend:${NC}"
echo -e "   cd ../frontend"
echo -e "   git init"
echo -e "   git add ."
echo -e "   git commit -m \"Initial commit\""
echo -e "   heroku git:remote -a $FRONTEND_APP"
echo -e "   git push heroku main"
echo -e "   heroku ps:scale web=1 -a $FRONTEND_APP"
echo ""
echo -e "${BLUE}Or use the automated scripts:${NC}"
echo -e "   ./deploy-backend.sh $BACKEND_APP"
echo -e "   ./deploy-frontend.sh $FRONTEND_APP $BACKEND_URL"
echo ""
echo -e "${BLUE}═══ Deployment URLs ═══${NC}"
echo -e "Backend:  ${GREEN}$BACKEND_URL${NC}"
echo -e "Frontend: ${GREEN}https://$FRONTEND_APP.herokuapp.com${NC}"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
