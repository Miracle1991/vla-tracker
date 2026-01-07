from __future__ import annotations

import argparse
import time
from datetime import date, datetime, timedelta
from typing import Optional

from crawler import search_all_sites
from summarizer import simple_group_and_summarize
from storage import save_week_results, load_week_results

try:
    import config
except ImportError:
    import config.example as config  # type: ignore


def get_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill weekly VLA results.")
    parser.add_argument(
        "--since",
        type=str,
        default=getattr(config, "START_DATE", "2025-10-01"),
        help="Start date (YYYY-MM-DD), inclusive. Default from config.START_DATE.",
    )
    parser.add_argument(
        "--max-weeks",
        type=int,
        default=4,
        help="Max number of past weeks to backfill (to avoid API quota burst). Default: 4.",
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
    weeks: list[date] = []
    w = since_week
    while w <= current_week and len(weeks) < 1000:
        weeks.append(w)
        w = w + timedelta(days=7)

    # Only process last N weeks if max-weeks specified
    if args.max_weeks > 0:
        weeks = weeks[-args.max_weeks :]

    print(f"Backfilling {len(weeks)} week(s): {[wk.isoformat() for wk in weeks]}")

    for week_start in weeks:
        week_end = week_start + timedelta(days=6)
        # skip if exists
        existing = load_week_results(datetime.combine(week_start, datetime.min.time()))
        if existing:
            print(f"Skip {week_start.isoformat()} ~ {week_end.isoformat()}: already exists")
            continue

        after_date = week_start.isoformat()
        before_date = (week_end + timedelta(days=1)).isoformat()
        print(f"Fetching week {after_date} ~ {week_end.isoformat()} ...")
        raw_items = search_all_sites(after_date=after_date, before_date=before_date)
        print(f"Fetched {len(raw_items)} raw items for week {after_date}")

        summary = simple_group_and_summarize(raw_items)
        summary["week_start"] = after_date
        summary["week_end"] = week_end.isoformat()

        save_week_results(datetime.combine(week_start, datetime.min.time()), summary)
        print(f"Saved week {after_date}")

        time.sleep(float(args.sleep))


if __name__ == "__main__":
    main()

