from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import requests

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
            SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "VLA")
            TARGET_SITES = ["zhihu.com", "github.com", "huggingface.co", "arxiv.org"]
            MAX_RESULTS_PER_SITE = int(os.environ.get("MAX_RESULTS_PER_SITE", "10"))
        
        config = Config()  # type: ignore


GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
ARXIV_API_URL = "http://export.arxiv.org/api/query"
GITHUB_API_URL = "https://api.github.com/search/repositories"
HUGGINGFACE_API_URL = "https://huggingface.co/api/models"


class SearchError(Exception):
    pass


class RateLimitError(SearchError):
    """API 限流错误"""
    pass


def google_site_search(
    query: str,
    site: str,
    max_results: int = 10,
    after_date: str | None = None,
    before_date: str | None = None,
) -> list[dict[str, Any]]:
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

    # 如果 site 为空，则不添加站点限制（用于机构搜索）
    if site:
        q = f"{query} site:{site}"
    else:
        q = query
    if after_date:
        # Google 搜索支持 after: 参数来过滤日期
        q = f"{q} after:{after_date}"
    if before_date:
        # Google 搜索支持 before: 参数来过滤日期
        q = f"{q} before:{before_date}"
    
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
        if resp.status_code == 429:
            # 限流错误，抛出 RateLimitError
            raise RateLimitError(f"Google API 限流: {resp.status_code} {resp.text}")
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


def _simplify_query_for_github(query: str) -> str:
    """
    简化查询以符合 GitHub API 限制（最多 5 个 AND/OR/NOT 操作符）。
    
    GitHub API 对查询复杂度有限制，需要将复杂查询简化为关键词组合。
    现在返回 "VLA drive OR VLA robot"，确保包含 VLA 且同时包含 drive 或 robot 其中一个词。
    
    Args:
        query: 原始搜索查询
    
    Returns:
        简化后的查询字符串：VLA drive OR VLA robot
    """
    # 返回 "VLA drive OR VLA robot"，确保包含 VLA 且同时包含 drive 或 robot
    # GitHub API 语法：使用 OR 连接两个条件，每个条件都包含 VLA
    return "VLA drive OR VLA robot"


