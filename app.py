from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from flask import Flask, render_template, abort, request, jsonify
from jinja2 import DictLoader
import requests

from storage import list_all_weeks, load_week_results

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
            GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "Miracle1991")
            GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "vla-tracker")
        
        config = Config()  # type: ignore

# 用于定时任务触发数据更新
try:
    from run_daily import run_once
except ImportError:
    run_once = None


def get_week_start(date: datetime.date) -> datetime.date:
    """获取本周的开始日期（周一）"""
    days_since_monday = date.weekday()  # 0=Monday, 6=Sunday
    return date - timedelta(days=days_since_monday)


def filter_this_week_days(days: list[dict]) -> list[dict]:
    """只保留本周的日期"""
    today = datetime.utcnow().date()
    week_start = get_week_start(today)
    week_end = week_start + timedelta(days=6)
    
    this_week_days = []
    for day in days:
        day_date = day.get("date")
        if day_date and week_start <= day_date <= week_end:
            this_week_days.append(day)
    return this_week_days


def _build_week_list() -> list[dict]:
    """
    从 data/weeks/*.json 构建周列表，供模板渲染。
    """
    weeks_meta = list_all_weeks()
    weeks: list[dict] = []
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
    return weeks


BASE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>VLA 每周追踪</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif; margin: 0; padding: 0; background: #f5f5f7; color: #111827;}
      header { background: #111827; color: white; padding: 1rem 1.5rem; position: relative; }
      header h1 { margin: 0; font-size: 1.5rem; }
      header p { margin: 0.25rem 0 0; font-size: 0.9rem; color: #9ca3af; }
      .star-button { position: absolute; top: 1rem; right: 1.5rem; display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: #1f2937; border: 1px solid #374151; border-radius: 0.5rem; color: white; text-decoration: none; font-size: 0.9rem; transition: all 0.2s; cursor: pointer; }
      .star-button:hover { background: #374151; border-color: #4b5563; transform: translateY(-1px); }
      .star-button:active { transform: translateY(0); }
      .star-icon { font-size: 1.1rem; }
      .star-count { font-weight: 500; }
      @media (max-width: 768px) {
        .star-button { position: static; margin-top: 0.75rem; display: inline-flex; }
      }
      .container { display: flex; }
      .sidebar { background: white; padding: 1.5rem 1rem; position: sticky; top: 0; height: fit-content; max-height: calc(100vh - 80px); overflow-y: auto; }
      .sidebar-left { width: 180px; border-right: 1px solid #e5e7eb; }
      .sidebar-right { width: 280px; border-left: 1px solid #e5e7eb; }
      .sidebar h3 { margin: 0 0 1rem 0; font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
      .sidebar ul { list-style: none; padding: 0; margin: 0; }
      .sidebar li { margin-bottom: 0.5rem; }
      .sidebar a { display: block; padding: 0.5rem 0.75rem; color: #374151; text-decoration: none; border-radius: 0.375rem; font-size: 0.9rem; transition: background-color 0.2s; white-space: nowrap; }
      .sidebar a:hover { background: #f3f4f6; color: #111827; }
      .sidebar a.active { background: #111827; color: white; }
      .week-link { font-weight: 500; }
      main { flex: 1; padding: 1.5rem; max-width: 1200px; }
      .date-list { margin-bottom: 1.5rem; }
      .date-pill { display: inline-block; margin: 0.25rem 0.4rem 0.25rem 0; padding: 0.35rem 0.75rem; border-radius: 999px; background: #e5e7eb; font-size: 0.85rem; text-decoration: none; color: #111827; }
      .date-pill.active { background: #111827; color: #f9fafb; }
      .card { background: white; border-radius: 0.75rem; padding: 1.25rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 10px 15px -3px rgba(15,23,42,0.08), 0 4px 6px -2px rgba(15,23,42,0.05); scroll-margin-top: 1rem; }
      .card h2 { margin-top: 0; font-size: 1.1rem; margin-bottom: 0.4rem; }
      .card small { color: #6b7280; }
      .item-list { margin-top: 0.75rem; padding-left: 1.1rem; }
      .item-list li { margin-bottom: 0.45rem; }
      .item-list a { color: #2563eb; text-decoration: none; }
      .item-list a:hover { text-decoration: underline; }
      .empty { color: #6b7280; font-size: 0.95rem; }
      footer { text-align: center; padding: 1rem; font-size: 0.75rem; color: #6b7280; }
      @media (max-width: 1024px) {
        .sidebar-left { width: 140px; padding: 1rem 0.75rem; }
        .sidebar-right { width: 220px; padding: 1rem 0.75rem; }
      }
      @media (max-width: 768px) {
        .container { flex-direction: column; }
        .sidebar { width: 100%; position: relative; border-right: none; border-left: none; border-bottom: 1px solid #e5e7eb; max-height: none; }
        .sidebar-left { border-right: none; }
        .sidebar-right { border-left: none; }
        .sidebar ul { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .sidebar li { margin-bottom: 0; }
        main { padding: 1rem; order: -1; }
      }
    </style>
    <script>
      // 平滑滚动到锚点（来源目录）
      document.querySelectorAll('.sidebar a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
          e.preventDefault();
          const targetId = this.getAttribute('href').substring(1);
          const targetElement = document.getElementById(targetId);
          if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // 更新活动状态
            document.querySelectorAll('.sidebar a[href^="#"]').forEach(a => a.classList.remove('active'));
            this.classList.add('active');
          }
        });
      });
      
      // 根据滚动位置高亮当前站点
      function updateActiveSite() {
        const cards = document.querySelectorAll('.card[id]');
        const siteLinks = document.querySelectorAll('.sidebar a[href^="#"]');
        let currentSite = '';
        
        cards.forEach(card => {
          const rect = card.getBoundingClientRect();
          if (rect.top <= 150 && rect.bottom >= 150) {
            currentSite = card.id;
          }
        });
        
        siteLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + currentSite) {
            link.classList.add('active');
          }
        });
      }
      
      // 监听滚动事件
      window.addEventListener('scroll', updateActiveSite);
      // 页面加载时也更新一次
      window.addEventListener('load', updateActiveSite);
      
      // 获取 GitHub star 数量
      async function fetchStarCount() {
        try {
          const response = await fetch('/api/github-stars');
          if (response.ok) {
            const data = await response.json();
            const starCountEl = document.getElementById('starCount');
            if (starCountEl) {
              starCountEl.textContent = data.stargazers_count || 0;
            }
          } else {
            const starCountEl = document.getElementById('starCount');
            if (starCountEl) {
              starCountEl.textContent = '?';
            }
          }
        } catch (error) {
          console.error('获取 star 数量失败:', error);
          const starCountEl = document.getElementById('starCount');
          if (starCountEl) {
            starCountEl.textContent = '?';
          }
        }
      }
      
      // 处理点赞按钮点击
      function handleStarClick(event) {
        // 不阻止默认行为，让链接正常跳转
        // 按钮已经设置了 href，会直接跳转到 GitHub 仓库页面
        // 用户可以在 GitHub 页面点击 star 按钮
      }
      
      // 页面加载时获取 star 数量
      window.addEventListener('load', fetchStarCount);
    </script>
  </head>
  <body>
    <header>
      <h1>VLA 每周追踪</h1>
      <p>自动聚合来自 知乎 / GitHub / HuggingFace / arXiv 的 VLA 相关更新（专注于机器人、自动驾驶领域）</p>
      <a href="{{ github_repo_url }}" target="_blank" rel="noopener noreferrer" class="star-button" id="starButton" onclick="handleStarClick(event)">
        <span class="star-icon">⭐</span>
        <span class="star-text">点赞</span>
        <span class="star-count" id="starCount">加载中...</span>
      </a>
    </header>
    <div class="container">
      <aside class="sidebar sidebar-left">
        <h3>来源目录</h3>
        <ul>
          <li><a href="#arxiv">arXiv</a></li>
          <li><a href="#github">GitHub</a></li>
          <li><a href="#huggingface">HuggingFace</a></li>
          <li><a href="#zhihu">知乎</a></li>
        </ul>
        <h3 style="margin-top: 1.5rem;">头部玩家</h3>
        <ul>
          {% if week_data and week_data.get('sites') %}
            {% set has_orgs = false %}
            {% for site_block in week_data.get('sites', []) %}
              {% if site_block.get('site') == 'organizations' %}
                {% set has_orgs = true %}
              {% endif %}
            {% endfor %}
            {% if has_orgs %}
              <li><a href="#organizations">🏢 头部玩家</a></li>
            {% else %}
              <li style="color: #9ca3af; font-size: 0.85rem; padding: 0.5rem 0.75rem;">本周无更新</li>
            {% endif %}
          {% else %}
            <li style="color: #9ca3af; font-size: 0.85rem; padding: 0.5rem 0.75rem;">本周无更新</li>
          {% endif %}
        </ul>
      </aside>
      <main>
        {% block content %}{% endblock %}
      </main>
      <aside class="sidebar sidebar-right">
        <h3>时间线</h3>
        <ul id="week-timeline">
          {% for week in weeks %}
            <li>
              <a href="{{ week.week_key }}.html" class="week-link {% if week.week_key == current_week %}active{% endif %}" data-week="{{ week.week_key }}">
                {{ week.week_label }}
              </a>
            </li>
          {% endfor %}
        </ul>
      </aside>
    </div>
    <footer>
      数据来源于 Google 搜索结果，仅供学习与研究使用。
    </footer>
  </body>
</html>
"""


INDEX_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
  {% if weeks %}
    <div style="text-align: center; padding: 3rem 1rem;">
      <h2 style="color: #111827; margin-bottom: 1rem;">VLA 每周追踪</h2>
      <p style="color: #6b7280; margin-bottom: 2rem;">请从右侧时间线选择要查看的周，或点击下方链接查看最新周：</p>
      <a href="{{ weeks[0].week_key }}.html" style="display: inline-block; padding: 0.75rem 1.5rem; background: #111827; color: white; text-decoration: none; border-radius: 0.5rem; font-weight: 500;">
        查看最新周：{{ weeks[0].week_label }}
      </a>
    </div>
  {% else %}
    <p class="empty">暂时没有抓取到任何数据，请先运行一次 <code>python run_daily.py</code>。</p>
  {% endif %}
{% endblock %}
"""

WEEK_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
  {% if week_data and week_data.get('sites') %}
    <h2 style="color:#111827;margin-bottom:1.5rem;padding-bottom:0.5rem;border-bottom:2px solid #e5e7eb;">
      {{ week_label }}
    </h2>
    {% for site_block in week_data.get('sites', []) %}
      {% set site_name = site_block.get('site', 'Unknown') %}
      {% set site_id = site_name.replace('.', '').lower() %}
      {% set is_organization = site_name == 'organizations' %}
      {% if is_organization %}
        {% set site_id = 'organizations' %}
        {% set display_name = '头部玩家' %}
      {% elif 'zhihu' in site_id %} 
        {% set site_id = 'zhihu' %}
        {% set display_name = site_name %}
      {% elif 'github' in site_id %} 
        {% set site_id = 'github' %}
        {% set display_name = site_name %}
      {% elif 'huggingface' in site_id %} 
        {% set site_id = 'huggingface' %}
        {% set display_name = site_name %}
      {% elif 'arxiv' in site_id %} 
        {% set site_id = 'arxiv' %}
        {% set display_name = site_name %}
      {% else %}
        {% set display_name = site_name %}
      {% endif %}
      <article class="card" id="{{ site_id }}" {% if is_organization %}style="border-left: 4px solid #10b981;"{% endif %}>
        <h2>{% if is_organization %}🏢 {{ display_name }}{% else %}{{ display_name }}{% endif %}</h2>
        <small>{{ site_block.get('site_summary', '') }}</small>
        {% if site_block.get('items') and site_block.get('items')|length > 0 %}
          <ul class="item-list">
            {% for item in site_block.get('items', []) %}
              <li style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem;">
                  <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                      <a href="{{ item.get('url', '#') }}" target="_blank" rel="noopener noreferrer" style="font-weight: 500; font-size: 1rem; line-height: 1.5; word-wrap: break-word; display: block;">{{ item.get('title') or item.get('url', '#') }}</a>
                      {% if is_organization and item.get('organization') %}
                        <span style="font-size: 0.75rem; color: #6b7280; background: #f3f4f6; padding: 0.25rem 0.5rem; border-radius: 0.25rem; white-space: nowrap;">{{ item.get('organization') }}</span>
                      {% endif %}
                    </div>
                    {% if site_block.get('site') == 'arxiv.org' %}
                      <div style="font-size:0.85rem;color:#6b7280;margin-top:0.25rem;margin-bottom:0.5rem;line-height:1.6;">
                        {% if item.get('published') %}
                          <span style="margin-right:1rem;">📅 {{ item.get('published')[:10] }}</span>
                        {% endif %}
                        {% if item.get('authors') %}
                          <span style="margin-right:1rem;">👤 {{ item.get('authors')|join(', ') }}</span>
                        {% endif %}
                      </div>
                    {% endif %}
                    {% if site_block.get('site') == 'arxiv.org' and item.get('abstract_zh') %}
                      <div style="font-size:0.9rem;color:#374151;margin-top:0.5rem;line-height:1.6;padding:0.75rem;background:#f9fafb;border-radius:0.5rem;">
                        <strong style="color:#111827;">摘要：</strong>{{ item.get('abstract_zh') }}
                      </div>
                    {% elif site_block.get('site') == 'zhihu.com' and item.get('snippet') %}
                      <div style="font-size:0.9rem;color:#374151;margin-top:0.5rem;line-height:1.6;padding:0.75rem;background:#f0f9ff;border-left:3px solid #3b82f6;border-radius:0.375rem;">
                        {{ item.get('snippet') }}
                      </div>
                    {% elif site_block.get('site') == 'github.com' and item.get('snippet') %}
                      <div style="font-size:0.9rem;color:#374151;margin-top:0.5rem;line-height:1.6;padding:0.75rem;background:#f9fafb;border-left:3px solid #6b7280;border-radius:0.375rem;">
                        {{ item.get('snippet') }}
                      </div>
                    {% elif item.get('snippet') %}
                      <div style="font-size:0.85rem;color:#6b7280;margin-top:0.5rem;line-height:1.5;">{{ item.get('snippet') }}</div>
                    {% endif %}
                  </div>
                </div>
              </li>
            {% endfor %}
          </ul>
        {% else %}
          <p class="empty" style="padding: 1.5rem; text-align: center; color: #9ca3af; font-size: 0.95rem;">本周无更新</p>
        {% endif %}
      </article>
    {% endfor %}
  {% else %}
    <p class="empty">本周暂无数据。</p>
  {% endif %}
{% endblock %}
"""


app = Flask(__name__)
app.jinja_loader = DictLoader(
    {
        "base.html": BASE_TEMPLATE,
        "index.html": INDEX_TEMPLATE,
        "week.html": WEEK_TEMPLATE,
    }
)


@app.route("/api/github-stars")
def get_github_stars() -> Any:
    """获取 GitHub 仓库的 star 数量"""
    try:
        repo_owner = getattr(config, "GITHUB_REPO_OWNER", "Miracle1991")
        repo_name = getattr(config, "GITHUB_REPO_NAME", "vla-tracker")
        
        # 使用 GitHub API 获取仓库信息（不需要认证，公开 API）
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "stargazers_count": data.get("stargazers_count", 0),
                "success": True
            })
        else:
            return jsonify({
                "stargazers_count": 0,
                "success": False,
                "error": f"GitHub API 返回 {response.status_code}"
            })
    except Exception as e:
        return jsonify({
            "stargazers_count": 0,
            "success": False,
            "error": str(e)
        })


@app.route("/")
def index() -> Any:
    """首页：显示周列表"""
    weeks = _build_week_list()
    current_week = weeks[0]["week_key"] if weeks else None
    
    # 获取 GitHub 仓库 URL
    repo_owner = getattr(config, "GITHUB_REPO_OWNER", "Miracle1991")
    repo_name = getattr(config, "GITHUB_REPO_NAME", "vla-tracker")
    github_repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    
    return render_template(
        "index.html",
        weeks=weeks,
        week_data_map={},
        current_week=current_week,
        github_repo_url=github_repo_url,
    )


@app.route("/week/<week_key>")
@app.route("/<week_key>.html")
def week_view(week_key: str) -> Any:
    """按周查看（支持 /week/<week_key> 和 /<week_key>.html 两种格式）"""
    weeks = _build_week_list()
    
    # 如果 URL 是 .html 格式，去掉 .html 后缀
    if week_key.endswith('.html'):
        week_key = week_key[:-5]
    
    # 找到对应的周
    target_week = None
    for week in weeks:
        if week["week_key"] == week_key:
            target_week = week
            break
    
    if not target_week:
        abort(404)
    
    try:
        dt = datetime.strptime(week_key, "%Y-%m-%d")
        week_data = load_week_results(dt)
    except Exception:
        week_data = None
    
    # 获取 GitHub 仓库 URL
    repo_owner = getattr(config, "GITHUB_REPO_OWNER", "Miracle1991")
    repo_name = getattr(config, "GITHUB_REPO_NAME", "vla-tracker")
    github_repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    
    return render_template(
        "week.html",
        weeks=weeks,
        week_data=week_data or {},
        week_label=target_week["week_label"],
        current_week=week_key,
        github_repo_url=github_repo_url,
    )


@app.route("/run-daily", methods=["POST", "GET"])
def trigger_daily_update() -> Any:
    """
    触发每日数据更新。
    可以通过定时任务服务（如 cron-job.org）定期访问此端点来更新数据。
    
    为了安全，可以添加简单的认证（例如通过查询参数）。
    """
    # 简单的认证（可选）：通过 ?token=xxx 验证
    import os
    expected_token = os.environ.get("UPDATE_TOKEN", None)
    if expected_token:
        token = request.args.get("token")
        if token != expected_token:
            return {"error": "Unauthorized"}, 401
    
    try:
        from run_daily import run_once
        run_once()
        return {"status": "success", "message": "Daily update completed"}
    except ImportError:
        return {"error": "Update function not available"}, 500
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    # 生产环境使用环境变量 PORT，开发环境默认 5000
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

