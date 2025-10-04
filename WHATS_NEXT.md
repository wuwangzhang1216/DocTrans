# ✅ What's Been Deployed

## 🎉 Backend and Worker are being deployed to AWS App Runner!

### Services Created:

1. **Backend**: `translate-doc-backend`
   - URL: https://ba37ecejh7.us-east-1.awsapprunner.com
   - Status: Building... (5-10 minutes)

2. **Worker**: `translate-doc-worker`
   - URL: https://zrizgtqpij.us-east-1.awsapprunner.com
   - Status: Building... (5-10 minutes)

---

## 🔍 Monitor Deployment

### Option 1: AWS Console
Visit: https://console.aws.amazon.com/apprunner/home?region=us-east-1

You'll see both services building. Wait for status to change to **RUNNING** (green).

### Option 2: Command Line
```bash
# Check backend status
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-east-1:772081360719:service/translate-doc-backend/2b0af65830f54d24bc098358bfd54a67 \
  --region us-east-1 \
  --query 'Service.{Name:ServiceName,Status:Status}' \
  --output table

# Check worker status
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-east-1:772081360719:service/translate-doc-worker/39537b9e64224712868d12275642bccd \
  --region us-east-1 \
  --query 'Service.{Name:ServiceName,Status:Status}' \
  --output table
```

---

## ⏱️ When Services are RUNNING (in ~5-10 minutes)

### Step 1: Test Backend

```bash
curl https://ba37ecejh7.us-east-1.awsapprunner.com/api/health
```

Expected response:
```json
{"status":"ok","timestamp":"2025-10-03T..."}
```

### Step 2: Deploy Frontend to Amplify

**Manual deployment via AWS Console** (you don't have Amplify CLI access):

1. Go to: https://console.aws.amazon.com/amplify/home?region=us-east-1

2. Click **"New app"** → **"Host web app"**

3. **Connect Repository**:
   - Provider: **GitHub**
   - Authorize if needed
   - Repository: `wuwangzhang1216/DocTrans`
   - Branch: `main`
   - Click **Next**

4. **Build Settings** - Paste this exactly:

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
```

5. **Advanced Settings** → **Environment variables**:

Add this variable:
```
Name: NEXT_PUBLIC_API_URL
Value: https://ba37ecejh7.us-east-1.awsapprunner.com
```

6. Click **Next** → **Save and deploy**

7. Wait 5-10 minutes for build to complete

8. **Save your Amplify URL** (e.g., `https://main.d123abc.amplifyapp.com`)

### Step 3: Update Backend with Frontend URL

Once you have your Amplify URL, update the backend for CORS:

```bash
# Replace YOUR_AMPLIFY_URL with your actual Amplify URL
aws apprunner update-service \
  --service-arn arn:aws:apprunner:us-east-1:772081360719:service/translate-doc-backend/2b0af65830f54d24bc098358bfd54a67 \
  --region us-east-1 \
  --source-configuration '{
    "AuthenticationConfiguration": {
      "ConnectionArn": "arn:aws:apprunner:us-east-1:772081360719:connection/wuwangzhang1216/4fc5453d422144f7bb0dbe3d8c8980a5"
    },
    "AutoDeploymentsEnabled": true,
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/wuwangzhang1216/DocTrans",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "API",
        "CodeConfigurationValues": {
          "Runtime": "NODEJS_18",
          "BuildCommand": "cd translate-web-app/backend && npm install --production",
          "StartCommand": "cd translate-web-app/backend && node server.js",
          "Port": "3001",
          "RuntimeEnvironmentVariables": {
            "GEMINI_API_KEY": "AIzaSyBNUM6wm1YcLAbR44xUK-n6lA6tVmE95Os",
            "REDIS_URL": "rediss://default:ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU@stable-jennet-15065.upstash.io:6379",
            "REDIS_HOST": "stable-jennet-15065.upstash.io",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "ATrZAAIncDJlZGMzYjQwMzU2NjI0ZGE5OWIwZWQ4ZmM3NGM0NmEyOXAyMTUwNjU",
            "NODE_ENV": "production",
            "PORT": "3001",
            "WORKER_CONCURRENCY": "5",
            "JOB_TIMEOUT": "600000",
            "MAX_FILE_SIZE": "10485760",
            "FRONTEND_URL": "YOUR_AMPLIFY_URL"
          }
        }
      }
    }
  }'
```

---

## ✅ Final Test

Once everything is deployed:

1. Open your Amplify URL in browser
2. Upload a test document (PDF, DOCX, or PPTX)
3. Select target language (e.g., Chinese)
4. Click **Translate**
5. Watch the real-time progress bar
6. Download the translated file

---

## 📊 Deployment Summary

| Service | Status | URL |
|---------|--------|-----|
| Backend | 🟡 Building | https://ba37ecejh7.us-east-1.awsapprunner.com |
| Worker | 🟡 Building | https://zrizgtqpij.us-east-1.awsapprunner.com |
| Frontend | ⏳ Pending | (Deploy via Amplify Console) |

---

## 🆘 Need Help?

**View deployment logs:**
```bash
# Backend logs
aws logs tail /aws/apprunner/translate-doc-backend --follow --region us-east-1

# Worker logs
aws logs tail /aws/apprunner/translate-doc-worker --follow --region us-east-1
```

**Common issues:**
- Build fails → Check CloudWatch logs in App Runner console
- Can't connect → Verify environment variables
- Worker not processing → Check Redis connection

---

## 💰 Monthly Cost

- Backend: ~$30
- Worker: ~$50
- Frontend: ~$10
- **Total: ~$90/month**

---

**Check back in 5-10 minutes and test your backend!** 🚀
