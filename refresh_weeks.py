"""
刷新指定日期之后的所有周的数据（强制重新抓取）。
用于代码更新时重新抓取历史数据。
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta

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


def refresh_weeks_since(since_date: str, sleep: float = 2.0, skip_if_all_exist: bool = True) -> None:
    """
    刷新指定日期之后的所有周的数据（强制重新抓取）。
    
    Args:
        since_date: 起始日期，格式 "YYYY-MM-DD"
        sleep: 每个周之间的延迟（秒）
        skip_if_all_exist: 如果所有周都有数据，是否跳过整个刷新过程（默认 True，节省资源）
    """
    since_dt = datetime.strptime(since_date, "%Y-%m-%d").date()
    since_week = get_week_start(since_dt)
    today = datetime.utcnow().date()
    current_week = get_week_start(today)

    # 构建从 since_week 到 current_week 的所有周列表
    all_weeks: list[date] = []
    w = since_week
    while w <= current_week and len(all_weeks) < 1000:
        all_weeks.append(w)
        w = w + timedelta(days=7)

    print(f"将检查 {len(all_weeks)} 个周的数据（从 {since_week.isoformat()} 到 {current_week.isoformat()}）")
    if all_weeks:
        print(f"周列表: {[wk.isoformat() for wk in all_weeks]}")
    print()

    # 如果启用了 skip_if_all_exist，先快速检查是否所有周都有数据
    if skip_if_all_exist and all_weeks:
        print("快速检查：验证是否所有周都有数据...")
        weeks_need_refresh = []
        for week_start in all_weeks:
            existing = load_week_results(datetime.combine(week_start, datetime.min.time()))
            if existing and existing.get("sites"):
                total_items = sum(len(site.get("items", [])) for site in existing.get("sites", []))
                if total_items == 0:
                    weeks_need_refresh.append(week_start)
            else:
                weeks_need_refresh.append(week_start)
        
        if not weeks_need_refresh:
            print("✓ 所有周都有数据，跳过刷新以节省 API 调用")
            print(f"=" * 60)
            print(f"✓ 共检查 {len(all_weeks)} 个周，全部已有数据，无需刷新")
            print(f"=" * 60)
            return
        
        # 只处理需要刷新的周
        all_weeks = weeks_need_refresh
        print(f"发现 {len(all_weeks)} 个周需要刷新：{[wk.isoformat() for wk in all_weeks]}")

    completed_count = 0
    total_count = len(all_weeks)
    skipped_count = 0
    
    for week_start in all_weeks:
        week_end = week_start + timedelta(days=6)
        week_key = week_start.isoformat()

        # 检查是否已有数据（仅检查是否有内容，不检查文件是否存在）
        existing = load_week_results(datetime.combine(week_start, datetime.min.time()))
        if existing and existing.get("sites"):
            total_items = sum(len(site.get("items", [])) for site in existing.get("sites", []))
            if total_items > 0:
                skipped_count += 1
                print(f"\n跳过 {week_key} ~ {week_end.isoformat()}: 已有数据 ({len(existing.get('sites', []))} 个站点, {total_items} 条记录)")
                completed_count += 1
                continue  # 跳过已有内容的周

        print(f"\n刷新 {week_key} ~ {week_end.isoformat()} ...")

        after_date = week_start.isoformat()
        before_date = (week_end + timedelta(days=1)).isoformat()
        
        raw_items = search_all_sites(after_date=after_date, before_date=before_date)
        print(f"  抓取到 {len(raw_items)} 条原始数据")

        if raw_items:
            summary = simple_group_and_summarize(raw_items)
            summary["week_start"] = after_date
            summary["week_end"] = week_end.isoformat()
            summary["last_updated"] = datetime.utcnow().date().isoformat()

            save_week_results(datetime.combine(week_start, datetime.min.time()), summary)
            total_items = sum(len(site.get("items", [])) for site in summary.get("sites", []))
            completed_count += 1
            print(f"  ✓ 已保存周 {after_date} ({len(summary.get('sites', []))} 个站点, {total_items} 条记录) [{completed_count}/{total_count}]")
        else:
            completed_count += 1
            print(f"  ⚠ 警告: 本周没有抓取到任何数据 [{completed_count}/{total_count}]")

        time.sleep(sleep)
    
    print()
    print(f"=" * 60)
    if skipped_count > 0:
        print(f"✓ 所有周的数据处理完成！共处理 {completed_count}/{total_count} 个周（跳过 {skipped_count} 个已有内容的周）")
    else:
        print(f"✓ 所有周的数据刷新完成！共处理 {completed_count}/{total_count} 个周")
    print(f"=" * 60)


if __name__ == "__main__":
    # 默认刷新 2025年8月之后的所有周
    since_date = "2025-08-01"
    refresh_weeks_since(since_date, sleep=2.0)
