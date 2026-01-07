# 搜索方式选择（三选一）：
# 1. USE_DUCKDUCKGO=True：使用 DuckDuckGo（推荐，无需 API key，完全免费）
# 2. USE_SERPAPI=True：使用 SerpAPI（需要 API key）
# 3. 两者都为 False：使用 Google Custom Search API（需要 API key 和 CSE ID）

USE_DUCKDUCKGO = True  # 默认使用 DuckDuckGo，无需配置即可使用

USE_SERPAPI = False
SERPAPI_KEY = "YOUR_SERPAPI_KEY"

GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
GOOGLE_CSE_ID = "YOUR_CUSTOM_SEARCH_ENGINE_ID"

# 可选：Google Cloud Translation API Key（用于翻译 arXiv 论文摘要为中文）
# 如果不配置，将使用免费的 googletrans 库（可能不稳定）
# GOOGLE_TRANSLATE_API_KEY = "YOUR_GOOGLE_TRANSLATE_API_KEY"

# 搜索关键词，只搜索与机器人、自动驾驶相关的 VLA 内容
# 可以根据需要调整，例如：
# - 只搜索机器人相关: (VLA OR "vision language action") AND (robot OR robotics OR "robotic manipulation")
# - 只搜索自动驾驶相关: (VLA OR "vision language action") AND ("autonomous driving" OR "self-driving" OR "autonomous vehicle")
# - 搜索所有 VLA 内容: VLA OR "vision language action"
SEARCH_QUERY = "(VLA OR \"vision language action\") AND (robot OR robotics OR \"autonomous driving\" OR \"self-driving\" OR \"autonomous vehicle\" OR \"robotic manipulation\" OR \"embodied AI\" OR \"robot control\")"

# 重点关注站点，Google 查询中会自动加上 site:xxx 过滤
TARGET_SITES = [
    "zhihu.com",
    "github.com",
    "huggingface.co",
    "arxiv.org",
]

# 每天最多抓取的结果数（每个站点）
MAX_RESULTS_PER_SITE = 10

# 数据存储目录
DATA_DIR = "data"

