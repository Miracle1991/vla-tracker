import json
import os
from datetime import datetime
from typing import Optional, List, Dict

# 尝试导入 config，如果失败则从环境变量创建虚拟 config 对象
try:
    import config
except ImportError:
    try:
        import config.example as config  # type: ignore
    except ImportError:
        # 如果 config.example 也不存在，创建一个虚拟的 config 对象
        class Config:
            DATA_DIR = os.environ.get("DATA_DIR", "data")
        
        config = Config()  # type: ignore


def ensure_data_dir() -> str:
    data_dir = getattr(config, "DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _get_daily_filepath(date: datetime) -> str:
    data_dir = ensure_data_dir()
    date_str = date.strftime("%Y-%m-%d")
    return os.path.join(data_dir, f"{date_str}.json")

def _get_week_dir() -> str:
    data_dir = ensure_data_dir()
    week_dir = os.path.join(data_dir, "weeks")
    os.makedirs(week_dir, exist_ok=True)
    return week_dir


def _get_week_filepath(week_start: datetime) -> str:
    """
    week_start: 该周周一的日期（datetime）
    """
    week_dir = _get_week_dir()
    week_str = week_start.strftime("%Y-%m-%d")
    return os.path.join(week_dir, f"{week_str}.json")


def save_week_results(week_start: datetime, results: Dict) -> None:
    """
    保存某一周（周一开始）的抓取与总结结果到 JSON 文件。
    文件路径：data/weeks/YYYY-MM-DD.json（YYYY-MM-DD 为周一）
    """
    filepath = _get_week_filepath(week_start)
    _get_week_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_week_results(week_start: datetime) -> Optional[Dict]:
    filepath = _get_week_filepath(week_start)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_all_weeks() -> List[Dict]:
    """
    返回所有已存储周的简要信息，按周从新到旧排序。
    """
    week_dir = _get_week_dir()
    if not os.path.exists(week_dir):
        return []

    weeks: list[dict] = []
    for name in os.listdir(week_dir):
        if not name.endswith(".json"):
            continue
        week_str = name[:-5]
        try:
            week_date = datetime.strptime(week_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        weeks.append({"week_key": week_str, "week_start": week_date})

    weeks.sort(key=lambda x: x["week_start"], reverse=True)
    return weeks


def save_daily_results(date: datetime, results: Dict) -> None:
    """
    保存某一天的抓取与总结结果到 JSON 文件。
    results 建议结构：
    {
        "date": "YYYY-MM-DD",
        "generated_at": "ISO8601",
        "items": [
            {
                "site": "github.com",
                "title": "...",
                "url": "...",
                "snippet": "...",
                "summary": "...",
                "published_time": "..."
            },
            ...
        ]
    }
    """
    filepath = _get_daily_filepath(date)
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_daily_results(date: datetime) -> Optional[Dict]:
    filepath = _get_daily_filepath(date)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_all_days() -> List[Dict]:
    """
    返回所有已存储日期的简要信息，按日期从新到旧排序。
    """
    data_dir = ensure_data_dir()
    if not os.path.exists(data_dir):
        return []

    days: list[dict] = []
    for name in os.listdir(data_dir):
        if not name.endswith(".json"):
            continue
        date_str = name[:-5]
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        days.append({"date_str": date_str, "date": date})

    days.sort(key=lambda x: x["date"], reverse=True)
    return days

