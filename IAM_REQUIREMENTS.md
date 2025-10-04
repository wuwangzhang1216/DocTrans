# IAM Permissions Required for AWS Deployment

## Current Issue

Your AWS user (`arn:aws:iam::772081360719:user/steve`) doesn't have permission to create IAM roles, which are required for automated deployment.

## Required IAM Permissions

To deploy using the automated script or AWS CLI, your user needs these permissions:

### 1. IAM Permissions (For creating service roles)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "iam:TagRole"
      ],
      "Resource": [
        "arn:aws:iam::772081360719:role/AppRunnerECRAccessRole"
      ]
    }
  ]
}
```

### 2. App Runner Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apprunner:CreateService",
        "apprunner:UpdateService",
        "apprunner:ListServices",
        "apprunner:DescribeService",
        "apprunner:DeleteService",
        "apprunner:TagResource",
        "apprunner:CreateConnection",
        "apprunner:ListConnections"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. ECR Permissions (If using Docker locally)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DescribeRepositories",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. Amplify Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "amplify:CreateApp",
        "amplify:CreateBranch",
        "amplify:UpdateApp",
        "amplify:StartJob",
        "amplify:GetApp",
        "amplify:ListApps",
        "amplify:DeleteApp"
      ],
      "Resource": "*"
    }
  ]
}
```

## Pre-Created Role Alternative

Instead of creating the role via CLI, your AWS administrator can pre-create this role:

### Role Name: `AppRunnerECRAccessRole`

**Trust Policy:**
```json
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
```

**Attached Policy:**
- AWS Managed Policy: `arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess`

## Solutions

### Option 1: Request IAM Permissions (Recommended for CLI)

Ask your AWS administrator to attach a policy with the permissions above to user `steve`.

### Option 2: Use Pre-Created Roles (Easiest)

Ask your AWS administrator to:
1. Create the `AppRunnerECRAccessRole` with the trust policy above
2. Attach the `AWSAppRunnerServicePolicyForECRAccess` policy
3. Then you can deploy via CLI without creating new roles

### Option 3: Use AWS Console (No IAM permissions needed)

**This is what I recommend for you!** ✅

The AWS Console handles role creation automatically. Follow the guides:
- [QUICK_START.md](QUICK_START.md)
- [DEPLOY_STEPS.md](DEPLOY_STEPS.md)

When deploying via Console:
- App Runner will automatically create needed service roles
- Amplify will automatically create needed build roles
- No manual IAM work required!

## Minimal IAM Policy for Console Deployment

If using AWS Console, you need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apprunner:*",
        "amplify:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::772081360719:role/aws-service-role/apprunner.amazonaws.com/AWSServiceRoleForAppRunner"
    }
  ]
}
```

## Check Your Current Permissions

Run this to see what you have:

```bash
aws iam get-user --user-name steve
aws iam list-attached-user-policies --user-name steve
aws iam list-user-policies --user-name steve
```

## Recommendation

**Use the AWS Console** (Option 3) - it's the simplest approach and doesn't require additional IAM permissions. The Console will handle all service role creation automatically when you create App Runner and Amplify services.

Follow [QUICK_START.md](QUICK_START.md) to get started! 🚀
