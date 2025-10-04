#!/bin/bash

# AWS Deployment Script for Document Translation Web App
# This script deploys the frontend to AWS Amplify and backend/worker to AWS App Runner

set -e  # Exit on error

echo "=== Document Translation Web App - AWS Deployment ==="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials are not configured."
    echo "Run: aws configure"
    exit 1
fi

# Variables - Update these with your values
AWS_REGION="${AWS_REGION:-us-east-1}"
APP_NAME="translate-doc"
BACKEND_SERVICE_NAME="${APP_NAME}-backend"
WORKER_SERVICE_NAME="${APP_NAME}-worker"
GITHUB_REPO_URL="${GITHUB_REPO_URL:-}"  # Set your GitHub repo URL

echo "AWS Region: $AWS_REGION"
echo ""

# Function to deploy to App Runner
deploy_app_runner() {
    local SERVICE_NAME=$1
    local SOURCE_DIR=$2
    local SERVICE_ROLE_ARN=$3

    echo "Deploying $SERVICE_NAME to AWS App Runner..."

    # Check if ECR repository exists, create if not
    REPO_URI=$(aws ecr describe-repositories --repository-names "$SERVICE_NAME" --region "$AWS_REGION" --query 'repositories[0].repositoryUri' --output text 2>/dev/null || echo "")

    if [ -z "$REPO_URI" ]; then
        echo "Creating ECR repository for $SERVICE_NAME..."
        REPO_URI=$(aws ecr create-repository --repository-name "$SERVICE_NAME" --region "$AWS_REGION" --query 'repository.repositoryUri' --output text)
    fi

    echo "ECR Repository: $REPO_URI"

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REPO_URI"

    # Build Docker image
    echo "Building Docker image for $SERVICE_NAME..."
    cd "$SOURCE_DIR"
    docker build -t "$SERVICE_NAME" .

    # Tag and push to ECR
    docker tag "$SERVICE_NAME:latest" "$REPO_URI:latest"
    echo "Pushing image to ECR..."
    docker push "$REPO_URI:latest"

    cd - > /dev/null

    # Check if App Runner service exists
    SERVICE_ARN=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text)

    if [ -z "$SERVICE_ARN" ]; then
        echo "Creating App Runner service: $SERVICE_NAME..."

        # Create App Runner service
        aws apprunner create-service \
            --service-name "$SERVICE_NAME" \
            --region "$AWS_REGION" \
            --source-configuration "{
                \"ImageRepository\": {
                    \"ImageIdentifier\": \"$REPO_URI:latest\",
                    \"ImageRepositoryType\": \"ECR\",
                    \"ImageConfiguration\": {
                        \"Port\": \"3001\",
                        \"RuntimeEnvironmentVariables\": {
                            \"NODE_ENV\": \"production\",
                            \"REDIS_URL\": \"$REDIS_URL\",
                            \"REDIS_HOST\": \"$REDIS_HOST\",
                            \"REDIS_PORT\": \"$REDIS_PORT\",
                            \"REDIS_PASSWORD\": \"$REDIS_PASSWORD\",
                            \"GEMINI_API_KEY\": \"$GEMINI_API_KEY\",
                            \"WORKER_CONCURRENCY\": \"5\",
                            \"JOB_TIMEOUT\": \"600000\",
                            \"MAX_FILE_SIZE\": \"10485760\"
                        }
                    }
                },
                \"AutoDeploymentsEnabled\": false,
                \"AuthenticationConfiguration\": {
                    \"AccessRoleArn\": \"$SERVICE_ROLE_ARN\"
                }
            }" \
            --instance-configuration "{
                \"Cpu\": \"1024\",
                \"Memory\": \"2048\"
            }"
    else
        echo "Updating App Runner service: $SERVICE_NAME..."

        # Update App Runner service
        aws apprunner update-service \
            --service-arn "$SERVICE_ARN" \
            --region "$AWS_REGION" \
            --source-configuration "{
                \"ImageRepository\": {
                    \"ImageIdentifier\": \"$REPO_URI:latest\",
                    \"ImageRepositoryType\": \"ECR\",
                    \"ImageConfiguration\": {
                        \"Port\": \"3001\",
                        \"RuntimeEnvironmentVariables\": {
                            \"NODE_ENV\": \"production\",
                            \"REDIS_URL\": \"$REDIS_URL\",
                            \"REDIS_HOST\": \"$REDIS_HOST\",
                            \"REDIS_PORT\": \"$REDIS_PORT\",
                            \"REDIS_PASSWORD\": \"$REDIS_PASSWORD\",
                            \"GEMINI_API_KEY\": \"$GEMINI_API_KEY\",
                            \"WORKER_CONCURRENCY\": \"5\",
                            \"JOB_TIMEOUT\": \"600000\",
                            \"MAX_FILE_SIZE\": \"10485760\"
                        }
                    }
                },
                \"AutoDeploymentsEnabled\": false,
                \"AuthenticationConfiguration\": {
                    \"AccessRoleArn\": \"$SERVICE_ROLE_ARN\"
                }
            }"
    fi

    echo "$SERVICE_NAME deployment initiated!"
}

