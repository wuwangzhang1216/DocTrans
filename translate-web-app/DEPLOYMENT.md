# DocTrans Heroku Deployment Guide

Complete guide for deploying the DocTrans web application to Heroku with AWS S3 storage.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Deployment](#manual-deployment)
- [AWS S3 Configuration](#aws-s3-configuration)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)
- [Scaling](#scaling)
- [Cost Estimates](#cost-estimates)

---

## Overview

The DocTrans web application is deployed to Heroku as **two separate applications**:

1. **Backend App**: Express API server + Translation worker + AWS S3 integration
2. **Frontend App**: Next.js UI application

### Why Two Apps?

- **Separation of Concerns**: Frontend and backend can scale independently
- **Better Resource Management**: Worker processes isolated from web server
- **Easier Debugging**: Separate logs for frontend and backend
- **Flexible Scaling**: Scale workers independently based on translation load

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Heroku + AWS                             │
├──────────────────────────┬──────────────────────────────────────┤
│  Backend App             │  Frontend App                         │
│  ├─ Web Dyno             │  ├─ Web Dyno                          │
│  │  └─ Express Server    │  │  └─ Next.js Server                │
│  ├─ Worker Dyno          │  └─ Serves React UI                   │
│  │  └─ Translation Jobs  │                                       │
│  └─ Redis Addon          │                                       │
│     └─ Bull Queue        │                                       │
└──────────────────────────┴──────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   AWS S3 Bucket │
                    │   doctranslab   │
                    │  ├─ uploads/    │
                    │  └─ outputs/    │
                    └─────────────────┘
```

### Key Components

- **Web Dyno (Backend)**: Handles API requests, file uploads to S3
- **Worker Dyno (Backend)**: Processes translation jobs from Redis queue
- **Redis**: Bull queue for managing translation jobs
- **AWS S3**: Persistent file storage for uploads and translated documents
- **Frontend Dyno**: Serves Next.js application

---

## Prerequisites

### Required Tools

1. **Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku

   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh

   # Windows
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **AWS CLI** (for S3 bucket setup)
   ```bash
   # macOS
   brew install awscli

   # Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install

   # Windows
   # Download from: https://aws.amazon.com/cli/
   ```

3. **Git** - Installed and configured

### Required Accounts

1. **Heroku Account** - Sign up at https://heroku.com
2. **AWS Account** - Sign up at https://aws.amazon.com
3. **Google AI Studio** - Get Gemini API key at https://ai.google.dev/

---

## Quick Start

Deploy in 3 easy steps!

### Step 1: Login

```bash
# Login to Heroku
heroku login

# Login to AWS
aws configure
```

### Step 2: Create S3 Bucket

```bash
# Create S3 bucket for file storage
aws s3 mb s3://your-bucket-name --region us-east-1

# Verify bucket was created
aws s3 ls
```

### Step 3: Deploy Backend

```bash
cd translate-web-app/backend

# Create Heroku app
heroku create your-backend-app-name --region us

# Add Redis addon
heroku addons:create heroku-redis:mini -a your-backend-app-name

# Set environment variables
heroku config:set \
  GEMINI_API_KEY="your-gemini-api-key" \
  AWS_ACCESS_KEY_ID="your-aws-access-key" \
  AWS_SECRET_ACCESS_KEY="your-aws-secret-key" \
  AWS_REGION="us-east-1" \
  S3_BUCKET_NAME="your-bucket-name" \
  -a your-backend-app-name

# Deploy
git init
git add .
git commit -m "Initial backend deployment"
heroku git:remote -a your-backend-app-name
git push heroku main

# Scale dynos
heroku ps:scale web=1 worker=1 -a your-backend-app-name
```

### Step 4: Deploy Frontend

```bash
cd translate-web-app/frontend

# Create Heroku app
heroku create your-frontend-app-name --region us

# Set backend URL
heroku config:set NEXT_PUBLIC_API_URL="https://your-backend-app-name.herokuapp.com" -a your-frontend-app-name

# Deploy
git init
git add .
git commit -m "Initial frontend deployment"
heroku git:remote -a your-frontend-app-name
git push heroku main

# Scale dynos
heroku ps:scale web=1 -a your-frontend-app-name
```

### Step 5: Verify Deployment

```bash
# Check backend
heroku open -a your-backend-app-name

# Check frontend
heroku open -a your-frontend-app-name

# View logs
heroku logs --tail -a your-backend-app-name
```

---

## Manual Deployment

### Backend Setup

#### 1. Prepare Backend Directory

The backend already has the required files:
- ✅ `Procfile` - Defines web and worker processes
- ✅ `package.json` - Node.js configuration with engines
- ✅ `requirements.txt` - Python dependencies for translation
- ✅ `s3Helper.js` - AWS S3 integration utilities

#### 2. Create Heroku App

```bash
cd translate-web-app/backend

# Create app (choose unique name)
heroku create doctrans-backend-your-name --region us

# Add buildpacks (Python + Node.js)
heroku buildpacks:add --index 1 heroku/python -a doctrans-backend-your-name
heroku buildpacks:add --index 2 heroku/nodejs -a doctrans-backend-your-name
```

#### 3. Add Redis Addon

```bash
# Add Heroku Redis (free tier: 25MB, 20 connections)
heroku addons:create heroku-redis:mini -a doctrans-backend-your-name

# Verify Redis was added
heroku addons -a doctrans-backend-your-name

# Get Redis URL (auto-configured)
heroku config:get REDIS_URL -a doctrans-backend-your-name
```

#### 4. Configure AWS S3

```bash
# Create S3 bucket
aws s3 mb s3://doctranslab-your-name --region us-east-1

# Set bucket policy (optional, for public read access)
aws s3api put-bucket-policy --bucket doctranslab-your-name --policy file://bucket-policy.json
```

Example `bucket-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::doctranslab-your-name/outputs/*"
    }
  ]
}
```

#### 5. Set Environment Variables

```bash
heroku config:set \
  GEMINI_API_KEY="your-gemini-api-key-here" \
  AWS_ACCESS_KEY_ID="your-aws-access-key" \
  AWS_SECRET_ACCESS_KEY="your-aws-secret-key" \
  AWS_REGION="us-east-1" \
  S3_BUCKET_NAME="doctranslab-your-name" \
  NODE_ENV="production" \
  -a doctrans-backend-your-name
```

#### 6. Deploy Backend

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial backend commit for Heroku"

# Add Heroku remote
heroku git:remote -a doctrans-backend-your-name

# Deploy
git push heroku main
```

#### 7. Scale Dynos

```bash
# Start web server
heroku ps:scale web=1 -a doctrans-backend-your-name

# Start translation worker
heroku ps:scale worker=1 -a doctrans-backend-your-name

# Verify dynos are running
heroku ps -a doctrans-backend-your-name
```

### Frontend Setup

#### 1. Prepare Frontend Directory

The frontend already has the required files:
- ✅ `Procfile` - Defines web process
- ✅ `package.json` - Node.js configuration with heroku-postbuild
- ✅ `next.config.js` - Next.js configuration

#### 2. Create Heroku App

```bash
cd translate-web-app/frontend

# Create app
heroku create doctrans-frontend-your-name --region us
```

#### 3. Set Environment Variables

```bash
# Set backend API URL (use your actual backend URL)
heroku config:set \
  NEXT_PUBLIC_API_URL="https://doctrans-backend-your-name.herokuapp.com" \
  NODE_ENV="production" \
  -a doctrans-frontend-your-name
```

#### 4. Deploy Frontend

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial frontend commit for Heroku"

# Add Heroku remote
heroku git:remote -a doctrans-frontend-your-name

# Deploy
git push heroku main
```

#### 5. Scale Dynos

```bash
# Start web server
heroku ps:scale web=1 -a doctrans-frontend-your-name

# Verify dyno is running
heroku ps -a doctrans-frontend-your-name
```

---

## AWS S3 Configuration

### Why S3?

Heroku uses an **ephemeral filesystem** - files are deleted when:
- Dyno restarts
- App redeploys
- Dyno switches (web vs worker)

S3 provides **persistent storage** for:
- Uploaded documents
- Translated documents
- Temporary processing files

### S3 Bucket Structure

```
doctranslab/
├── uploads/
│   ├── abc123_document.pdf
│   ├── def456_presentation.pptx
│   └── ...
└── outputs/
    ├── document_Chinese_1234567890.pdf
    ├── presentation_Spanish_9876543210.pptx
    └── ...
```

### IAM Permissions Required

Your AWS credentials need these S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

---

## Environment Variables

### Backend Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for translation | `AIzaSyDxxx...` |
| `AWS_ACCESS_KEY_ID` | ✅ Yes | AWS access key for S3 | `AKIA3HQ5CT...` |
| `AWS_SECRET_ACCESS_KEY` | ✅ Yes | AWS secret key for S3 | `A12iyfrFMb...` |
| `AWS_REGION` | ✅ Yes | AWS region for S3 bucket | `us-east-1` |
| `S3_BUCKET_NAME` | ✅ Yes | S3 bucket name | `doctranslab` |
| `REDIS_URL` | Auto | Redis connection URL (auto-set) | `redis://...` |
| `PORT` | Auto | Server port (auto-set by Heroku) | `3000` |
| `NODE_ENV` | Optional | Environment mode | `production` |
| `WORKER_CONCURRENCY` | Optional | Number of concurrent workers | `5` |
| `MAX_FILE_SIZE` | Optional | Max upload size in bytes | `10485760` |

### Frontend Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | Backend API URL | `https://backend.herokuapp.com` |
| `PORT` | Auto | Server port (auto-set by Heroku) | `3000` |
| `NODE_ENV` | Optional | Environment mode | `production` |

### Setting Environment Variables

```bash
# Set multiple variables at once
heroku config:set VAR1="value1" VAR2="value2" -a app-name

# View all config vars
heroku config -a app-name

# Get specific variable
heroku config:get VAR_NAME -a app-name

# Unset variable
heroku config:unset VAR_NAME -a app-name
```

---

## Post-Deployment

### Verification Checklist

- [ ] Backend app deployed successfully
- [ ] Frontend app deployed successfully
- [ ] Redis addon attached to backend
- [ ] AWS S3 bucket created and accessible
- [ ] All environment variables set correctly
- [ ] Web dyno running on backend
- [ ] Worker dyno running on backend
- [ ] Web dyno running on frontend
- [ ] Backend health check passing (`/api/health`)
- [ ] Frontend can connect to backend
- [ ] File upload works
- [ ] Translation job completes
- [ ] Translated file downloads from S3

### Test the Deployment

#### 1. Test Backend Health

```bash
curl https://your-backend-app.herokuapp.com/api/health
# Expected: {"status":"ok","timestamp":"..."}
```

#### 2. Test Queue Stats

```bash
curl https://your-backend-app.herokuapp.com/api/stats
# Expected: {"queue":{"waiting":0,"active":0,...}}
```

#### 3. Test File Upload

Upload a test document through the frontend UI and verify:
- File uploads to S3 (`uploads/` folder)
- Job is queued
- Worker processes the job
- Result appears in S3 (`outputs/` folder)
- Download works

#### 4. Check S3 Files

```bash
# List uploaded files
aws s3 ls s3://your-bucket-name/uploads/

# List output files
aws s3 ls s3://your-bucket-name/outputs/
```

---

## Troubleshooting

### Common Issues

#### Issue 1: H10 Error (Backend Crashed)

**Symptoms**: Backend app immediately crashes after deployment

**Causes**:
- Missing environment variables
- Python dependencies not installed
- Node.js version mismatch

**Solutions**:

```bash
# Check logs
heroku logs --tail -a backend-app

# Verify environment variables
heroku config -a backend-app

# Check buildpacks
heroku buildpacks -a backend-app

# Verify Python buildpack is first
heroku buildpacks:add --index 1 heroku/python -a backend-app

# Redeploy
git push heroku main --force
```

#### Issue 2: Worker Not Processing Jobs

**Symptoms**: Jobs stay in "queued" status indefinitely

**Causes**:
- Worker dyno not running
- Redis connection issues
- Python dependencies missing

**Solutions**:

```bash
# Check worker status
heroku ps -a backend-app

# Scale worker if needed
heroku ps:scale worker=1 -a backend-app

# Check worker logs
heroku logs --tail --dyno worker -a backend-app

# Restart worker
heroku ps:restart worker -a backend-app
```

#### Issue 3: S3 Upload/Download Fails

**Symptoms**: "Access Denied" or "File not found" errors

**Causes**:
- AWS credentials not set or incorrect
- IAM permissions insufficient
- Bucket name incorrect

**Solutions**:

```bash
# Verify AWS credentials
heroku config:get AWS_ACCESS_KEY_ID -a backend-app
heroku config:get AWS_SECRET_ACCESS_KEY -a backend-app
heroku config:get S3_BUCKET_NAME -a backend-app

# Test S3 access locally
aws s3 ls s3://your-bucket-name/

# Check IAM permissions in AWS Console
# Ensure your user/role has PutObject, GetObject, DeleteObject permissions
```

#### Issue 4: Frontend Can't Connect to Backend

**Symptoms**: Network errors, CORS errors in browser console

**Causes**:
- Incorrect `NEXT_PUBLIC_API_URL`
- CORS not configured in backend
- Backend not running

**Solutions**:

```bash
# Verify frontend config
heroku config -a frontend-app

# Update backend URL (use exact URL from backend)
heroku config:set NEXT_PUBLIC_API_URL="https://correct-backend-url.herokuapp.com" -a frontend-app

# Restart frontend
heroku restart -a frontend-app

# Check backend is running
curl https://your-backend-url.herokuapp.com/api/health
```

#### Issue 5: Redis Connection Errors

**Symptoms**: "ECONNREFUSED" or "REDIS_URL not found" errors

**Causes**:
- Redis addon not attached
- REDIS_URL not set

**Solutions**:

```bash
# Check if Redis addon is attached
heroku addons -a backend-app

# If not attached, add it
heroku addons:create heroku-redis:mini -a backend-app

# Verify REDIS_URL is set
heroku config:get REDIS_URL -a backend-app

# Restart app after Redis is attached
heroku restart -a backend-app
```

### Debugging Commands

```bash
# View live logs
heroku logs --tail -a app-name

# View logs for specific dyno
heroku logs --tail --dyno web -a app-name
heroku logs --tail --dyno worker -a app-name

# Check dyno status
heroku ps -a app-name

# Run bash in dyno
heroku run bash -a app-name

# Check environment
heroku run env -a app-name

# Check Node.js version
heroku run "node --version" -a app-name

# Check Python version
heroku run "python --version" -a app-name

# Test Python imports
heroku run "python -c 'from translators import DocumentTranslator'" -a app-name
```

---

## Monitoring

### Heroku Dashboard

Monitor your apps at: https://dashboard.heroku.com/

Features:
- Dyno metrics (CPU, memory, response time)
- Dyno logs
- Dyno restart history
- Add-on status

### Command Line Monitoring

```bash
# View metrics
heroku metrics -a app-name

# View dyno status
heroku ps -a app-name

# View release history
heroku releases -a app-name

# View recent logs
heroku logs -n 200 -a app-name

# Monitor queue
curl https://your-backend-url.herokuapp.com/api/stats
```

### Setting Up Alerts

Use Heroku's monitoring add-ons:

```bash
# Add Papertrail for log management
heroku addons:create papertrail -a backend-app

# Add New Relic for performance monitoring
heroku addons:create newrelic -a backend-app
```

---

## Scaling

### Vertical Scaling (More Power Per Dyno)

```bash
# Upgrade to Hobby dyno ($7/month)
heroku ps:type hobby -a backend-app

# Upgrade to Standard dyno ($25-50/month)
heroku ps:type standard-1x -a backend-app

# Upgrade to Performance dyno ($250+/month)
heroku ps:type performance-m -a backend-app
```

### Horizontal Scaling (More Dynos)

```bash
# Scale web dynos (for high traffic)
heroku ps:scale web=2 -a backend-app

# Scale worker dynos (for more concurrent translations)
heroku ps:scale worker=3 -a backend-app

# Scale both
heroku ps:scale web=2 worker=3 -a backend-app
```

### Auto-Scaling

Consider using Heroku's autoscaling feature:

```bash
# Enable autoscaling (requires Standard tier or higher)
heroku ps:autoscale:enable web -a backend-app
heroku ps:autoscale:set web --min=1 --max=5 --p95-response-time=500ms -a backend-app
```

---

## Cost Estimates

### Free Tier

| Resource | Cost | Limitations |
|----------|------|-------------|
| Backend Web Dyno | $0 | 550 hours/month, sleeps after 30min inactivity |
| Backend Worker Dyno | $0 | 550 hours/month, sleeps after 30min inactivity |
| Frontend Web Dyno | $0 | 550 hours/month, sleeps after 30min inactivity |
| Heroku Redis Mini | $0 | 25MB storage, 20 connections |
| AWS S3 | ~$0 | 5GB free tier first year, then $0.023/GB/month |

**Total**: $0/month (with limitations)

**Note**: Free dynos share 1000 hours/month across all apps

### Hobby Tier (Recommended for Production)

| Resource | Cost | Benefits |
|----------|------|----------|
| Backend Web Dyno (Hobby) | $7/month | No sleeping, better performance |
| Backend Worker Dyno (Hobby) | $7/month | Continuous processing |
| Frontend Web Dyno (Hobby) | $7/month | No sleeping |
| Heroku Redis Mini | $0 | Same as free tier |
| AWS S3 | ~$1-5/month | Depends on storage/bandwidth usage |

**Total**: ~$22-26/month

### Production Tier

| Resource | Cost | Benefits |
|----------|------|----------|
| Backend Web Dyno (Standard-1X) | $25/month | More memory, better performance |
| Backend Worker Dyno (Standard-1X × 2) | $50/month | Parallel processing |
| Frontend Web Dyno (Standard-1X) | $25/month | Better performance |
| Heroku Redis Premium-0 | $15/month | 100MB, backups, high availability |
| AWS S3 | ~$5-20/month | Production storage/bandwidth |

**Total**: ~$120-135/month

---

## Security Best Practices

1. **Never Commit Secrets**
   - Use `.gitignore` for `.env` files
   - Use Heroku config vars for all sensitive data

2. **Rotate API Keys Regularly**
   ```bash
   heroku config:set GEMINI_API_KEY="new-key" -a backend-app
   ```

3. **Enable HTTPS Only**
   - Heroku provides SSL automatically
   - Ensure frontend uses `https://` for API URL

4. **Set Strong CORS Policy**
   - Backend should only allow requests from your frontend domain

5. **Monitor for Vulnerabilities**
   ```bash
   # Check for npm vulnerabilities
   npm audit
   npm audit fix
   ```

6. **Use IAM Roles (Instead of Access Keys)**
   - For production, consider using AWS IAM roles with temporary credentials

---

## Support Resources

- **Heroku Dev Center**: https://devcenter.heroku.com/
- **Heroku Status**: https://status.heroku.com/
- **AWS S3 Documentation**: https://docs.aws.amazon.com/s3/
- **Google Gemini AI**: https://ai.google.dev/
- **Project Repository**: Your GitHub repository

---

## Maintenance

### Regular Updates

```bash
# Update dependencies
cd backend
npm update
git add package.json package-lock.json
git commit -m "Update dependencies"
git push heroku main

cd ../frontend
npm update
git add package.json package-lock.json
git commit -m "Update dependencies"
git push heroku main
```

### Database Cleanup (S3)

```bash
# List old files
aws s3 ls s3://your-bucket-name/uploads/ --recursive

# Delete files older than 30 days (example)
aws s3 ls s3://your-bucket-name/uploads/ --recursive | \
  awk '$1 < "'$(date -d '30 days ago' '+%Y-%m-%d')'" {print $4}' | \
  xargs -I {} aws s3 rm s3://your-bucket-name/{}
```

### Log Rotation

Heroku retains logs for 1 week. For longer retention:

```bash
# Add log drain to Papertrail or similar
heroku addons:create papertrail -a backend-app
```

---

**Last Updated**: 2025-10-13
**Version**: 2.0.0 (S3 Integration)
