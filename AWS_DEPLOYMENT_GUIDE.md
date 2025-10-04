# AWS Deployment Guide for Document Translation Web App

This guide will help you deploy your document translation web app to AWS using:
- **AWS Amplify** for the Next.js frontend
- **AWS App Runner** for the Express backend
- **AWS App Runner** for the worker process

## Prerequisites

1. **AWS Account** - Sign up at https://aws.amazon.com
2. **AWS CLI** - Install from https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
3. **Docker** - Install from https://docs.docker.com/get-docker/
4. **Git** - For version control and GitHub integration

## Configuration

### 1. Configure AWS CLI

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### 2. Set Environment Variables

Ensure your `.env` file contains all required variables:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key

# Redis Configuration (Upstash)
REDIS_URL=rediss://default:password@your-redis.upstash.io:6379
REDIS_HOST=your-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Server Configuration
PORT=3001
NODE_ENV=production

# Worker Configuration
WORKER_CONCURRENCY=5
JOB_TIMEOUT=600000
MAX_FILE_SIZE=10485760
```

## Deployment Options

### Option 1: Automated Deployment Script (Recommended)

Run the provided deployment script:

```bash
chmod +x deploy-aws.sh
./deploy-aws.sh
```

The script will:
1. Create necessary IAM roles
2. Build and push Docker images to ECR
3. Deploy backend and worker to App Runner
4. Provide instructions for Amplify frontend deployment

### Option 2: Manual Deployment

#### A. Deploy Backend to AWS App Runner

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name translate-doc-backend --region us-east-1
   ```

2. **Build and Push Docker Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build image
   cd translate-web-app/backend
   docker build -t translate-doc-backend .

   # Tag and push
   docker tag translate-doc-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/translate-doc-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/translate-doc-backend:latest
   ```

3. **Create App Runner Service**

   Go to AWS App Runner Console:
   - Click "Create service"
   - Source: Container registry → Amazon ECR
   - Select your image
   - Configure environment variables (from .env)
   - Instance: 1 vCPU, 2 GB memory
   - Create service

4. **Note the Backend URL** (e.g., `https://xyz.us-east-1.awsapprunner.com`)

#### B. Deploy Worker to AWS App Runner

1. **Copy translate_doc.py to worker directory**
   ```bash
   cp translate_doc.py translate-web-app/worker/
   ```

2. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name translate-doc-worker --region us-east-1
   ```

3. **Build and Push Docker Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build image
   cd translate-web-app/worker
   docker build -t translate-doc-worker .

   # Tag and push
   docker tag translate-doc-worker:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/translate-doc-worker:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/translate-doc-worker:latest
   ```

4. **Create App Runner Service**
   - Similar to backend, but using worker image
   - Configure same environment variables

#### C. Deploy Frontend to AWS Amplify

1. **Push Code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for AWS deployment"
   git push origin main
   ```

2. **Create Amplify App**

   Go to AWS Amplify Console:
   - Click "New app" → "Host web app"
   - Connect GitHub repository
   - Select your repository and branch
   - Build settings:
     - Build specification: Use `translate-web-app/frontend/amplify.yml`
     - Root directory: `translate-web-app/frontend`

3. **Configure Environment Variables**
   - Add environment variable:
     - Key: `NEXT_PUBLIC_API_URL`
     - Value: `https://your-backend-url.awsapprunner.com` (from step A.4)

4. **Deploy**
   - Click "Save and deploy"
   - Wait for build to complete

## Using AWS CLI for Amplify (Alternative)

If you prefer CLI deployment for Amplify:

```bash
# Set your backend URL
export BACKEND_URL="https://your-backend-url.awsapprunner.com"

# Create Amplify app
aws amplify create-app \
  --name translate-doc-frontend \
  --repository <your-github-repo-url> \
  --platform WEB \
  --environment-variables NEXT_PUBLIC_API_URL=$BACKEND_URL

# Create branch
aws amplify create-branch \
  --app-id <app-id-from-previous-command> \
  --branch-name main

# Start deployment
aws amplify start-job \
  --app-id <app-id> \
  --branch-name main \
  --job-type RELEASE
```

## Environment Variables Reference

### Backend (App Runner)
- `NODE_ENV`: production
- `REDIS_URL`: Your Upstash Redis URL
- `REDIS_HOST`: Your Redis host
- `REDIS_PORT`: Redis port (6379)
- `REDIS_PASSWORD`: Your Redis password
- `GEMINI_API_KEY`: Your Google Gemini API key
- `WORKER_CONCURRENCY`: 5
- `JOB_TIMEOUT`: 600000
- `MAX_FILE_SIZE`: 10485760
- `PORT`: 3001

### Worker (App Runner)
- `NODE_ENV`: production
- `REDIS_URL`: Your Upstash Redis URL
- `REDIS_HOST`: Your Redis host
- `REDIS_PORT`: Redis port (6379)
- `REDIS_PASSWORD`: Your Redis password
- `GEMINI_API_KEY`: Your Google Gemini API key
- `WORKER_CONCURRENCY`: 5
- `JOB_TIMEOUT`: 600000

### Frontend (Amplify)
- `NEXT_PUBLIC_API_URL`: Backend URL from App Runner

## Post-Deployment

### Verify Deployments

1. **Backend Health Check**
   ```bash
   curl https://your-backend-url.awsapprunner.com/api/health
   ```

2. **Frontend**
   - Visit your Amplify app URL
   - Test file upload and translation

### Monitor Services

- **App Runner**: https://console.aws.amazon.com/apprunner/
- **Amplify**: https://console.aws.amazon.com/amplify/
- **ECR**: https://console.aws.amazon.com/ecr/

### Update Backend URL in Frontend

If you need to update the backend URL later:

1. Go to Amplify Console
2. Select your app → Environment variables
3. Update `NEXT_PUBLIC_API_URL`
4. Redeploy the app

## Cost Estimates

- **App Runner**: ~$25-50/month per service (2 services)
- **Amplify**: ~$5-15/month for hosting
- **ECR**: ~$1/month for image storage
- **Redis (Upstash)**: Free tier available
- **Gemini API**: Pay per use

## Troubleshooting

### Backend/Worker Won't Start
- Check CloudWatch logs in App Runner console
- Verify all environment variables are set
- Ensure Redis is accessible

### Frontend Can't Connect to Backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in backend
- Ensure backend App Runner service is running

### Docker Build Fails
- Ensure Docker is running
- Check Dockerfile syntax
- Verify all dependencies are listed

### Worker Not Processing Jobs
- Check CloudWatch logs
- Verify Redis connection
- Ensure Python dependencies are installed
- Check GEMINI_API_KEY is valid

## Security Recommendations

1. **Use AWS Secrets Manager** for sensitive environment variables
2. **Enable CloudWatch Logs** for monitoring
3. **Set up CloudWatch Alarms** for errors
4. **Use VPC** for backend and worker services
5. **Enable Auto Scaling** in App Runner for production loads

## Cleanup

To delete all resources:

```bash
# Delete App Runner services
aws apprunner delete-service --service-arn <backend-service-arn>
aws apprunner delete-service --service-arn <worker-service-arn>

# Delete ECR repositories
aws ecr delete-repository --repository-name translate-doc-backend --force
aws ecr delete-repository --repository-name translate-doc-worker --force

# Delete Amplify app
aws amplify delete-app --app-id <app-id>
```

## Support

For issues:
- AWS App Runner: https://docs.aws.amazon.com/apprunner/
- AWS Amplify: https://docs.aws.amazon.com/amplify/
- GitHub Issues: [Your repo URL]