def github_search(query: str, max_results: int = 10, after_date: str | None = None, before_date: str | None = None) -> list[dict[str, Any]]:
    """
    使用 GitHub Search API 进行搜索。
    注意：GitHub API 无需认证也可以使用，但有速率限制（未认证：60次/小时，认证：5000次/小时）。
    建议配置 GITHUB_TOKEN 以提高速率限制。
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数（最多100条，GitHub API 单次最多返回100条）
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后更新的内容
        before_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之前更新的内容
    """
    max_results = min(max_results, 100)  # GitHub API 单次最多返回100条
    results: list[dict[str, Any]] = []
    
    # 尝试获取 GitHub Token（可选，用于提高速率限制）
    try:
        import config
        github_token = getattr(config, "GITHUB_TOKEN", None)
    except ImportError:
        github_token = os.environ.get("GITHUB_TOKEN", None)
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    # GitHub 搜索查询，简化查询以符合 GitHub API 限制（最多 5 个 AND/OR/NOT 操作符）
    # GitHub API 不支持复杂的查询，需要简化
    # 将复杂查询简化为关键词组合
    simplified_query = _simplify_query_for_github(query)
    search_query = f"{simplified_query} in:name,description,readme"
    
    # 添加 star 数量过滤（star > 100）
    search_query = f"{search_query} stars:>100"
    
    # 添加日期过滤（GitHub API 支持 updated:YYYY-MM-DD 格式）
    if after_date:
        search_query = f"{search_query} updated:>={after_date}"
    if before_date:
        # GitHub API 使用 updated:<=YYYY-MM-DD 格式
        search_query = f"{search_query} updated:<={before_date}"
    
    params = {
        "q": search_query,
        "sort": "updated",  # 按更新时间排序
        "order": "desc",
        "per_page": min(max_results, 100),  # 每页最多100条
    }
    
    try:
        resp = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=20)
        
        # 检查速率限制
        if resp.status_code == 403:
            rate_limit_remaining = resp.headers.get("X-RateLimit-Remaining", "0")
            if rate_limit_remaining == "0":
                raise RateLimitError(f"GitHub API 速率限制: {resp.status_code}")
            raise SearchError(f"GitHub API 请求失败: {resp.status_code}")
        
        if resp.status_code == 429:
            raise RateLimitError(f"GitHub API 限流: {resp.status_code}")
        
        if resp.status_code != 200:
            raise SearchError(f"GitHub API 请求失败: {resp.status_code} {resp.text}")
        
        data = resp.json()
        items = data.get("items", []) or []
        
        # 过滤掉包含特定关键词的仓库（不区分大小写）
        filtered_items = []
        filter_keywords = [
            "arxiv_daily", "arxiv-daily", "paper-daily",
            "ai-daily", "ai_daily", "awesome", "blog"
        ]
        
        for item in items:
            title = item.get("full_name", "").lower()
            description = (item.get("description", "") or "").lower()
            name = (item.get("name", "") or "").lower()
            
            # 检查是否包含要过滤的关键词
            should_filter = False
            for keyword in filter_keywords:
                if keyword in title or keyword in description or keyword in name:
                    should_filter = True
                    break
            
            if should_filter:
                continue
            
            filtered_items.append(item)
        
        # 只要在时间范围内有更新就保留（不进行内容过滤）
        # 查询已经包含了 VLA 和 (drive OR robot) 的条件，所以结果应该都是相关的
        for item in filtered_items[:max_results]:
            results.append(
                {
                    "title": item.get("full_name", ""),  # 仓库全名，如 "owner/repo"
                    "url": item.get("html_url", ""),
                    "snippet": item.get("description", "") or item.get("name", ""),
                    "site": "github.com",
                    "rank": len(results) + 1,
                }
            )
        
    except RateLimitError:
        raise
    except SearchError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "限流" in error_msg or "429" in error_msg or "rate limit" in error_msg.lower():
            raise RateLimitError(f"GitHub API 限流: {error_msg}")
        raise SearchError(f"GitHub 搜索失败: {error_msg}")
    
    return results


def huggingface_search(query: str, max_results: int = 10, after_date: str | None = None, before_date: str | None = None) -> list[dict[str, Any]]:
    """
    使用 HuggingFace Hub API 进行搜索。
    注意：HuggingFace API 无需认证，完全免费。
    注意：HuggingFace API 不支持日期过滤，会在返回结果后手动过滤。
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数（最多100条）
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后更新的内容（手动过滤）
        before_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之前更新的内容（手动过滤）
    """
    max_results = min(max_results, 100)
    results: list[dict[str, Any]] = []
    
    try:
        # 使用 HuggingFace Hub API 搜索模型
        # API 文档: https://huggingface.co/docs/api-inference/index
        params = {
            "search": query,
            "limit": max_results,
            "sort": "downloads",  # 按下载量排序
            "direction": "-1",  # 降序
        }
        
        headers = {
            "Accept": "application/json",
        }
        
        resp = requests.get(HUGGINGFACE_API_URL, headers=headers, params=params, timeout=20)
        
        if resp.status_code == 429:
            raise RateLimitError(f"HuggingFace API 限流: {resp.status_code}")
        
        if resp.status_code != 200:
            raise SearchError(f"HuggingFace API 请求失败: {resp.status_code} {resp.text}")
        
        items = resp.json()
        
        # HuggingFace API 返回的是模型列表
        # 注意：HuggingFace API 不直接支持日期过滤，需要手动过滤
        from datetime import datetime as dt
        
        for item in items:
            if len(results) >= max_results:
                break
                
            model_id = item.get("id", "")
            if not model_id:
                continue
            
            # 提取更新时间（如果可用）
            updated_at = item.get("updatedAt") or item.get("createdAt")
            
            # 日期过滤（手动过滤）
            if after_date or before_date:
                if updated_at:
                    try:
                        # HuggingFace 返回的时间格式可能是 ISO 8601
                        item_date = dt.fromisoformat(updated_at.replace('Z', '+00:00')).date()
                        after_dt = dt.strptime(after_date, "%Y-%m-%d").date() if after_date else None
                        before_dt = dt.strptime(before_date, "%Y-%m-%d").date() if before_date else None
                        
                        if after_dt and item_date < after_dt:
                            continue
                        if before_dt and item_date > before_dt:
                            continue
                    except (ValueError, AttributeError):
                        # 如果日期解析失败，保留该项（避免误过滤）
                        pass
                else:
                    # 如果没有日期信息，根据配置决定是否保留
                    # 为了安全，如果没有日期信息，我们保留该项
                    pass
            
            results.append(
                {
                    "title": model_id,
                    "url": f"https://huggingface.co/{model_id}",
                    "snippet": item.get("summary", "") or item.get("modelId", ""),
                    "site": "huggingface.co",
                    "rank": len(results) + 1,
                    "published": updated_at,  # 额外信息：更新时间
                }
            )
        
    except RateLimitError:
        raise
    except SearchError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "限流" in error_msg or "429" in error_msg or "rate limit" in error_msg.lower():
            raise RateLimitError(f"HuggingFace API 限流: {error_msg}")
        raise SearchError(f"HuggingFace 搜索失败: {error_msg}")
    
    return results


