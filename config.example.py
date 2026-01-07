import os

# 搜索方式选择（三选一）：
# 1. USE_DUCKDUCKGO=True：使用 DuckDuckGo（推荐，无需 API key，完全免费）
# 2. USE_SERPAPI=True：使用 SerpAPI（需要 API key）
# 3. 两者都为 False：使用 Google Custom Search API（需要 API key 和 CSE ID）

# 从环境变量读取配置（用于生产环境），如果没有则使用默认值
USE_DUCKDUCKGO = os.environ.get("USE_DUCKDUCKGO", "False").lower() == "true"

USE_SERPAPI = os.environ.get("USE_SERPAPI", "False").lower() == "true"
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "YOUR_SERPAPI_KEY")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "YOUR_GOOGLE_CSE_ID")

# 搜索关键词，只搜索与机器人、自动驾驶相关的 VLA 内容
SEARCH_QUERY = os.environ.get(
    "SEARCH_QUERY",
    '(VLA OR "vision language action") AND (robot OR robotics OR "autonomous driving" OR "self-driving" OR "autonomous vehicle" OR "robotic manipulation" OR "embodied AI" OR "robot control")'
)

# 只抓取从该日期开始的内容（含该月），格式 YYYY-MM-DD
START_DATE = os.environ.get("START_DATE", "2025-10-01")

# 重点关注站点，Google 查询中会自动加上 site:xxx 过滤
TARGET_SITES = [
    "zhihu.com",
    "github.com",
    "huggingface.co",
    "arxiv.org",
]

# 每天最多抓取的结果数（每个站点），按搜索相关性排序显示 top 30
MAX_RESULTS_PER_SITE = int(os.environ.get("MAX_RESULTS_PER_SITE", "30"))

# 数据存储目录
DATA_DIR = os.environ.get("DATA_DIR", "data")

