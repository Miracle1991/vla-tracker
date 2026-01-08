from __future__ import annotations

from datetime import datetime, timedelta

from crawler import search_all_sites
from summarizer import simple_group_and_summarize
from storage import save_daily_results, save_week_results, load_week_results

# 尝试导入 config，如果失败则从环境变量创建虚拟 config 对象
try:
    import config
except ImportError:
    try:
        import config.example as config  # type: ignore
    except ImportError:
        # 如果 config.example 也不存在，创建一个虚拟的 config 对象
        import os
        class Config:
            GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
            GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")
            SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "VLA")
            TARGET_SITES = ["zhihu.com", "github.com", "huggingface.co", "arxiv.org"]
            MAX_RESULTS_PER_SITE = int(os.environ.get("MAX_RESULTS_PER_SITE", "10"))
            RESEARCH_ORGANIZATIONS = [org.strip() for org in os.environ.get("RESEARCH_ORGANIZATIONS", "").split(",") if org.strip()] if os.environ.get("RESEARCH_ORGANIZATIONS") else []
            DATA_DIR = os.environ.get("DATA_DIR", "data")
            GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
            HF_TOKEN = os.environ.get("HF_TOKEN", "")
        
        config = Config()  # type: ignore


def get_week_start(date: datetime.date) -> datetime.date:
    """获取本周的开始日期（周一）"""
    days_since_monday = date.weekday()  # 0=Monday, 6=Sunday
    return date - timedelta(days=days_since_monday)


def run_once() -> None:
    """
    运行每日更新：更新上一周的内容（每周一运行）。
    """
    today = datetime.utcnow().date()
    # 获取上一周的周一（如果今天是周一，则更新上周；否则更新包含今天的那一周的前一周）
    if today.weekday() == 0:  # 今天是周一
        # 更新上一周（上周一到上周日）
        week_start = get_week_start(today) - timedelta(days=7)
    else:
        # 更新包含今天的那一周的前一周
        current_week_start = get_week_start(today)
        week_start = current_week_start - timedelta(days=7)
    
    week_end = week_start + timedelta(days=6)
    print(f"Running weekly VLA tracker for {today.isoformat()} ...")
    print(f"更新周：{week_start.isoformat()} ~ {week_end.isoformat()}")

    # 检查是否已有数据（如果已有内容，则跳过刷新以节省 API 调用）
    existing = load_week_results(datetime.combine(week_start, datetime.min.time()))
    if existing and existing.get("sites"):
        total_items = sum(len(site.get("items", [])) for site in existing.get("sites", []))
        if total_items > 0:
            print(f"✓ 该周已有数据 ({len(existing.get('sites', []))} 个站点, {total_items} 条记录)，跳过刷新")
            return  # 已有内容，跳过刷新
    
    print(f"开始搜索并更新上一周的数据...")
    
    after_date = week_start.isoformat()
    before_date = (week_end + timedelta(days=1)).isoformat()  # before: 使用下一天来包含周日
    raw_items = search_all_sites(after_date=after_date, before_date=before_date)
    print(f"Fetched {len(raw_items)} raw items.")

    if raw_items:
        summary = simple_group_and_summarize(raw_items)
        summary["date"] = today.isoformat()
        summary["week_start"] = week_start.isoformat()
        summary["week_end"] = week_end.isoformat()
        summary["last_updated"] = today.isoformat()
        
        # 保存周数据
        save_week_results(datetime.combine(week_start, datetime.min.time()), summary)
        # 同时保存为当天的数据（用于兼容）
        save_daily_results(datetime.combine(today, datetime.min.time()), summary)
        
        total_items = sum(len(site.get("items", [])) for site in summary.get("sites", []))
        print(f"Saved weekly results ({len(summary.get('sites', []))} sites, {total_items} items).")
    else:
        print(f"警告: 没有抓取到任何数据。")
        return  # 没有数据，直接返回，不保存


if __name__ == "__main__":
    run_once()

