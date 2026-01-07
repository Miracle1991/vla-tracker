"""
生成静态 HTML 文件，用于 GitHub Pages 部署。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from app import app, filter_this_week_days
from storage import list_all_days, load_daily_results


def generate_static_html() -> None:
    """生成静态 HTML 文件"""
    with app.app_context():
        # 获取所有日期
        all_days = list_all_days()
        days = filter_this_week_days(all_days)
        
        # 生成主页面（最新日期）
        current_date = days[0]["date_str"] if days else None
        summary = None
        if current_date:
            dt = datetime.strptime(current_date, "%Y-%m-%d")
            summary = load_daily_results(dt)
        
        # 渲染模板
        from flask import render_template
        html = render_template(
            "index.html",
            days=days,
            current_date=current_date,
            summary=summary,
        )
        
        # 创建输出目录
        output_dir = Path("docs")  # GitHub Pages 使用 docs 目录
        output_dir.mkdir(exist_ok=True)
        
        # 保存主页面
        index_path = output_dir / "index.html"
        index_path.write_text(html, encoding="utf-8")
        print(f"✓ 生成主页面: {index_path}")
        
        # 为每个日期生成独立页面（可选，如果需要的话）
        # 注意：GitHub Pages 使用单页应用，所以主要使用 index.html
        # 如果需要多页面，可以取消下面的注释
        # for day in days:
        #     date_str = day["date_str"]
        #     dt = datetime.strptime(date_str, "%Y-%m-%d")
        #     summary = load_daily_results(dt)
        #     
        #     if summary:
        #         html = render_template(
        #             "index.html",
        #             days=days,
        #             current_date=date_str,
        #             summary=summary,
        #         )
        #         
        #         day_path = output_dir / f"{date_str}.html"
        #         day_path.write_text(html, encoding="utf-8")
        #         print(f"✓ 生成日期页面: {day_path}")
        
        # 创建 .nojekyll 文件（告诉 GitHub Pages 不要使用 Jekyll）
        nojekyll_path = output_dir / ".nojekyll"
        nojekyll_path.touch()
        print(f"✓ 创建 .nojekyll 文件")


if __name__ == "__main__":
    print("开始生成静态 HTML 文件...")
    generate_static_html()
    print("完成！静态文件已生成到 docs/ 目录")
