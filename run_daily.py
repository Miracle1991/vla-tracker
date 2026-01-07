from __future__ import annotations

from datetime import datetime, timedelta

from crawler import search_all_sites
from summarizer import simple_group_and_summarize
from storage import save_daily_results, save_week_results

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
    week_start = get_week_start(today)
    week_end = week_start + timedelta(days=6)
    print(f"Running daily VLA tracker for {today.isoformat()} ...")
    start_date = getattr(config, "START_DATE", "2025-10-01")
    print(f"只抓取从 {start_date} 开始的内容；并按周归档（本次更新周：{week_start.isoformat()}~{week_end.isoformat()}）")

    # 只抓取“本周”窗口（避免把所有历史结果都塞进当前周）
    # 同时保证不早于 START_DATE（当 START_DATE 晚于本周周一时，以 START_DATE 为准）
    after_date = max(start_date, week_start.isoformat())
    before_date = (week_end + timedelta(days=1)).isoformat()  # before: 使用下一天来包含周日
    raw_items = search_all_sites(after_date=after_date, before_date=before_date)
    print(f"Fetched {len(raw_items)} raw items.")

    summary = simple_group_and_summarize(raw_items)
    summary["date"] = today.isoformat()
    summary["week_start"] = week_start.isoformat()
    summary["week_end"] = week_end.isoformat()

    save_daily_results(datetime.combine(today, datetime.min.time()), summary)
    # 同时保存本周聚合结果（供周时间线展示）
    save_week_results(datetime.combine(week_start, datetime.min.time()), summary)
    print("Saved daily results.")


if __name__ == "__main__":
    run_once()

