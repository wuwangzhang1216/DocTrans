# AWS Console Deployment Steps

Your code has been pushed to GitHub: `https://github.com/wuwangzhang1216/DocTrans.git`

Follow these steps carefully to deploy your application to AWS.

## Environment Variables (Ready to Copy)

```
GEMINI_API_KEY=AIzaSyBNUM6wm1YcLAbR44xUK-n6lA6tVmE95Os
REDIS_URL=rediss://default:ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU@stable-jennet-15065.upstash.io:6379
REDIS_HOST=stable-jennet-15065.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU
NODE_ENV=production
PORT=3001
WORKER_CONCURRENCY=5
JOB_TIMEOUT=600000
MAX_FILE_SIZE=10485760
```

---

## Part 1: Deploy Backend to AWS App Runner

### Step 1: Open App Runner Console
1. Go to: https://console.aws.amazon.com/apprunner/home?region=us-east-1
2. Click **"Create service"**

### Step 2: Configure Source
1. **Repository type**: Select **"Source code repository"**
2. Click **"Add new"** to create a GitHub connection
   - Connection name: `github-translate-doc`
   - Click **"Install another"**
   - Authorize AWS Connector for GitHub
   - Select your repository: `wuwangzhang1216/DocTrans`
   - Click **"Connect"**
3. Back in App Runner:
   - **Repository**: `wuwangzhang1216/DocTrans`
   - **Branch**: `main`
   - **Deployment trigger**: Automatic
   - Click **"Next"**

### Step 3: Configure Build
1. **Configuration file**: Select **"Use a configuration file"**
2. **Configuration file path**: `translate-web-app/backend/apprunner.yaml`
3. Click **"Next"**

### Step 4: Configure Service
1. **Service name**: `translate-doc-backend`
2. **Virtual CPU**: `1 vCPU`
3. **Memory**: `2 GB`

### Step 5: Configure Environment Variables
Click **"Add environment variable"** for each:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | `AIzaSyBNUM6wm1YcLAbR44xUK-n6lA6tVmE95Os` |
| `REDIS_URL` | `rediss://default:ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU@stable-jennet-15065.upstash.io:6379` |
| `REDIS_HOST` | `stable-jennet-15065.upstash.io` |
| `REDIS_PORT` | `6379` |
| `REDIS_PASSWORD` | `ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU` |
| `NODE_ENV` | `production` |
| `PORT` | `3001` |
| `MAX_FILE_SIZE` | `10485760` |
| `JOB_TIMEOUT` | `600000` |

### Step 6: Configure Auto Scaling (Optional)
- **Minimum instances**: 1
- **Maximum instances**: 3

### Step 7: Configure Health Check
- **Health check protocol**: HTTP
- **Health check path**: `/api/health`
- **Interval**: 10 seconds
- **Timeout**: 5 seconds

### Step 8: Review and Create
1. Review all settings
2. Click **"Create & deploy"**
3. **Wait 5-10 minutes** for deployment
4. **COPY THE SERVICE URL** - you'll need it! (e.g., `https://xyz123.us-east-1.awsapprunner.com`)

---

## Part 2: Deploy Worker to AWS App Runner

### Step 1: Open App Runner Console
1. Go to: https://console.aws.amazon.com/apprunner/home?region=us-east-1
2. Click **"Create service"**

### Step 2: Configure Source
1. **Repository type**: Select **"Source code repository"**
2. **Select existing connection**: `github-translate-doc` (created in Part 1)
3. **Repository**: `wuwangzhang1216/DocTrans`
4. **Branch**: `main`
5. **Deployment trigger**: Automatic
6. Click **"Next"**

### Step 3: Configure Build
1. **Configuration file**: Select **"Use a configuration file"**
2. **Configuration file path**: `translate-web-app/worker/apprunner.yaml`
3. Click **"Next"**

### Step 4: Configure Service
1. **Service name**: `translate-doc-worker`
2. **Virtual CPU**: `2 vCPU`
3. **Memory**: `4 GB`

### Step 5: Configure Environment Variables
Click **"Add environment variable"** for each:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | `AIzaSyBNUM6wm1YcLAbR44xUK-n6lA6tVmE95Os` |
| `REDIS_URL` | `rediss://default:ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU@stable-jennet-15065.upstash.io:6379` |
| `REDIS_HOST` | `stable-jennet-15065.upstash.io` |
| `REDIS_PORT` | `6379` |
| `REDIS_PASSWORD` | `ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU` |
| `NODE_ENV` | `production` |
| `WORKER_CONCURRENCY` | `5` |
| `JOB_TIMEOUT` | `600000` |

