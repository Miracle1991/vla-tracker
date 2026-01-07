from __future__ import annotations

import argparse
import time
from datetime import date, datetime, timedelta
from typing import Optional

from crawler import search_all_sites
from summarizer import simple_group_and_summarize
from storage import save_week_results, load_week_results

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


def get_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill weekly VLA results.")
    parser.add_argument(
        "--since",
        type=str,
        default="2025-12-01",
        help="Start date (YYYY-MM-DD), inclusive. Default: 2025-12-01.",
    )
    parser.add_argument(
        "--max-weeks",
        type=int,
        default=0,
        help="Max number of past weeks to backfill (0 = all empty weeks). Default: 0 (all).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=2.0,
        help="Seconds to sleep between weeks to be gentle on APIs. Default: 2s.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    since_date = datetime.strptime(args.since, "%Y-%m-%d").date()
    since_week = get_week_start(since_date)
    today = datetime.utcnow().date()
    current_week = get_week_start(today)

    # Build list of week starts from since_week to current_week (inclusive)
    all_weeks: list[date] = []
    w = since_week
    while w <= current_week and len(all_weeks) < 1000:
        all_weeks.append(w)
        w = w + timedelta(days=7)

    # Filter: only keep weeks that are empty or have no data
    weeks: list[date] = []
    for week_start in all_weeks:
        existing = load_week_results(datetime.combine(week_start, datetime.min.time()))
        if existing and existing.get("sites"):
            total_items = sum(len(site.get("items", [])) for site in existing.get("sites", []))
            if total_items > 0:
                continue  # 跳过已有内容的周
        weeks.append(week_start)  # 只处理空的周

    # Only process last N weeks if max-weeks specified
    if args.max_weeks > 0:
        weeks = weeks[-args.max_weeks :]

    print(f"发现 {len(weeks)} 个需要补齐的周（共检查了 {len(all_weeks)} 个周）")
    if weeks:
        print(f"将补齐以下周: {[wk.isoformat() for wk in weeks]}")
    else:
        print("所有周都有数据，无需补齐")
        return

    for week_start in weeks:
        week_end = week_start + timedelta(days=6)
        week_key = week_start.isoformat()
        
        # 检查是否已有数据（不仅检查文件是否存在，还要检查数据是否为空）
        existing = load_week_results(datetime.combine(week_start, datetime.min.time()))
        if existing and existing.get("sites"):
            # 检查是否有实际内容
            total_items = sum(len(site.get("items", [])) for site in existing.get("sites", []))
            if total_items > 0:
                print(f"✓ Skip {week_key} ~ {week_end.isoformat()}: 已有数据 ({len(existing.get('sites', []))} 个站点, {total_items} 条记录)")
                continue
            else:
                print(f"⚠ {week_key} ~ {week_end.isoformat()}: 数据文件存在但为空，将重新抓取")
        else:
            print(f"✗ {week_key} ~ {week_end.isoformat()}: 无数据，开始抓取")

        after_date = week_start.isoformat()
        before_date = (week_end + timedelta(days=1)).isoformat()
        print(f"  Fetching week {after_date} ~ {week_end.isoformat()} ...")
        raw_items = search_all_sites(after_date=after_date, before_date=before_date)
        print(f"  Fetched {len(raw_items)} raw items for week {after_date}")

        if raw_items:
            summary = simple_group_and_summarize(raw_items)
            summary["week_start"] = after_date
            summary["week_end"] = week_end.isoformat()
            summary["last_updated"] = datetime.utcnow().date().isoformat()

            save_week_results(datetime.combine(week_start, datetime.min.time()), summary)
            total_items = sum(len(site.get("items", [])) for site in summary.get("sites", []))
            print(f"  ✓ Saved week {after_date} ({len(summary.get('sites', []))} 个站点, {total_items} 条记录)")
        else:
            print(f"  ⚠ 警告: 本周没有抓取到任何数据，跳过保存")

        time.sleep(float(args.sleep))


if __name__ == "__main__":
    main()

