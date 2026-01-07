## VLA Daily Tracker

这个项目每天使用 Google 搜索来抓取 “VLA” 相关内容，重点关注知乎、GitHub、HuggingFace (hf) 和 arXiv，然后自动生成一个网页展示每日更新摘要。

### 功能概览

- **每天定时**：通过定时任务（cron 或系统任务计划）每天执行一次抓取。
- **Google 搜索**：使用 Google Custom Search API 或第三方搜索 API（例如 SerpAPI）按站点过滤搜索结果。
- **站点过滤**：重点收集来自知乎、GitHub、HuggingFace、arXiv 的结果。
- **自动总结**：对每天新抓取的链接和摘要进行简单整理与聚合。
- **网页展示**：通过 Flask Web 服务展示一个按日期分组的更新列表页面。

### 项目结构

- `config.example.py`：配置示例（API Key、搜索引擎 ID、搜索关键字等）。
- `config.py`：你的实际配置文件（需要你根据示例复制并修改，不会被提交）。
- `crawler.py`：调用搜索 API，抓取并过滤结果。
- `summarizer.py`：对抓取的结果做简单整合与“摘要”。
- `storage.py`：负责将每日数据存储为 JSON 文件并读取。
- `app.py`：Flask Web 应用，展示每日更新列表。
- `requirements.txt`：Python 依赖。
- `run_daily.py`：每天执行一次的入口脚本，串联抓取、总结和存储。

### 使用步骤

1. **创建虚拟环境并安装依赖**

```bash
cd /home/mi/workspace/cursor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **配置 `config.py`**

复制示例文件并填写你自己的配置：

```bash
cp config.example.py config.py
```

然后编辑 `config.py`，填入：

- Google Custom Search API Key 或 SerpAPI Key
- 搜索引擎 ID（如果使用 CSE）
- 搜索关键词（比如 `"VLA" 或 "vision language action"`）

#### 如何获取 Google Custom Search API Key（推荐）

1. **访问 Google Cloud Console**
   - 打开 https://console.cloud.google.com/
   - 创建新项目或选择现有项目

2. **启用 Custom Search API**
   - 在左侧菜单找到 "API和服务" > "库"
   - 搜索 "Custom Search API"
   - 点击启用

3. **创建 API Key**
   - 进入 "API和服务" > "凭据"
   - 点击 "创建凭据" > "API 密钥"
   - 复制生成的 API Key

4. **创建自定义搜索引擎（CSE）**
   - 访问 https://programmablesearchengine.google.com/
   - 点击 "添加" 创建新的搜索引擎
   - **重要**：在 "要搜索的网站" 中选择 "搜索整个网络"（Search the entire web）
   - 创建后，在 "控制面板" 中找到 "搜索引擎 ID"（格式类似：`017576662512468239146:omuauf_lfve`）

5. **配置到 `config.py`**
   ```python
   USE_DUCKDUCKGO = False  # 关闭 DuckDuckGo
   GOOGLE_API_KEY = "你的API_KEY"
   GOOGLE_CSE_ID = "你的搜索引擎ID"
   ```

**注意**：Google Custom Search API 免费额度为每天 100 次查询，对于每天抓取 4 个站点来说完全够用。

3. **手动测试抓取与生成**

```bash
source venv/bin/activate
python run_daily.py
python app.py
```

访问 `http://127.0.0.1:5000` 查看网页是否能显示当日更新。

4. **设置每天自动运行（以 Linux cron 为例）**

编辑 crontab：

```bash
crontab -e
```

添加类似：

```bash
0 8 * * * /usr/bin/bash -lc 'cd /home/mi/workspace/cursor && source venv/bin/activate && python run_daily.py >> logs/daily.log 2>&1'
```

表示每天早上 8 点自动抓取一次。

5. **部署 Web 服务**

开发环境下可以直接：

```bash
source venv/bin/activate
python app.py
```

生产环境可以用 gunicorn + Nginx 或其它反向代理，具体可根据你现有环境定制。

---

后续如果你希望接入更智能的自然语言摘要（比如用大模型将每天的链接内容做更高质量总结），可以在 `summarizer.py` 中接入对应 API。

