from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import requests

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None  # type: ignore

# 尝试导入 config，如果失败则从环境变量创建虚拟 config 对象
try:
    import config
except ImportError:
    try:
        import config.example as config  # type: ignore
    except ImportError:
        # 如果 config.example 也不存在，创建一个虚拟的 config 对象
        class Config:
            GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
            GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")
            SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
            SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "VLA")
            TARGET_SITES = ["zhihu.com", "github.com", "huggingface.co", "arxiv.org"]
            MAX_RESULTS_PER_SITE = int(os.environ.get("MAX_RESULTS_PER_SITE", "10"))
            USE_DUCKDUCKGO = os.environ.get("USE_DUCKDUCKGO", "False").lower() == "true"
            USE_SERPAPI = os.environ.get("USE_SERPAPI", "False").lower() == "true"
        
        config = Config()  # type: ignore


GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
SERPAPI_URL = "https://serpapi.com/search"


class SearchError(Exception):
    pass


def google_site_search(query: str, site: str, max_results: int = 10, after_date: str | None = None) -> list[dict[str, Any]]:
    """
    使用 Google Custom Search API 针对单个站点搜索。
    注意：需要在 config.py 中配置 GOOGLE_API_KEY 与 GOOGLE_CSE_ID。
    
    Args:
        query: 搜索关键词
        site: 目标站点
        max_results: 最大结果数（最多30，因为需要分页）
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后的内容
    """
    api_key = getattr(config, "GOOGLE_API_KEY", None)
    cse_id = getattr(config, "GOOGLE_CSE_ID", None)
    if not api_key or not cse_id:
        raise SearchError("缺少 GOOGLE_API_KEY 或 GOOGLE_CSE_ID 配置")

    q = f"{query} site:{site}"
    if after_date:
        # Google搜索支持 after: 参数来过滤日期
        q = f"{q} after:{after_date}"
    
    # Google API 每次最多返回10条，需要分页获取
    max_results = min(max_results, 30)  # 限制最多30条
    results: list[dict[str, Any]] = []
    items_per_page = 10
    pages_needed = (max_results + items_per_page - 1) // items_per_page  # 向上取整
    
    for page in range(pages_needed):
        start_index = page * items_per_page + 1  # Google API 从1开始
        num_items = min(items_per_page, max_results - len(results))
        
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": q,
            "num": num_items,
            "start": start_index,
            "hl": "zh-CN",
        }

        resp = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=20)
        if resp.status_code != 200:
            raise SearchError(f"Google API 请求失败: {resp.status_code} {resp.text}")

        data = resp.json()
        items = data.get("items", []) or []
        
        # 如果这一页没有结果，说明已经获取完所有结果
        if not items:
            break
            
        for item in items:
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "site": site,
                    "rank": len(results) + 1,  # 添加排名信息（按搜索相关性排序）
                }
            )
            # 如果已经获取到足够的结果，停止
            if len(results) >= max_results:
                break
        
        # 如果这一页返回的结果少于请求的数量，说明没有更多结果了
        if len(items) < num_items:
            break
        
        # 添加短暂延迟，避免请求过快
        if page < pages_needed - 1:
            time.sleep(0.5)
    
    return results


def serpapi_site_search(query: str, site: str, max_results: int = 10) -> list[dict[str, Any]]:
    """
    如果你使用 SerpAPI，可以通过这个函数做站点搜索。
    支持获取最多30条结果（按搜索相关性排序）。
    """
    api_key = getattr(config, "SERPAPI_KEY", None)
    if not api_key:
        raise SearchError("缺少 SERPAPI_KEY 配置")

    max_results = min(max_results, 30)  # 限制最多30条
    q = f"{query} site:{site}"
    results: list[dict[str, Any]] = []
    
    # SerpAPI 支持通过 start 参数分页
    items_per_page = 10
    pages_needed = (max_results + items_per_page - 1) // items_per_page
    
    for page in range(pages_needed):
        start_index = page * items_per_page
        num_items = min(items_per_page, max_results - len(results))
        
        params = {
            "engine": "google",
            "q": q,
            "hl": "zh-CN",
            "num": num_items,
            "start": start_index,
            "api_key": api_key,
        }
        resp = requests.get(SERPAPI_URL, params=params, timeout=20)
        if resp.status_code != 200:
            raise SearchError(f"SerpAPI 请求失败: {resp.status_code} {resp.text}")

        data = resp.json()
        organic = data.get("organic_results", []) or []
        
        if not organic:
            break
            
        for idx, item in enumerate(organic):
            if len(results) >= max_results:
                break
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "site": site,
                    "rank": len(results) + 1,  # 添加排名信息
                }
            )
        
        if len(organic) < num_items:
            break
        
        if page < pages_needed - 1:
            time.sleep(0.5)
    
    return results