# Step 1: Load environment variables
echo "Step 1: Loading environment variables from .env file..."
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Environment variables loaded."
else
    echo "Warning: .env file not found. Please ensure environment variables are set."
fi
echo ""

# Step 2: Create IAM role for App Runner (if not exists)
echo "Step 2: Setting up IAM role for App Runner..."
ROLE_NAME="AppRunnerECRAccessRole"
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "Creating IAM role for App Runner..."

    # Create trust policy
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    ROLE_ARN=$(aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --query 'Role.Arn' \
        --output text)

    # Attach ECR access policy
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"

    echo "IAM role created: $ROLE_ARN"
    echo "Waiting 10 seconds for IAM role to propagate..."
    sleep 10
else
    echo "Using existing IAM role: $ROLE_ARN"
fi
echo ""

# Step 3: Deploy Backend to App Runner
echo "Step 3: Deploying Backend to AWS App Runner..."
deploy_app_runner "$BACKEND_SERVICE_NAME" "translate-web-app/backend" "$ROLE_ARN"
echo ""

# Step 4: Deploy Worker to App Runner
echo "Step 4: Deploying Worker to AWS App Runner..."
# Copy translate_doc.py to worker directory for Docker build
cp translate_doc.py translate-web-app/worker/ 2>/dev/null || echo "translate_doc.py already in worker directory"
deploy_app_runner "$WORKER_SERVICE_NAME" "translate-web-app/worker" "$ROLE_ARN"
echo ""

# Step 5: Get Backend URL
echo "Step 5: Getting Backend service URL..."
BACKEND_URL=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='$BACKEND_SERVICE_NAME'].ServiceUrl" --output text)

if [ ! -z "$BACKEND_URL" ]; then
    BACKEND_URL="https://$BACKEND_URL"
    echo "Backend URL: $BACKEND_URL"
else
    echo "Warning: Could not retrieve backend URL. Please check App Runner console."
    BACKEND_URL="https://your-backend-url.awsapprunner.com"
fi
echo ""

# Step 6: Deploy Frontend to AWS Amplify
echo "Step 6: Deploying Frontend to AWS Amplify..."
echo ""

if [ -z "$GITHUB_REPO_URL" ]; then
    echo "Manual Amplify Setup Required:"
    echo "================================"
    echo "1. Go to AWS Amplify Console: https://console.aws.amazon.com/amplify/"
    echo "2. Click 'New app' -> 'Host web app'"
    echo "3. Connect your GitHub repository"
    echo "4. Set build settings to use: translate-web-app/frontend/amplify.yml"
    echo "5. Add environment variable:"
    echo "   - Key: NEXT_PUBLIC_API_URL"
    echo "   - Value: $BACKEND_URL"
    echo "6. Deploy the app"
    echo ""
    echo "Alternatively, set GITHUB_REPO_URL environment variable and re-run this script."
else
    echo "Attempting to create Amplify app..."

    # Note: This requires GitHub OAuth token and additional setup
    # For production, use Amplify console or configure GitHub OAuth

    AMPLIFY_APP_ID=$(aws amplify create-app \
        --name "$APP_NAME-frontend" \
        --region "$AWS_REGION" \
        --repository "$GITHUB_REPO_URL" \
        --platform WEB \
        --build-spec "$(cat translate-web-app/frontend/amplify.yml)" \
        --environment-variables "NEXT_PUBLIC_API_URL=$BACKEND_URL" \
        --query 'app.appId' \
        --output text 2>/dev/null || echo "")

    if [ ! -z "$AMPLIFY_APP_ID" ]; then
        echo "Amplify App created: $AMPLIFY_APP_ID"
        echo "Visit: https://console.aws.amazon.com/amplify/apps/$AMPLIFY_APP_ID"
    else
        echo "Could not create Amplify app via CLI. Please use the manual setup instructions above."
    fi
fi

echo ""
echo "=== Deployment Summary ==="
echo "Backend Service: $BACKEND_SERVICE_NAME"
echo "Backend URL: $BACKEND_URL"
echo "Worker Service: $WORKER_SERVICE_NAME"
echo ""
echo "Monitor your deployments:"
echo "- App Runner: https://console.aws.amazon.com/apprunner/home?region=$AWS_REGION"
echo "- Amplify: https://console.aws.amazon.com/amplify/"
echo ""
echo "Deployment complete!"
