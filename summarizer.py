from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from arxiv_helper import enrich_arxiv_items


def simple_group_and_summarize(items: list[dict[str, Any]]) -> dict:
    """
    一个非常简单的"摘要"函数：
    - 按站点分组；
    - 每个站点保留 top 30 条记录（按搜索相关性排序，即排名）；
    - 添加一个站点级别的简短说明文字。

    后续你可以在这里接入更强的自然语言模型做真正的摘要。
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        site = item.get("site", "unknown")
        grouped[site].append(item)

    site_summaries: list[dict[str, Any]] = []
    for site, site_items in grouped.items():
        # 按排名排序（如果有 rank 字段），否则保持原有顺序（已经是按相关性排序的）
        if site_items and "rank" in site_items[0]:
            site_items.sort(key=lambda x: x.get("rank", 999))
        
        # 只保留 top 30
        site_items = site_items[:30]
        
        # 如果是 arXiv，为每个论文添加摘要（中文）
        if site == "arxiv.org":
            print(f"[INFO] 正在为 {len(site_items)} 篇 arXiv 论文获取摘要...")
            site_items = enrich_arxiv_items(site_items)
        
        # 简单站点级别"摘要"语句
        summary_text = f"{site} 上共发现 {len(site_items)} 条与 VLA 相关的更新内容（按搜索相关性排序，显示 Top {len(site_items)}）。"
        site_summaries.append(
            {
                "site": site,
                "site_summary": summary_text,
                "items": site_items,
            }
        )

    result = {
        "generated_at": datetime.utcnow().isoformat(),
        "sites": sorted(site_summaries, key=lambda x: x["site"]),
    }
    return result


if __name__ == "__main__":
    # 简单自测
    demo_items = [
        {"site": "github.com", "title": "A", "url": "https://github.com/a", "snippet": "demo"},
        {"site": "github.com", "title": "B", "url": "https://github.com/b", "snippet": "demo"},
        {"site": "zhihu.com", "title": "C", "url": "https://www.zhihu.com/c", "snippet": "demo"},
    ]
    summary = simple_group_and_summarize(demo_items)
    from pprint import pprint

    pprint(summary)