def arxiv_search(query: str, max_results: int = 10, after_date: str | None = None, before_date: str | None = None) -> list[dict[str, Any]]:
    """
    使用 arXiv 官方 API 进行搜索。
    注意：arXiv API 是免费的，无需 API Key。
    参考：https://arxiv.org/help/api
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数（最多100条，arXiv API 单次最多返回100条）
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后提交的论文
        before_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之前提交的论文
    """
    max_results = min(max_results, 100)  # arXiv API 单次最多返回100条
    results: list[dict[str, Any]] = []
    
    # arXiv API 支持分页，每页最多100条
    items_per_page = 100
    pages_needed = (max_results + items_per_page - 1) // items_per_page
    
    for page in range(pages_needed):
        start = page * items_per_page
        num_items = min(items_per_page, max_results - len(results))
        
        # 构建 arXiv 搜索查询，添加日期过滤
        # arXiv API 支持 submittedDate:[YYYYMMDD TO YYYYMMDD] 格式
        search_query = query
        if after_date or before_date:
            # 将 YYYY-MM-DD 转换为 YYYYMMDD
            after_str = after_date.replace("-", "") if after_date else "00000000"
            before_str = before_date.replace("-", "") if before_date else "99999999"
            date_filter = f"submittedDate:[{after_str} TO {before_str}]"
            search_query = f"{query} AND {date_filter}"
        
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": num_items,
            "sortBy": "relevance",  # 按相关性排序
            "sortOrder": "descending",
        }
        
        try:
            resp = requests.get(ARXIV_API_URL, params=params, timeout=20)
            if resp.status_code == 429:
                raise RateLimitError(f"arXiv API 限流: {resp.status_code}")
            if resp.status_code != 200:
                raise SearchError(f"arXiv API 请求失败: {resp.status_code} {resp.text}")
            
            # 解析 Atom XML 响应
            try:
                from xml.etree import ElementTree as ET
            except ImportError:
                raise SearchError("需要 xml.etree.ElementTree 模块（Python 标准库）")
            
            root = ET.fromstring(resp.text)
            
            # Atom 命名空间
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # 查找所有 entry 元素
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                break
            
            for entry in entries:
                if len(results) >= max_results:
                    break
                
                # 提取标题
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                
                # 提取链接（abs 页面）
                link_elem = entry.find('atom:id', ns)  # arXiv 使用 id 作为链接
                url = link_elem.text if link_elem is not None and link_elem.text else ""
                
                # 如果没有 id，尝试找 link
                if not url:
                    link = entry.find('atom:link[@type="text/html"]', ns)
                    if link is not None:
                        url = link.get('href', '')
                
                # 提取摘要
                summary_elem = entry.find('atom:summary', ns)
                snippet = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
                
                # 提取发布日期
                published_elem = entry.find('atom:published', ns)
                published = published_elem.text if published_elem is not None and published_elem.text else ""
                
                # 提取作者信息
                authors = []
                for author_elem in entry.findall('atom:author', ns):
                    name_elem = author_elem.find('atom:name', ns)
                    if name_elem is not None and name_elem.text:
                        author_name = name_elem.text.strip()
                        if author_name:
                            authors.append(author_name)
                
                if title and url:
                    result_item = {
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "site": "arxiv.org",
                        "rank": len(results) + 1,
                        "published": published,  # 额外信息：发布日期
                    }
                    # 如果有作者信息，添加到结果中
                    if authors:
                        result_item["authors"] = authors
                    results.append(result_item)
            
            # 如果这一页返回的结果少于请求的数量，说明没有更多结果了
            if len(entries) < num_items:
                break
            
            # 添加延迟，避免请求过快（arXiv 建议每秒不超过1个请求）
            if page < pages_needed - 1:
                time.sleep(1.2)  # 延迟 1.2 秒，确保不超过 1 QPS
                
        except RateLimitError:
            raise
        except SearchError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "限流" in error_msg or "429" in error_msg or "rate limit" in error_msg.lower():
                raise RateLimitError(f"arXiv API 限流: {error_msg}")
            raise SearchError(f"arXiv 搜索失败: {error_msg}")
    
    return results


