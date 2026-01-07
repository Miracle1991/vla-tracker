import os

# 搜索方式配置：
# 1. 特殊站点使用官方 API（无需 Google）：
#    - arXiv.org → arXiv 官方 API
#    - github.com → GitHub Search API（可选：配置 GITHUB_TOKEN 提高速率限制）
#    - huggingface.co → HuggingFace Hub API
# 2. 知乎使用 Google Custom Search API（需要 API key 和 CSE ID）
# 3. 如果 Google 被限流或未配置，将跳过该站点

# 从环境变量读取配置（用于生产环境），如果没有则使用默认值

# Google Custom Search API（用于非特殊站点）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "YOUR_GOOGLE_CSE_ID")

# GitHub Token（可选，用于提高 API 速率限制：未认证 60次/小时，认证 5000次/小时）
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 翻译配置（用于翻译 arXiv 论文摘要）
# 使用 googletrans 库（免费，无需 API Key，无需配置）

# 搜索关键词，只搜索与机器人、自动驾驶相关的 VLA 内容
SEARCH_QUERY = os.environ.get(
    "SEARCH_QUERY",
    '(VLA OR "vision language action") AND (robot OR robotics OR "autonomous driving" OR "self-driving" OR "autonomous vehicle" OR "robotic manipulation" OR "embodied AI" OR "robot control")'
)

# 只抓取从该日期开始的内容（含该月），格式 YYYY-MM-DD
START_DATE = os.environ.get("START_DATE", "2025-10-01")

# 重点关注站点
# 注意：特殊站点（GitHub、HuggingFace、arXiv）使用自己的 API，不使用 Google
# 知乎使用 Google 搜索
TARGET_SITES = [
    "zhihu.com",       # 使用 Google 搜索
    "github.com",      # 使用 GitHub Search API
    "huggingface.co",  # 使用 HuggingFace Hub API
    "arxiv.org",       # 使用 arXiv 官方 API
]

# 主流公司和机构列表（用于追踪研究进展）
# 通过 Google 搜索这些机构与 VLA 相关的研究进展
RESEARCH_ORGANIZATIONS = [
    "NVIDIA",
    "Google DeepMind",
    "Meta",
    "Microsoft",
    "OpenAI",
    "MIT",
    "Stanford",
    "UC Berkeley",
    "清华",
    "中科院",
    "新加坡国立大学",
    "Tesla",
    "Boston Dynamics",
    "Physical Intelligence",
    "智元机器人",
]

# 每天最多抓取的结果数（每个站点），按搜索相关性排序显示 top 30
MAX_RESULTS_PER_SITE = int(os.environ.get("MAX_RESULTS_PER_SITE", "30"))

# 数据存储目录
DATA_DIR = os.environ.get("DATA_DIR", "data")

