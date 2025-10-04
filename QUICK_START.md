# Quick Start - AWS Deployment

## ✅ What's Ready

Your code is on GitHub: **https://github.com/wuwangzhang1216/DocTrans**

All configuration files are in place:
- ✅ Backend Dockerfile and apprunner.yaml
- ✅ Worker Dockerfile and apprunner.yaml
- ✅ Frontend amplify.yml
- ✅ All environment variables documented

## 🚀 Deploy Now (3 Services)

### 1️⃣ Deploy Backend (5-10 min)

**URL**: https://console.aws.amazon.com/apprunner/home?region=us-east-1

1. Click **"Create service"**
2. Source: **"Source code repository"**
3. Create GitHub connection → Connect `wuwangzhang1216/DocTrans`
4. Branch: `main`
5. Config file: `translate-web-app/backend/apprunner.yaml`
6. Service name: `translate-doc-backend`
7. Add environment variables (see below)
8. **Create & deploy**
9. **📝 SAVE THE URL!**

### 2️⃣ Deploy Worker (5-10 min)

**URL**: https://console.aws.amazon.com/apprunner/home?region=us-east-1

1. Click **"Create service"**
2. Use existing GitHub connection from step 1
3. Repository: `wuwangzhang1216/DocTrans`
4. Branch: `main`
5. Config file: `translate-web-app/worker/apprunner.yaml`
6. Service name: `translate-doc-worker`
7. **CPU: 2 vCPU, Memory: 4 GB** (worker needs more resources)
8. Add environment variables (see below)
9. **Create & deploy**

### 3️⃣ Deploy Frontend (5-10 min)

**URL**: https://console.aws.amazon.com/amplify/home?region=us-east-1

1. Click **"New app"** → **"Host web app"**
2. Connect GitHub → `wuwangzhang1216/DocTrans`
3. Branch: `main`
4. Build settings - paste this YAML:

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

5. **Environment variable** (IMPORTANT!):
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://YOUR-BACKEND-URL` (from step 1)
6. **Save and deploy**

---

## 🔐 Environment Variables

### Backend & Worker (Same for both)

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

### Frontend

```
NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-URL-FROM-APP-RUNNER
```

---

## 🔄 Final Step: Link Frontend to Backend

After all 3 services are deployed:

1. Go to App Runner backend service
2. Configuration → Edit environment variables
3. Add: `FRONTEND_URL` = `https://your-amplify-url`
4. Save (auto-redeploys)

---

## ✅ Test Your App

1. Open Amplify URL in browser
2. Upload a document (PDF, DOCX, PPTX)
3. Select target language
4. Click translate
5. Watch real-time progress
6. Download translated file

---

## 📊 Monitor Deployments

- **App Runner**: https://console.aws.amazon.com/apprunner/home?region=us-east-1
- **Amplify**: https://console.aws.amazon.com/amplify/home?region=us-east-1
- **Logs**: CloudWatch Logs in each service

---

## 🆘 Troubleshooting

**Backend build fails?**
- Check CloudWatch logs
- Verify all env vars are set

**Worker build fails?**
- Increase to 2 vCPU, 4 GB memory
- Check Python dependencies in logs

**Frontend can't connect?**
- Verify `NEXT_PUBLIC_API_URL` matches backend URL
- Check backend has `FRONTEND_URL` set

**Jobs not processing?**
- Check worker is running
- Verify Redis connection (REDIS_URL)
- Check GEMINI_API_KEY is valid

---

## 💰 Estimated Cost

- Backend: ~$30/month
- Worker: ~$50/month
- Frontend: ~$10/month
- **Total**: ~$90/month

---

## 📚 Need More Details?

See **DEPLOY_STEPS.md** for detailed step-by-step instructions with screenshots references.

---

**Ready to deploy? Start with the Backend! 🚀**
