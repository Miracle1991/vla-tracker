"""
生成静态 HTML 文件，用于 GitHub Pages 部署。
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app import app
from storage import list_all_weeks, load_week_results


def generate_static_html() -> None:
    """生成静态 HTML 文件"""
    try:
        with app.app_context():
            # 获取所有周数据
            try:
                weeks_meta = list_all_weeks()
                weeks = []
                for w in weeks_meta:
                    week_start = w["week_start"]
                    week_end = week_start + timedelta(days=6)
                    week_key = w["week_key"]
                    weeks.append(
                        {
                            "week_key": week_key,
                            "week_start": week_start,
                            "week_end": week_end,
                            "week_label": f"{week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}",
                        }
                    )
                print(f"找到 {len(weeks)} 个周的数据（来自 data/weeks/）")
            except Exception as e:
                print(f"警告: 获取周列表失败: {e}")
                weeks = []
            
            # 读取每周的数据
            week_data_map: dict[str, dict[str, Any]] = {}
            for week in weeks:
                wk = week["week_key"]
                try:
                    dt = datetime.strptime(wk, "%Y-%m-%d")
                    week_data = load_week_results(dt)
                    if week_data:
                        week_data_map[wk] = week_data
                except Exception as e:
                    print(f"警告: 读取周 {wk} 的数据失败: {e}")
            
            # 创建输出目录
            output_dir = Path("docs")  # GitHub Pages 使用 docs 目录
            output_dir.mkdir(exist_ok=True)
            print(f"输出目录: {output_dir.absolute()}")

            # 同步周数据到 docs/weeks（用于 Pages 持久化历史周数据）
            try:
                data_weeks_dir = Path("data") / "weeks"
                out_weeks_dir = output_dir / "weeks"
                out_weeks_dir.mkdir(parents=True, exist_ok=True)
                if data_weeks_dir.exists():
                    for p in data_weeks_dir.glob("*.json"):
                        shutil.copy2(p, out_weeks_dir / p.name)
                print(f"✓ 同步周数据到: {out_weeks_dir}")
            except Exception as e:
                print(f"警告: 同步周数据失败: {e}")
            
            # 渲染并保存主页面（首页）
            from flask import render_template
            try:
                current_week = weeks[0]["week_key"] if weeks else None
                html = render_template(
                    "index.html",
                    weeks=weeks,
                    week_data_map={},
                    current_week=current_week,
                )
                index_path = output_dir / "index.html"
                index_path.write_text(html, encoding="utf-8")
                print(f"✓ 生成主页面: {index_path}")
            except Exception as e:
                print(f"错误: 渲染主页面失败: {e}")
                raise
            
            # 为每个周生成独立页面
            for week in weeks:
                week_key = week["week_key"]
                week_data = week_data_map.get(week_key, {})
                
                try:
                    html = render_template(
                        "week.html",
                        weeks=weeks,
                        week_data=week_data,
                        week_label=week["week_label"],
                        current_week=week_key,
                    )
                    week_path = output_dir / f"{week_key}.html"
                    week_path.write_text(html, encoding="utf-8")
                    print(f"✓ 生成周页面: {week_path}")
                except Exception as e:
                    print(f"警告: 生成周 {week_key} 页面失败: {e}")
            
            # 创建 .nojekyll 文件（告诉 GitHub Pages 不要使用 Jekyll）
            nojekyll_path = output_dir / ".nojekyll"
            nojekyll_path.touch()
            print(f"✓ 创建 .nojekyll 文件")
            
    except Exception as e:
        print(f"严重错误: 生成静态 HTML 失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("开始生成静态 HTML 文件...")
    generate_static_html()
    print("完成！静态文件已生成到 docs/ 目录")
