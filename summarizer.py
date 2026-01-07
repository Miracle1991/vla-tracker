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
    - 特殊处理机构数据：按机构分组

    后续你可以在这里接入更强的自然语言模型做真正的摘要。
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    org_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    
    # 分离机构数据和其他站点数据
    for item in items:
        site = item.get("site", "unknown")
        if site == "organizations":
            # 机构数据按机构分组
            org = item.get("organization", "Unknown")
            org_grouped[org].append(item)
        else:
            grouped[site].append(item)

    site_summaries: list[dict[str, Any]] = []
    
    # 确保所有目标站点都有条目（即使没有内容）
    target_sites = ["zhihu.com", "github.com", "huggingface.co", "arxiv.org"]
    for site in target_sites:
        site_items = grouped.get(site, [])
        
        # 按排名排序（如果有 rank 字段），否则保持原有顺序（已经是按相关性排序的）
        if site_items and "rank" in site_items[0]:
            site_items.sort(key=lambda x: x.get("rank", 999))
        
        # 只保留 top 30
        site_items = site_items[:30]
        
        # 如果是 arXiv，为每个论文添加摘要（中文）
        if site == "arxiv.org" and site_items:
            print(f"[INFO] 正在为 {len(site_items)} 篇 arXiv 论文获取摘要...")
            site_items = enrich_arxiv_items(site_items)
        
        # 简单站点级别"摘要"语句
        if site_items:
            summary_text = f"{site} 上共发现 {len(site_items)} 条与 VLA 相关的更新内容（按搜索相关性排序，显示 Top {len(site_items)}）。"
        else:
            summary_text = f"{site} 本周无更新。"
        
        site_summaries.append(
            {
                "site": site,
                "site_summary": summary_text,
                "items": site_items,
            }
        )
    
    # 处理机构数据：聚合所有机构到一个"头部玩家"栏目
    # 获取所有机构列表（从 config 或已找到的机构）
    try:
        import config
        all_orgs = list(getattr(config, "RESEARCH_ORGANIZATIONS", []))
    except ImportError:
        all_orgs = list(org_grouped.keys()) if org_grouped else []
    
    # 聚合所有机构的数据
    all_org_items: list[dict[str, Any]] = []
    org_stats: dict[str, int] = {}  # 统计每个机构的数据量
    
    for org in all_orgs:
        org_items = org_grouped.get(org, [])
        
        # 按排名排序
        if org_items and "rank" in org_items[0]:
            org_items.sort(key=lambda x: x.get("rank", 999))
        
        # 只保留 top 30
        org_items = org_items[:30]
        
        # 统计每个机构的数据量
        org_stats[org] = len(org_items)
        
        # 将所有机构的数据合并，保留机构信息
        for item in org_items:
            item["organization"] = org  # 确保每个项目都有机构标识
            all_org_items.append(item)
    
    # 对所有机构数据按排名排序（跨机构排序）
    if all_org_items and "rank" in all_org_items[0]:
        all_org_items.sort(key=lambda x: x.get("rank", 999))
    
    # 只保留 top 100（聚合后的总限制）
    all_org_items = all_org_items[:100]
    
    # 统计有数据的机构数量
    orgs_with_data = sum(1 for count in org_stats.values() if count > 0)
    total_items = sum(org_stats.values())
    
    if total_items > 0:
        summary_text = f"头部玩家本周共发现 {total_items} 条与 VLA 相关的研究进展（来自 {orgs_with_data} 个机构，按搜索相关性排序，显示 Top {len(all_org_items)}）。"
    else:
        summary_text = "头部玩家本周无更新。"
    
    # 创建一个聚合的"头部玩家"条目
    site_summaries.append(
        {
            "site": "organizations",
            "site_summary": summary_text,
            "items": all_org_items,
            "organization_stats": org_stats,  # 保存每个机构的统计信息
        }
    )
    
    # 添加其他站点（如果有）
    for site, site_items in grouped.items():
        if site not in target_sites and site != "organizations":
            # 按排名排序（如果有 rank 字段），否则保持原有顺序（已经是按相关性排序的）
            if site_items and "rank" in site_items[0]:
                site_items.sort(key=lambda x: x.get("rank", 999))
            
            # 只保留 top 30
            site_items = site_items[:30]
            
            summary_text = f"{site} 上共发现 {len(site_items)} 条与 VLA 相关的更新内容（按搜索相关性排序，显示 Top {len(site_items)}）。"
            site_summaries.append(
                {
                    "site": site,
                    "site_summary": summary_text,
                    "items": site_items,
                }
            )

    # 自定义排序：arxiv → 头部玩家 → github → hf → 知乎
    def sort_key(x: dict[str, Any]) -> tuple[int, str]:
        site = x.get("site", "")
        # 定义显示顺序
        order_map = {
            "arxiv.org": 1,           # 1. arXiv
            "organizations": 2,        # 2. 头部玩家
            "github.com": 3,          # 3. GitHub
            "huggingface.co": 4,      # 4. HuggingFace
            "zhihu.com": 5,           # 5. 知乎
        }
        # 其他站点按 order_map 排序
        order = order_map.get(site, 99)
        return (order, site)
    
    result = {
        "generated_at": datetime.utcnow().isoformat(),
        "sites": sorted(site_summaries, key=sort_key),
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

