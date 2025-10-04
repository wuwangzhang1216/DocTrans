# 🚀 Deployment In Progress

## ✅ Services Created

### 1. Backend Service
- **Name**: `translate-doc-backend`
- **Status**: 🟡 Building and deploying...
- **URL**: https://ba37ecejh7.us-east-1.awsapprunner.com
- **Health Check**: https://ba37ecejh7.us-east-1.awsapprunner.com/api/health
- **Resources**: 1 vCPU, 2 GB RAM
- **Console**: https://us-east-1.console.aws.amazon.com/apprunner/home?region=us-east-1#/services/translate-doc-backend

### 2. Worker Service
- **Name**: `translate-doc-worker`
- **Status**: 🟡 Building and deploying...
- **URL**: https://zrizgtqpij.us-east-1.awsapprunner.com
- **Resources**: 2 vCPU, 4 GB RAM
- **Console**: https://us-east-1.console.aws.amazon.com/apprunner/home?region=us-east-1#/services/translate-doc-worker

### 3. Frontend (Next Step)
- **Platform**: AWS Amplify
- **Status**: ⏳ Waiting for backend to complete
- **Will use**: Backend URL above

---

## ⏱️ Deployment Timeline

- **Started**: Just now
- **Expected completion**: 5-10 minutes
- **Current step**: Building Docker images and deploying

---

## 📊 Monitor Progress

Run this command to check status:

```bash
aws apprunner describe-service --service-arn arn:aws:apprunner:us-east-1:772081360719:service/translate-doc-backend/2b0af65830f54d24bc098358bfd54a67 --region us-east-1 --query 'Service.{Name:ServiceName,Status:Status}' --output table
```

Or visit the App Runner console:
https://console.aws.amazon.com/apprunner/home?region=us-east-1

---

## 🔄 Next Steps

Once both services show `RUNNING` status:

### 1. Test Backend
```bash
curl https://ba37ecejh7.us-east-1.awsapprunner.com/api/health
```

Expected response:
```json
{"status":"ok","timestamp":"..."}
```

### 2. Deploy Frontend to Amplify

Go to: https://console.aws.amazon.com/amplify/home?region=us-east-1

1. Click **"New app"** → **"Host web app"**
2. Select **GitHub** → Connect to `wuwangzhang1216/DocTrans`
3. Branch: `main`
4. Build settings:

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

5. **Add environment variable**:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://ba37ecejh7.us-east-1.awsapprunner.com`

6. Click **"Save and deploy"**

### 3. Update Backend CORS

After Amplify deploys, update backend with frontend URL:

```bash
# Get your Amplify URL first, then run:
aws apprunner update-service \
  --service-arn arn:aws:apprunner:us-east-1:772081360719:service/translate-doc-backend/2b0af65830f54d24bc098358bfd54a67 \
  --region us-east-1 \
  --source-configuration '{
    "CodeRepository": {
      "CodeConfiguration": {
        "CodeConfigurationValues": {
          "RuntimeEnvironmentVariables": {
            "FRONTEND_URL": "https://your-amplify-url.amplifyapp.com"
          }
        }
      }
    }
  }'
```

---

## 🆘 Troubleshooting

If deployment fails, check CloudWatch logs:

```bash
# View logs
aws logs tail /aws/apprunner/translate-doc-backend --follow --region us-east-1
```

Common issues:
- **Build timeout**: Increase instance size
- **Dependency errors**: Check package.json
- **Connection errors**: Verify Redis credentials

---

## 💰 Current Cost

Running costs (while deployed):
- Backend: ~$30/month
- Worker: ~$50/month
- Total so far: ~$80/month
- Frontend (Amplify): +$10/month when added

---

**Status will auto-update as deployment progresses...**
