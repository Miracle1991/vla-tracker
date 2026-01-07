# 部署指南

本指南将帮助你将这个 VLA 追踪网站部署到云端，让其他人也能访问。

## 推荐方案：使用 Render（免费且简单）

### 1. 准备工作

#### 1.1 创建 GitHub 仓库

```bash
# 在项目目录下初始化 Git
git init
git add .
git commit -m "Initial commit"

# 在 GitHub 上创建新仓库，然后推送
git remote add origin https://github.com/你的用户名/vla-tracker.git
git branch -M main
git push -u origin main
```

**重要**：确保 `config.py` 在 `.gitignore` 中，不要提交包含 API Key 的配置文件！

#### 1.2 在 Render 上设置环境变量

由于 `config.py` 不会被提交，你需要在 Render 上设置环境变量：

1. 登录 [Render](https://render.com)（可以用 GitHub 账号登录）
2. 创建新的 "Web Service"
3. 连接你的 GitHub 仓库
4. 在 "Environment" 标签页添加以下环境变量：

```
GOOGLE_API_KEY=你的Google_API_Key
GOOGLE_CSE_ID=你的搜索引擎ID
SEARCH_QUERY=(VLA OR "vision language action") AND (robot OR robotics OR "autonomous driving" OR "self-driving" OR "autonomous vehicle" OR "robotic manipulation" OR "embodied AI" OR "robot control")
MAX_RESULTS_PER_SITE=30
DATA_DIR=data
USE_DUCKDUCKGO=False
USE_SERPAPI=False
```

#### 1.3 修改代码以支持环境变量

我已经修改了代码，但你需要确保 `config.py` 可以从环境变量读取：

在 `config.py` 开头添加：

```python
import os

# 从环境变量读取配置（用于生产环境）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "YOUR_CUSTOM_SEARCH_ENGINE_ID")
SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "(VLA OR \"vision language action\") AND (robot OR robotics OR \"autonomous driving\" OR \"self-driving\" OR \"autonomous vehicle\" OR \"robotic manipulation\" OR \"embodied AI\" OR \"robot control\")")
MAX_RESULTS_PER_SITE = int(os.environ.get("MAX_RESULTS_PER_SITE", "30"))
DATA_DIR = os.environ.get("DATA_DIR", "data")
USE_DUCKDUCKGO = os.environ.get("USE_DUCKDUCKGO", "False").lower() == "true"
USE_SERPAPI = os.environ.get("USE_SERPAPI", "False").lower() == "true"
```

#### 1.4 部署设置

在 Render 上：
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Plan**: 选择 Free 计划

### 2. 设置定时任务（可选）

如果你想让网站每天自动更新数据，可以：

#### 方案 A：使用 Render Cron Jobs（需要付费计划）

#### 方案 B：使用外部 Cron 服务

使用 [cron-job.org](https://cron-job.org) 或 [EasyCron](https://www.easycron.com/)：

1. 创建一个 HTTP 请求，每天访问：`https://你的网站地址/run-daily`
2. 需要在 `app.py` 中添加一个路由来触发抓取

#### 方案 C：在本地服务器运行定时任务

在你的电脑或服务器上设置 cron，定期运行 `run_daily.py`，然后将数据同步到云端。

---

## 其他部署方案

### 方案 2：Railway

1. 登录 [Railway](https://railway.app)
2. 连接 GitHub 仓库
3. 设置环境变量（同 Render）
4. 部署

### 方案 3：Heroku

1. 安装 Heroku CLI
2. 登录并创建应用
3. 设置环境变量
4. 部署

### 方案 4：自己的服务器

如果你有自己的服务器（VPS），可以：

```bash
# 安装依赖
pip install -r requirements.txt

# 使用 gunicorn 运行
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 或使用 systemd 服务
# 创建 /etc/systemd/system/vla-tracker.service
```

---

## 安全提示

1. **永远不要提交 `config.py`** - 它包含你的 API Key
2. **使用环境变量** - 在生产环境中使用环境变量存储敏感信息
3. **定期更新** - 定期检查并更新依赖包
4. **限制访问** - 如果需要，可以添加身份验证

---

## 常见问题

### Q: 数据存储在哪里？

A: 数据存储在 `data/` 目录下的 JSON 文件中。在 Render 等平台上，这个目录是临时的，重启后会丢失。如果需要持久化存储，可以考虑：
- 使用数据库（PostgreSQL、MongoDB）
- 使用云存储（AWS S3、Google Cloud Storage）
- 定期备份到 GitHub

### Q: 如何更新数据？

A: 可以：
1. 手动运行 `run_daily.py`（如果服务器支持 SSH）
2. 通过 API 端点触发（需要添加路由）
3. 使用定时任务服务

### Q: 网站访问速度慢？

A: 可能原因：
- 免费计划资源有限
- 数据文件较大
- 可以考虑使用 CDN 或优化数据加载

---

## 下一步

1. 按照上述步骤部署到 Render
2. 测试网站是否正常访问
3. 设置定时任务自动更新数据
4. 分享链接给其他人！