### Step 6: Configure Auto Scaling (Optional)
- **Minimum instances**: 1
- **Maximum instances**: 5

### Step 7: Review and Create
1. Review all settings
2. Click **"Create & deploy"**
3. **Wait 5-10 minutes** for deployment

---

## Part 3: Deploy Frontend to AWS Amplify

### Step 1: Open Amplify Console
1. Go to: https://console.aws.amazon.com/amplify/home?region=us-east-1
2. Click **"New app"** → **"Host web app"**

### Step 2: Connect Repository
1. Select **"GitHub"**
2. Click **"Authorize AWS Amplify"**
3. Select repository: `wuwangzhang1216/DocTrans`
4. Select branch: `main`
5. Click **"Next"**

### Step 3: Configure Build Settings
1. **App name**: `translate-doc-frontend`
2. Check **"Deploy to a custom build location"**
3. **Build and test settings**:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd translate-web-app/frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: translate-web-app/frontend/.next
    files:
      - '**/*'
  cache:
    paths:
      - translate-web-app/frontend/node_modules/**/*
      - translate-web-app/frontend/.next/cache/**/*
```

4. Click **"Advanced settings"**

### Step 4: Add Environment Variable
**IMPORTANT**: Add this environment variable with your backend URL from Part 1, Step 8

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-BACKEND-URL-FROM-PART-1.us-east-1.awsapprunner.com` |

Replace `YOUR-BACKEND-URL-FROM-PART-1` with the actual URL!

### Step 5: Review and Deploy
1. Click **"Next"**
2. Review settings
3. Click **"Save and deploy"**
4. **Wait 5-10 minutes** for build and deployment

---

## Part 4: Update Backend with Frontend URL (CORS)

After Amplify deploys your frontend:

### Step 1: Get Amplify URL
1. In Amplify Console, copy your app URL (e.g., `https://main.d3xyz.amplifyapp.com`)

### Step 2: Update Backend Environment Variable
1. Go back to App Runner Console
2. Open `translate-doc-backend` service
3. Click **"Configuration"** tab
4. Click **"Edit"** under **"Environment variables"**
5. Add new variable:
   - **Key**: `FRONTEND_URL`
   - **Value**: Your Amplify URL (e.g., `https://main.d3xyz.amplifyapp.com`)
6. Click **"Save changes"**
7. App Runner will automatically redeploy

---

## Verification Steps

### 1. Test Backend
```bash
curl https://YOUR-BACKEND-URL/api/health
```
Should return: `{"status":"ok","timestamp":"..."}`

### 2. Test Frontend
Open your Amplify URL in browser and test:
- Upload a document
- Select target language
- Click translate
- Monitor progress
- Download result

---

## Troubleshooting

### Backend Build Fails
- Check CloudWatch Logs in App Runner console
- Verify `apprunner.yaml` path is correct
- Ensure all environment variables are set

### Worker Build Fails
- Check if Python dependencies are installing correctly
- Increase memory/CPU if build times out
- Check CloudWatch Logs

### Frontend Build Fails
- Check build logs in Amplify console
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Ensure build spec YAML is correct

### Frontend Can't Connect to Backend
1. Verify `NEXT_PUBLIC_API_URL` in Amplify matches backend URL
2. Check `FRONTEND_URL` in backend matches Amplify URL
3. Test backend health endpoint directly

### Jobs Not Processing
- Check worker CloudWatch logs
- Verify Redis connection (REDIS_URL)
- Ensure GEMINI_API_KEY is valid
- Check worker service is running

---

## Cost Estimate

- **App Runner Backend**: ~$25-40/month (1 vCPU, 2GB, always on)
- **App Runner Worker**: ~$40-60/month (2 vCPU, 4GB, always on)
- **Amplify**: ~$5-15/month (hosting + build minutes)
- **Total**: ~$70-115/month

To reduce costs:
- Scale down when not in use
- Use smaller instances
- Enable auto-scaling to scale to zero

---

## Summary

After completing all steps, you'll have:

✅ Backend API running on App Runner
✅ Worker processing jobs on App Runner
✅ Frontend hosted on Amplify
✅ All services connected and communicating

Your app will be live at your Amplify URL!
