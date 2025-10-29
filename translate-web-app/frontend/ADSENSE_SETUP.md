# Google AdSense 设置指南

本指南将帮助您在翻译应用中设置 Google AdSense 广告。

## 📋 目录

1. [申请 Google AdSense 账号](#申请-google-adsense-账号)
2. [配置广告单元](#配置广告单元)
3. [在项目中配置](#在项目中配置)
4. [测试广告显示](#测试广告显示)
5. [故障排除](#故障排除)

---

## 1. 申请 Google AdSense 账号

### 前提条件

- 有效的 Google 账号
- 网站已部署上线（需要公开访问的 URL）
- 网站内容符合 [AdSense 计划政策](https://support.google.com/adsense/answer/48182)

### 申请步骤

#### 步骤 1: 访问 AdSense 官网
访问 [https://www.google.com/adsense/](https://www.google.com/adsense/) 并点击"开始使用"。

#### 步骤 2: 填写申请信息
- 输入您的网站 URL（例如：https://yourdomain.com）
- 填写您的电子邮件地址
- 同意 AdSense 条款和条件

#### 步骤 3: 验证网站所有权
Google 会要求您在网站的 `<head>` 标签中添加一段验证代码。

**好消息：** 本项目已经自动集成了 AdSense 代码！您只需：
1. 获得 AdSense 发布商 ID（ca-pub-xxxxxxxxxxxxxxxx）
2. 在 `.env.local` 中配置该 ID
3. 部署到生产环境
4. 在 AdSense 控制台中点击"验证"

#### 步骤 4: 等待审核
- Google 通常会在 1-3 个工作日内审核您的申请
- 审核期间请确保：
  - 网站可以正常访问
  - 网站有足够的原创内容
  - 网站符合 AdSense 政策

---

## 2. 配置广告单元

### 获取发布商 ID

1. 登录 [AdSense 控制台](https://www.google.com/adsense/)
2. 在左侧菜单中点击"广告" → "概览"
3. 您的发布商 ID 显示在顶部（格式：`ca-pub-xxxxxxxxxxxxxxxx`）

### 创建广告单元（可选）

虽然本项目使用的是**自动广告**（无需特定广告单元 ID），但您也可以创建自定义广告单元：

1. 在 AdSense 控制台中点击"广告" → "按广告单元"
2. 点击"新建广告单元"
3. 选择"展示广告"
4. 配置广告：
   - **类型**: 响应式
   - **名称**: Translation Progress Ad（或任意名称）
5. 点击"创建"并复制广告单元 ID

---

## 3. 在项目中配置

### 步骤 1: 创建 `.env.local` 文件

在 `frontend/` 目录下创建 `.env.local` 文件：

```bash
cd D:\work\translate-doc\translate-web-app\frontend
cp .env.local.example .env.local
```

### 步骤 2: 配置 AdSense ID

编辑 `.env.local` 文件，填入您的 AdSense 发布商 ID：

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_ADSENSE_ID=ca-pub-1234567890123456
```

**将 `ca-pub-1234567890123456` 替换为您的真实发布商 ID！**

### 步骤 3: 配置广告单元 ID（可选）

如果您创建了自定义广告单元，可以在 `GoogleAd.tsx` 组件中传入 `adSlot` 属性：

```tsx
<GoogleAd
  show={job.status === 'processing'}
  adFormat="auto"
  adSlot="1234567890"  // 👈 添加您的广告单元 ID
  minHeight="120px"
  className="my-4"
/>
```

### 步骤 4: 重启开发服务器

```bash
npm run dev
```

---

## 4. 测试广告显示

### 本地测试

在开发环境中，广告可能不会立即显示或显示为空白。这是正常的，因为：
- AdSense 需要验证网站域名
- 本地 localhost 无法通过 AdSense 审核

### 生产环境测试

1. 部署到生产环境（Heroku、Vercel 等）
2. 确保 `.env.local` 中的环境变量也在生产环境中配置
3. 访问网站并开始一个翻译任务
4. 当翻译进入 **processing** 状态时，广告应该显示在进度条上方

### 广告显示时机

根据配置，广告仅在以下情况显示：
- ✅ 翻译状态为 **processing**（处理中）
- ✅ 已正确配置 `NEXT_PUBLIC_ADSENSE_ID`
- ❌ 翻译状态为 queued、completed 或 failed 时不显示

---

## 5. 故障排除

### 问题 1: 广告不显示

**可能原因：**
- AdSense ID 未配置或配置错误
- 网站未通过 AdSense 审核
- 浏览器安装了广告拦截插件

**解决方法：**
1. 检查 `.env.local` 中的 `NEXT_PUBLIC_ADSENSE_ID` 是否正确
2. 打开浏览器开发者工具（F12），检查控制台是否有错误信息
3. 确认网站已通过 AdSense 审核
4. 暂时禁用广告拦截插件进行测试

### 问题 2: 显示空白区域

**可能原因：**
- AdSense 仍在加载广告
- 没有合适的广告匹配

**解决方法：**
- 等待几秒钟，广告可能正在加载
- 检查网络请求，确认 `pagead2.googlesyndication.com` 可以访问
- 新网站可能需要一段时间才能获得广告填充

### 问题 3: 控制台显示 "adsbygoogle.push() error"

**可能原因：**
- AdSense 脚本未正确加载

**解决方法：**
1. 检查 `layout.tsx` 中的 Script 标签是否正确
2. 确认网络可以访问 Google AdSense CDN
3. 清除浏览器缓存并重新加载

### 问题 4: 网站未通过 AdSense 审核

**可能原因：**
- 内容不足
- 网站导航不清晰
- 违反 AdSense 政策

**解决方法：**
- 确保网站有足够的原创内容
- 添加"关于我们"、"隐私政策"、"联系方式"等页面
- 改进网站导航和用户体验
- 检查并修正违反政策的内容

---

## 6. 进阶配置

### 自定义广告样式

您可以在 `GoogleAd.tsx` 组件中自定义样式：

```tsx
<GoogleAd
  show={job.status === 'processing'}
  adFormat="auto"
  minHeight="150px"      // 调整最小高度
  className="my-6 px-4"  // 自定义间距
/>
```

### 在其他位置添加广告

您可以在任何组件中导入并使用 `GoogleAd` 组件：

```tsx
import GoogleAd from '@/components/GoogleAd'

export default function YourComponent() {
  return (
    <div>
      <h1>Your Content</h1>
      <GoogleAd show={true} adFormat="auto" />
    </div>
  )
}
```

### 禁用广告（临时）

如果需要临时禁用广告，只需在 `.env.local` 中注释掉 AdSense ID：

```env
# NEXT_PUBLIC_ADSENSE_ID=ca-pub-1234567890123456
```

---

## 📚 相关资源

- [Google AdSense 官方网站](https://www.google.com/adsense/)
- [AdSense 帮助中心](https://support.google.com/adsense/)
- [AdSense 政策中心](https://support.google.com/adsense/answer/48182)
- [Next.js Script 组件文档](https://nextjs.org/docs/pages/api-reference/components/script)

---

## 💡 提示

- **收入优化**: 广告位置和大小会影响点击率和收入。根据数据分析调整广告配置。
- **用户体验**: 确保广告不会过度干扰用户的翻译体验。
- **合规性**: 定期检查并遵守 AdSense 政策，避免账号被暂停。
- **分析**: 使用 Google Analytics 配合 AdSense 分析广告效果。

---

**祝您广告收入丰厚！** 🎉