def search_all_sites(
    query: str | None = None,
    target_sites: list[str] | None = None,
    max_results_per_site: int | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    统一的搜索入口，优先使用 Google。
    返回合并后的结果列表。
    
    搜索方式优先级：
    1. 特殊站点使用官方 API：
       - arXiv.org → arXiv 官方 API
       - github.com → GitHub Search API
       - huggingface.co → HuggingFace Hub API
    2. 其他站点：使用 Google Custom Search API（如果配置）
    3. 如果 Google 被限流或未配置，将跳过该站点
    
    Args:
        query: 搜索关键词
        target_sites: 目标站点列表
        max_results_per_site: 每个站点最大结果数
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后的内容（仅对Google搜索有效）
        before_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之前的内容（仅对Google搜索有效）
    """
    if query is None:
        query = getattr(config, "SEARCH_QUERY", "VLA")
    if target_sites is None:
        target_sites = list(getattr(config, "TARGET_SITES", []))
    if max_results_per_site is None:
        max_results_per_site = int(getattr(config, "MAX_RESULTS_PER_SITE", 10))

    # 检查是否配置了 Google API
    has_google = bool(getattr(config, "GOOGLE_API_KEY", None) and getattr(config, "GOOGLE_CSE_ID", None))

    all_results: list[dict[str, Any]] = []
    google_rate_limited = False  # 标记 Google 是否被限流
    
    for idx, site in enumerate(target_sites):
        site_results: list[dict[str, Any]] = []
        
        try:
            # 特殊处理：如果是 arXiv，优先使用 arXiv 官方 API
            if site == "arxiv.org":
                try:
                    # 构建 arXiv 搜索查询（添加类别限制，只搜索相关领域）
                    # 可以添加 cat:cs.AI OR cat:cs.RO 等来限制类别
                    arxiv_query = f"all:{query}"
                    site_results = arxiv_search(arxiv_query, max_results=max_results_per_site, after_date=after_date, before_date=before_date)
                    if site_results:
                        print(f"[INFO] 站点 {site}: 找到 {len(site_results)} 条结果 (arXiv API)")
                        # 如果 arXiv 搜索成功，跳过通用搜索引擎
                        all_results.extend(site_results)
                        continue
                    else:
                        print(f"[WARN] arXiv API 未获取到结果，降级到通用搜索引擎")
                except (RateLimitError, SearchError) as e:
                    print(f"[WARN] arXiv API 搜索失败，降级到通用搜索引擎: {e}")
                    # 降级到通用搜索引擎，继续执行下面的逻辑
                except Exception as e:
                    print(f"[WARN] arXiv API 搜索异常，降级到通用搜索引擎: {e}")
                    # 降级到通用搜索引擎，继续执行下面的逻辑
            
            # 特殊处理：如果是 GitHub，使用 GitHub Search API
            if site == "github.com":
                try:
                    site_results = github_search(query, max_results=max_results_per_site, after_date=after_date, before_date=before_date)
                    # 如果设置了日期过滤但没有结果，直接返回空（不降级）
                    if site_results:
                        print(f"[INFO] 站点 {site}: 找到 {len(site_results)} 条结果 (GitHub API)")
                        all_results.extend(site_results)
                        continue
                    else:
                        if after_date or before_date:
                            print(f"[INFO] 站点 {site}: 时间范围内没有内容，跳过")
                        else:
                            print(f"[WARN] GitHub API 未获取到结果，跳过站点 {site}")
                        continue
                except (RateLimitError, SearchError) as e:
                    print(f"[WARN] GitHub API 搜索失败，跳过站点 {site}: {e}")
                    continue
                except Exception as e:
                    print(f"[WARN] GitHub API 搜索异常，跳过站点 {site}: {e}")
                    continue
            
            # 特殊处理：如果是 HuggingFace，使用 HuggingFace Hub API
            if site == "huggingface.co":
                try:
                    # HuggingFace API 可能不支持复杂的布尔查询，先搜索 VLA，然后在结果中过滤
                    # 搜索更多结果以便过滤后仍有足够的数据
                    hf_query = "VLA"
                    all_hf_results = huggingface_search(hf_query, max_results=max_results_per_site * 3, after_date=after_date, before_date=before_date)
                    
                    # 过滤：只保留同时包含 VLA 和 (drive 或 robot) 的结果
                    # 但日期过滤已经在 huggingface_search 中完成，这里只做内容过滤
                    site_results = []
                    for item in all_hf_results:
                        title = item.get('title', '')
                        snippet = item.get('snippet', '')
                        text = (title + ' ' + snippet).lower()
                        has_vla = 'vla' in text
                        has_drive = 'drive' in text
                        has_robot = 'robot' in text
                        # 必须同时包含 VLA 和 (drive 或 robot)
                        if has_vla and (has_drive or has_robot):
                            site_results.append(item)
                            if len(site_results) >= max_results_per_site:
                                break
                    
                    site_results = site_results[:max_results_per_site]  # 限制结果数量
                    # 如果设置了日期过滤但没有结果，直接返回空（不降级）
                    if site_results:
                        print(f"[INFO] 站点 {site}: 找到 {len(site_results)} 条结果 (HuggingFace API)")
                        all_results.extend(site_results)
                        continue
                    else:
                        if after_date or before_date:
                            print(f"[INFO] 站点 {site}: 时间范围内没有内容，跳过")
                        else:
                            print(f"[WARN] HuggingFace API 未获取到结果，跳过站点 {site}")
                        continue
                except (RateLimitError, SearchError) as e:
                    print(f"[WARN] HuggingFace API 搜索失败，跳过站点 {site}: {e}")
                    continue
                except Exception as e:
                    print(f"[WARN] HuggingFace API 搜索异常，跳过站点 {site}: {e}")
                    continue
            
            # 对于其他站点，如果配置了 Google 且未被限流，使用 Google
            if has_google and not google_rate_limited:
                try:
                    site_results = google_site_search(
                        query,
                        site,
                        max_results=max_results_per_site,
                        after_date=after_date,
                        before_date=before_date,
                    )
                    print(f"[INFO] 站点 {site}: 找到 {len(site_results)} 条结果 (Google)")
                except RateLimitError as e:
                    # Google 被限流，标记并跳过该站点
                    google_rate_limited = True
                    print(f"[WARN] Google API 被限流，跳过站点 {site}: {e}")
                    continue
                except SearchError as e:
                    # 其他 Google 错误，打印警告并跳过该站点
                    print(f"[WARN] Google 搜索站点 {site} 失败: {e}")
                    continue
            
            else:
                # 如果没有配置 Google API，跳过该站点
                print(f"[WARN] 未配置 Google API，跳过站点 {site}")
                continue
                
        except SearchError as e:
            # 打印错误，跳过该站点
            print(f"[WARN] 搜索站点 {site} 失败: {e}")
            continue
        
        # 给每条记录加一个时间戳字段（抓取时间）
        for r in site_results:
            r["fetched_at"] = datetime.utcnow().isoformat()
        all_results.extend(site_results)
        
        # 如果不是最后一个站点，添加延迟避免速率限制
        if idx < len(target_sites) - 1:
            time.sleep(1)
    
    # 搜索机构研究进展
    if has_google and not google_rate_limited:
        try:
            print("[INFO] 开始搜索机构研究进展...")
            org_results = search_organizations(
                max_results_per_org=max_results_per_site,
                after_date=after_date,
                before_date=before_date,
            )
            if org_results:
                print(f"[INFO] 机构研究进展: 找到 {len(org_results)} 条结果")
                all_results.extend(org_results)
        except RateLimitError as e:
            print(f"[WARN] 机构搜索时 Google 被限流: {e}")
        except Exception as e:
            print(f"[WARN] 机构搜索失败: {e}")

    return all_results


def search_organizations(
    organizations: list[str] | None = None,
    max_results_per_org: int = 10,
    after_date: str | None = None,
    before_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    搜索主流公司和机构的研究进展。
    使用 Google 搜索，查询格式：机构名 + VLA + 机器人/自动驾驶相关关键词。
    
    Args:
        organizations: 机构列表，如果为 None 则从 config 读取
        max_results_per_org: 每个机构最大结果数
        after_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之后的内容
        before_date: 可选，格式为 "YYYY-MM-DD"，只搜索此日期之前的内容
    
    Returns:
        结果列表，每个结果包含 organization 字段标识所属机构
    """
    if organizations is None:
        organizations = list(getattr(config, "RESEARCH_ORGANIZATIONS", []))
    
    # 基础查询：VLA + 机器人/自动驾驶相关
    base_query = '(VLA OR "vision language action") AND (robot OR robotics OR "autonomous driving" OR "self-driving" OR "autonomous vehicle" OR "robotic manipulation" OR "embodied AI" OR "robot control")'
    
    all_results: list[dict[str, Any]] = []
    google_rate_limited = False
    
    for org in organizations:
        if google_rate_limited:
            print(f"[WARN] Google 已被限流，跳过机构 {org}")
            continue
        
        try:
            # 构建查询：机构名 + 基础查询
            org_query = f'"{org}" {base_query}'
            
            # 使用 Google 搜索（不限制站点）
            try:
                results = google_site_search(
                    query=org_query,
                    site="",  # 不限制站点，搜索全网
                    max_results=max_results_per_org,
                    after_date=after_date,
                    before_date=before_date,
                )
                
                # 为每个结果添加机构标识
                for item in results:
                    item["organization"] = org
                    item["site"] = "organizations"  # 统一站点标识
                
                all_results.extend(results)
                print(f"[INFO] {org}: 找到 {len(results)} 条结果")
                
            except RateLimitError as e:
                print(f"[WARN] Google 搜索限流（机构 {org}）: {e}")
                google_rate_limited = True
                continue
            except Exception as e:
                print(f"[WARN] 机构 {org} 搜索失败: {e}")
                continue
                
        except Exception as e:
            print(f"[WARN] 处理机构 {org} 时出错: {e}")
            continue
    
    return all_results


if __name__ == "__main__":
    # 简单自测
    print("Running test search...")
    results = search_all_sites()
    print(f"Got {len(results)} results.")
    for item in results[:5]:
        print(f"- [{item['site']}] {item['title']} -> {item['url']}")

