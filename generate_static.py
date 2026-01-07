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
    try:
        with app.app_context():
            # 获取所有日期
            try:
                all_days = list_all_days()
                days = filter_this_week_days(all_days)
                print(f"找到 {len(days)} 个本周的日期")
            except Exception as e:
                print(f"警告: 获取日期列表失败: {e}")
                days = []
            
            # 生成主页面（最新日期）
            current_date = days[0]["date_str"] if days else None
            summary = None
            if current_date:
                try:
                    dt = datetime.strptime(current_date, "%Y-%m-%d")
                    summary = load_daily_results(dt)
                    if summary:
                        print(f"加载日期 {current_date} 的数据成功")
                    else:
                        print(f"警告: 日期 {current_date} 没有数据")
                except Exception as e:
                    print(f"警告: 加载数据失败: {e}")
            
            # 渲染模板
            from flask import render_template
            try:
                html = render_template(
                    "index.html",
                    days=days,
                    current_date=current_date,
                    summary=summary,
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
