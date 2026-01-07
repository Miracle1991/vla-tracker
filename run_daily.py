from __future__ import annotations

from datetime import datetime, timedelta

from crawler import search_all_sites
from summarizer import simple_group_and_summarize
from storage import save_daily_results

try:
    import config
except ImportError:
    import config.example as config  # type: ignore


def get_week_start(date: datetime.date) -> datetime.date:
    """获取本周的开始日期（周一）"""
    days_since_monday = date.weekday()  # 0=Monday, 6=Sunday
    return date - timedelta(days=days_since_monday)


def run_once() -> None:
    today = datetime.utcnow().date()
    print(f"Running daily VLA tracker for {today.isoformat()} ...")
    start_date = getattr(config, "START_DATE", "2025-10-01")
    print(f"只抓取从 {start_date} 开始的内容")

    # 只搜索从起始日期开始的内容
    raw_items = search_all_sites(after_date=start_date)
    print(f"Fetched {len(raw_items)} raw items.")

    summary = simple_group_and_summarize(raw_items)
    summary["date"] = today.isoformat()

    save_daily_results(datetime.combine(today, datetime.min.time()), summary)
    print("Saved daily results.")


if __name__ == "__main__":
    run_once()

