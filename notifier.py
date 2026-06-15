import logging
import subprocess
import webbrowser
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_FILE = "jobs_today.html"


def _build_html(jobs: list[dict]) -> str:
    today = date.today().strftime("%Y-%m-%d")

    cards = ""
    for job in jobs:
        salary = job.get("salary") or ""
        pub_date = job.get("date") or ""
        company = job.get("company") or ""
        location = job.get("location") or ""
        source = job.get("source") or ""
        link = job.get("link", "#")
        title = job.get("title", "")

        salary_html = f'<span class="tag salary">💰 {salary}</span>' if salary else ""
        date_html = f'<span class="tag date">📅 {pub_date}</span>' if pub_date else ""
        location_html = f'<span class="tag loc">📍 {location}</span>' if location else ""
        source_html = f'<span class="tag source">{source}</span>' if source else ""

        cards += f"""
        <div class="card">
          <a class="title" href="{link}" target="_blank">{title}</a>
          <div class="company">{company}</div>
          <div class="tags">{salary_html}{date_html}{location_html}{source_html}</div>
        </div>"""

    empty_msg = ""
    if not jobs:
        empty_msg = '<p style="text-align:center;color:#aaa;margin-top:48px">今日暂无新职位</p>'

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>今日职位推送 — {today}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #f0f2f5; color: #333; padding: 32px 16px; }}
    h1 {{ font-size: 22px; color: #1a1a2e; margin-bottom: 4px; }}
    .subtitle {{ color: #888; font-size: 14px; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
             gap: 16px; max-width: 1200px; margin: 0 auto; }}
    .card {{ background: #fff; border-radius: 12px; padding: 20px;
             box-shadow: 0 2px 8px rgba(0,0,0,.07); transition: box-shadow .2s; }}
    .card:hover {{ box-shadow: 0 6px 20px rgba(0,0,0,.12); }}
    .title {{ font-size: 16px; font-weight: 600; color: #1a0dab;
              text-decoration: none; line-height: 1.4; display: block; margin-bottom: 6px; }}
    .title:hover {{ text-decoration: underline; }}
    .company {{ font-size: 14px; color: #555; margin-bottom: 12px; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .tag {{ font-size: 12px; padding: 3px 8px; border-radius: 6px; }}
    .salary {{ background: #e6f4ea; color: #1e7e34; }}
    .date   {{ background: #fff3cd; color: #856404; }}
    .loc    {{ background: #e8f0fe; color: #1a73e8; }}
    .source {{ background: #f1f3f4; color: #5f6368; }}
    .footer {{ text-align: center; color: #aaa; font-size: 12px; margin-top: 32px; }}
  </style>
</head>
<body>
  <div style="max-width:1200px;margin:0 auto">
    <h1>📋 今日职位推送</h1>
    <p class="subtitle">{today} · 共 {len(jobs)} 个职位</p>
    <div class="grid">{cards}
    </div>
    {empty_msg}
    <p class="footer">由 job_scraper 自动生成 · {today}</p>
  </div>
</body>
</html>"""


def save_html(jobs: list[dict]) -> Path:
    """Write jobs_today.html and return the path. Does not open a browser."""
    html = _build_html(jobs)
    out = Path(OUTPUT_FILE).resolve()
    out.write_text(html, encoding="utf-8")
    logger.info(f"Saved {len(jobs)} jobs to {out}")
    return out


def save_and_open(jobs: list[dict]) -> bool:
    """Save jobs_today.html and try to open it in a browser (local use only)."""
    if not jobs:
        logger.info("No new jobs to save.")
        return False

    out = save_html(jobs)

    try:
        win_path = subprocess.check_output(["wslpath", "-w", str(out)]).decode().strip()
        subprocess.Popen(["cmd.exe", "/c", "start", win_path])
    except Exception:
        webbrowser.open(out.as_uri())

    return True