def duckduckgo_site_search(query: str, site: str, max_results: int = 10) -> list[dict[str, Any]]:
    """
    使用 DuckDuckGo 搜索，无需 API key，完全免费。
    注意：DuckDuckGo 的搜索结果可能不如 Google 精确，但足够使用。
    支持获取最多30条结果（按搜索相关性排序）。
    """
    if DDGS is None:
        raise SearchError("请先安装 duckduckgo-search: pip install duckduckgo-search")

    max_results = min(max_results, 30)  # 限制最多30条
    q = f"{query} site:{site}"
    results: list[dict[str, Any]] = []
    
    try:
        # 每次搜索前等待，避免速率限制
        time.sleep(2)
        
        with DDGS() as ddgs:
            # DuckDuckGo 搜索，获取最多30条结果
            search_results = list(ddgs.text(q, max_results=max_results, safesearch="off"))
            
            for item in search_results:
                url = item.get("href", "")
                # 过滤出目标站点的结果
                if site in url:
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "url": url,
                            "snippet": item.get("body", ""),
                            "site": site,
                            "rank": len(results) + 1,  # 添加排名信息
                        }
                    )
                    if len(results) >= max_results:
                        break
    except Exception as e:
        error_msg = str(e)
        # 如果是速率限制，给出更友好的提示
        if "Ratelimit" in error_msg or "202" in error_msg:
            raise SearchError(f"DuckDuckGo 速率限制，请稍后再试。如果持续出现，建议使用 Google API 或 SerpAPI。")
        raise SearchError(f"DuckDuckGo 搜索失败: {error_msg}")
    
    return results


def search_all_sites(
    query: str | None = None, target_sites: list[str] | None = None, max_results_per_site: int | None = None, after_date: str | None = None
) -> list[dict[str, Any]]:
    """
    统一的搜索入口，会按配置决定使用 Google、SerpAPI 还是 DuckDuckGo。
    返回合并后的结果列表。
    
    搜索方式优先级：
    1. 如果 USE_DUCKDUCKGO=True，使用 DuckDuckGo（推荐，无需 API key）
    2. 如果 USE_SERPAPI=True，使用 SerpAPI
    3. 否则使用 Google Custom Search API
    
    Args:
        query: 搜索关键词
        target_sites: 目标站点列表
        max_results_per_site: 每个站点最大结果数
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后的内容（仅对Google搜索有效）
    """
    if query is None:
        query = getattr(config, "SEARCH_QUERY", "VLA")
    if target_sites is None:
        target_sites = list(getattr(config, "TARGET_SITES", []))
    if max_results_per_site is None:
        max_results_per_site = int(getattr(config, "MAX_RESULTS_PER_SITE", 10))

    use_duckduckgo = bool(getattr(config, "USE_DUCKDUCKGO", True))  # 默认使用 DuckDuckGo
    use_serpapi = bool(getattr(config, "USE_SERPAPI", False))

    all_results: list[dict[str, Any]] = []
    for idx, site in enumerate(target_sites):
        try:
            if use_duckduckgo:
                site_results = duckduckgo_site_search(query, site, max_results=max_results_per_site)
            elif use_serpapi:
                site_results = serpapi_site_search(query, site, max_results=max_results_per_site)
            else:
                site_results = google_site_search(query, site, max_results=max_results_per_site, after_date=after_date)
            
            print(f"[INFO] 站点 {site}: 找到 {len(site_results)} 条结果")
        except SearchError as e:
            # 打印错误，跳过该站点
            print(f"[WARN] 搜索站点 {site} 失败: {e}")
            continue
        
        # 给每条记录加一个时间戳字段（抓取时间）
        for r in site_results:
            r["fetched_at"] = datetime.utcnow().isoformat()
        all_results.extend(site_results)
        
        # 如果不是最后一个站点，添加延迟避免速率限制
        if idx < len(target_sites) - 1 and use_duckduckgo:
            time.sleep(3)

    return all_results


if __name__ == "__main__":
    # 简单自测
    print("Running test search...")
    results = search_all_sites()
    print(f"Got {len(results)} results.")
    for item in results[:5]:
        print(f"- [{item['site']}] {item['title']} -> {item['url']}")

