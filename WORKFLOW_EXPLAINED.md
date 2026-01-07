# GitHub Actions 工作流详细说明

本文档详细解释 `.github/workflows/deploy.yml` 中每个步骤的作用。

## 完整工作流步骤

### 1. 触发条件

```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # 每天 UTC 8:00 自动运行
  workflow_dispatch:     # 允许手动触发
  push:
    branches:
      - main             # 推送到 main 分支时也触发
```

### 2. 执行步骤详解

#### 步骤 1: Checkout code
```yaml
- name: Checkout code
  uses: actions/checkout@v3
```
**作用**: 将你的 GitHub 仓库代码检出到 Actions 运行环境中。

#### 步骤 2: Set up Python
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'
```
**作用**: 安装 Python 3.11 运行环境。

#### 步骤 3: Install dependencies
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```
**作用**: 安装项目依赖（Flask、requests、gunicorn 等）。

#### 步骤 4: Run daily crawler ⭐
```yaml
- name: Run daily crawler
  env:
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    GOOGLE_CSE_ID: ${{ secrets.GOOGLE_CSE_ID }}
    SEARCH_QUERY: ${{ secrets.SEARCH_QUERY }}
    MAX_RESULTS_PER_SITE: ${{ secrets.MAX_RESULTS_PER_SITE }}
    DATA_DIR: data
    USE_DUCKDUCKGO: "False"
    USE_SERPAPI: "False"
  run: |
    python run_daily.py
```
**作用**: 
- 运行 `run_daily.py` 脚本
- 从环境变量读取 API Key 等配置
- 抓取知乎、GitHub、HuggingFace、arXiv 的 VLA 相关内容
- 获取 arXiv 论文摘要并翻译成中文
- 将数据保存到 `data/` 目录（JSON 格式）

**输出**: `data/YYYY-MM-DD.json` 文件

#### 步骤 5: Generate static HTML ⭐
```yaml
- name: Generate static HTML
  run: |
    python generate_static.py
```
**作用**:
- 运行 `generate_static.py` 脚本
- 读取 `data/` 目录中的数据
- 使用 Flask 模板引擎渲染 HTML
- 生成静态 HTML 文件到 `docs/` 目录

**输出**: `docs/index.html` 文件

#### 步骤 6: Deploy to GitHub Pages
```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs
    cname: false
    keep_files: false
```
**作用**:
- 将 `docs/` 目录的内容推送到 `gh-pages` 分支
- GitHub Pages 会自动从 `gh-pages` 分支读取并发布网站

## 环境变量说明

在步骤 4 中，需要设置以下环境变量（通过 GitHub Secrets）：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `GOOGLE_API_KEY` | Google Custom Search API Key | `AIzaSy...` |
| `GOOGLE_CSE_ID` | Google 自定义搜索引擎 ID | `0397694405284452f` |
| `SEARCH_QUERY` | 搜索关键词 | `(VLA OR "vision language action") AND ...` |
| `MAX_RESULTS_PER_SITE` | 每个站点最多结果数 | `30` |

## 如何查看执行日志

1. 进入 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择最新的工作流运行
4. 点击 **deploy** job
5. 展开每个步骤查看详细日志

## 常见问题

### Q: 为什么需要两个脚本？

A: 
- `run_daily.py`: 负责数据抓取（需要 API Key，会调用外部服务）
- `generate_static.py`: 负责生成静态 HTML（只需要读取本地数据文件）

分离的好处：
- 可以单独测试每个步骤
- 如果抓取失败，可以手动运行生成脚本
- 代码结构更清晰

### Q: 数据会保存多久？

A: GitHub Actions 运行环境是临时的，每次运行都会重新创建。但：
- 抓取的数据会保存到 `data/` 目录（在运行期间）
- 生成的 HTML 会部署到 `gh-pages` 分支（永久保存）
- 每次运行都会重新抓取最新数据

### Q: 可以修改运行时间吗？

A: 可以！编辑 `.github/workflows/deploy.yml` 中的 cron 表达式：
```yaml
schedule:
  - cron: '0 8 * * *'  # UTC 8:00 = 北京时间 16:00
```

Cron 格式：`分钟 小时 日 月 星期`
- `0 8 * * *` = 每天 UTC 8:00
- `0 0 * * *` = 每天 UTC 0:00（北京时间 8:00）
- `0 */6 * * *` = 每 6 小时一次

### Q: 可以手动触发吗？

A: 可以！在 Actions 页面：
1. 选择 "Deploy to GitHub Pages" workflow
2. 点击 "Run workflow"
3. 选择分支（通常是 main）
4. 点击绿色的 "Run workflow" 按钮

## 调试技巧

如果工作流失败：

1. **查看日志**: 在 Actions 页面查看失败步骤的日志
2. **本地测试**: 在本地运行相同的命令
   ```bash
   python run_daily.py
   python generate_static.py
   ```
3. **检查 Secrets**: 确保所有 Secrets 都已正确设置
4. **检查 API 配额**: 确保 Google API 有足够的配额
