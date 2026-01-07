# GitHub Pages 部署指南

本指南将帮助你将 VLA 追踪网站部署到 GitHub Pages，完全免费且无需服务器！

## 工作原理

GitHub Pages 只支持静态网站，所以我们需要：
1. 使用 GitHub Actions 定期运行抓取脚本（`run_daily.py`）
2. 生成静态 HTML 文件（`generate_static.py`）
3. 自动部署到 GitHub Pages

### GitHub Actions 工作流详解

当你提交代码或每天定时触发时，`.github/workflows/deploy.yml` 会自动执行以下步骤：

1. **Checkout code** - 检出代码到运行环境
2. **Set up Python** - 设置 Python 3.11 环境
3. **Install dependencies** - 安装 requirements.txt 中的依赖
4. **Run daily crawler** - **运行 `python run_daily.py`** 抓取最新数据
5. **Generate static HTML** - **运行 `python generate_static.py`** 生成静态 HTML 文件到 `docs/` 目录
6. **Deploy to GitHub Pages** - 将 `docs/` 目录部署到 GitHub Pages

## 部署步骤

### 步骤 1：准备代码

确保所有文件都已提交到 GitHub：

```bash
git add .
git commit -m "Add GitHub Pages deployment"
git push origin main
```

### 步骤 2：设置 GitHub Secrets

在 GitHub 仓库页面：

1. 点击 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**，添加以下 secrets：

   - `GOOGLE_API_KEY`: 你的 Google API Key
   - `GOOGLE_CSE_ID`: 你的搜索引擎 ID
   - `SEARCH_QUERY`: `(VLA OR "vision language action") AND (robot OR robotics OR "autonomous driving" OR "self-driving" OR "autonomous vehicle" OR "robotic manipulation" OR "embodied AI" OR "robot control")`
   - `MAX_RESULTS_PER_SITE`: `30`

### 步骤 3：启用 GitHub Pages

**重要**：必须正确配置，否则会显示 README 而不是网站内容！

1. 在仓库页面，点击 **Settings** → **Pages**
2. 在 **Source** 部分：
   - 选择 **Deploy from a branch**
   - Branch: 选择 `gh-pages`（这是 GitHub Actions 自动创建的）
   - Folder: 选择 `/ (root)`（不是 `/docs`）
3. 点击 **Save**

**注意**：
- 如果看不到 `gh-pages` 分支，先完成步骤 4（触发部署），部署成功后会自动创建
- 确保选择的是 `gh-pages` 分支，不是 `main` 分支
- Folder 必须选择 `/ (root)`，因为 GitHub Actions 会将 `docs/` 目录的内容推送到 `gh-pages` 分支的根目录

### 步骤 4：手动触发首次部署

1. 在仓库页面，点击 **Actions** 标签
2. 选择 **Deploy to GitHub Pages** workflow
3. 点击 **Run workflow** → **Run workflow**
4. 等待部署完成（大约 2-5 分钟）

### 步骤 5：访问网站

部署完成后，你的网站将在以下地址可用：
```
https://你的用户名.github.io/vla-tracker/
```

例如：`https://Miracle1991.github.io/vla-tracker/`

## 自动更新

GitHub Actions 会：
- **每天 UTC 8:00**（北京时间 16:00）自动运行抓取和部署
- 你也可以在 **Actions** 页面手动触发

## 文件说明

- `run_daily.py`: 每日抓取脚本，从各个网站抓取 VLA 相关内容
- `generate_static.py`: 生成静态 HTML 文件的脚本，将 Flask 模板渲染为静态 HTML
- `.github/workflows/deploy.yml`: GitHub Actions 工作流配置，自动执行上述两个脚本
- `docs/`: 生成的静态文件目录（由 `generate_static.py` 自动创建）

### 工作流执行顺序

```
GitHub Actions 触发
    ↓
安装依赖 (pip install -r requirements.txt)
    ↓
运行抓取脚本 (python run_daily.py)
    ├─ 从 Google 搜索抓取数据
    ├─ 获取 arXiv 论文摘要并翻译
    └─ 保存到 data/ 目录
    ↓
生成静态 HTML (python generate_static.py)
    ├─ 读取 data/ 目录中的数据
    ├─ 使用 Flask 模板渲染 HTML
    └─ 保存到 docs/index.html
    ↓
部署到 GitHub Pages
    └─ 将 docs/ 目录推送到 gh-pages 分支
```

## 注意事项

1. **首次部署**：需要手动触发一次，之后会自动运行
2. **数据持久化**：GitHub Actions 运行时的数据是临时的，但生成的 HTML 会保存
3. **更新频率**：默认每天更新一次，可以在 `.github/workflows/deploy.yml` 中修改 cron 时间
4. **API 限制**：确保 Google API 有足够的配额

## 自定义域名（可选）

如果你想使用自己的域名：

1. 在 `docs/` 目录创建 `CNAME` 文件，内容是你的域名
2. 在 GitHub Pages 设置中添加自定义域名

## 故障排除

### 问题：Actions 运行失败

- 检查 Secrets 是否正确设置
- 查看 Actions 日志找出错误原因
- 确保 API Key 有效且有足够配额

### 问题：网站显示空白

- 检查 `docs/` 目录是否有文件
- 确认 GitHub Pages 设置正确
- 等待几分钟让更改生效

### 问题：数据没有更新

- 检查 Actions 是否正常运行
- 查看 cron 时间设置
- 可以手动触发一次更新

## 优势

✅ **完全免费** - GitHub Pages 和 Actions 都有免费额度  
✅ **自动更新** - 每天自动抓取和部署  
✅ **无需服务器** - 纯静态网站  
✅ **全球 CDN** - GitHub Pages 自带 CDN 加速  
✅ **HTTPS** - 自动提供 SSL 证书  

享受你的免费网站吧！🎉
