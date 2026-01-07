"""
生成静态 HTML 文件，用于 GitHub Pages 部署。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from app import app, group_days_by_week, aggregate_week_data
from storage import list_all_days


def generate_static_html() -> None:
    """生成静态 HTML 文件"""
    try:
        with app.app_context():
            # 获取所有日期并按周分组
            try:
                all_days = list_all_days()
                from app import group_days_by_week, aggregate_week_data
                weeks = group_days_by_week(all_days)
                print(f"找到 {len(weeks)} 个周的数据")
            except Exception as e:
                print(f"警告: 获取日期列表失败: {e}")
                weeks = []
            
            # 聚合每周的数据
            week_data_map: dict[str, dict[str, Any]] = {}
            for week in weeks:
                try:
                    week_data = aggregate_week_data(week["days"])
                    week_data_map[week["week_key"]] = week_data
                    print(f"聚合周 {week['week_label']} 的数据: {len(week_data.get('sites', []))} 个站点")
                except Exception as e:
                    print(f"警告: 聚合周 {week.get('week_key', 'unknown')} 的数据失败: {e}")
            
            # 当前周（最新的周）
            current_week = weeks[0]["week_key"] if weeks else None
            
            # 渲染模板
            from flask import render_template
            try:
                html = render_template(
                    "index.html",
                    weeks=weeks,
                    week_data_map=week_data_map,
                    current_week=current_week,
                )
            except Exception as e:
                print(f"错误: 渲染模板失败: {e}")
                raise
            
            # 创建输出目录
            output_dir = Path("docs")  # GitHub Pages 使用 docs 目录
            output_dir.mkdir(exist_ok=True)
            print(f"输出目录: {output_dir.absolute()}")
            
            # 保存主页面
            index_path = output_dir / "index.html"
            index_path.write_text(html, encoding="utf-8")
            print(f"✓ 生成主页面: {index_path}")
            
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
