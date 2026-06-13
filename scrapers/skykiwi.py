import requests
from bs4 import BeautifulSoup
import re
import time
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://nz.skykiwi.com"
JOBS_URL = f"{BASE_URL}/class/type-job.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": BASE_URL,
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def _parse_listing_page(soup) -> list[dict]:
    jobs = []
    # SkyKiwi listing rows — adjust selectors if the site updates its structure
    items = soup.select("ul.info-list li, div.list-item, table.list-table tr")

    for item in items:
        link_tag = item.select_one("a[href]")
        if not link_tag:
            continue

        href = link_tag.get("href", "")
        link = href if href.startswith("http") else BASE_URL + href
        title = link_tag.get_text(strip=True)

        date_tag = item.select_one("span.time, span.date, td.date")
        date = date_tag.get_text(strip=True) if date_tag else ""

        summary_tag = item.select_one("p.desc, p.summary, td.desc")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""

        if title:
            jobs.append({
                "title": title,
                "link": link,
                "date": date,
                "summary": summary,
                "email": _extract_email(summary),
                "source": "skykiwi.com",
            })

    return jobs


def _fetch_detail(session: requests.Session, job: dict) -> dict:
    try:
        resp = session.get(job["link"], timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        content_tag = soup.select_one("div.content, div.article-content, div#content")
        if content_tag:
            text = content_tag.get_text(separator=" ", strip=True)
            job["summary"] = text[:500]
            job["email"] = _extract_email(text) or job["email"]
    except Exception as e:
        logger.warning(f"Failed to fetch SkyKiwi detail {job['link']}: {e}")
    return job


def scrape_skykiwi(max_pages: int = 5, fetch_details: bool = True) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    all_jobs = []
    seen_links = set()

    for page in range(1, max_pages + 1):
        url = JOBS_URL if page == 1 else f"{JOBS_URL}?page={page}"
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"SkyKiwi request failed on page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = _parse_listing_page(soup)

        if not jobs:
            logger.debug(f"SkyKiwi page {page}: no items found, stopping.")
            break

        for job in jobs:
            if job["link"] not in seen_links:
                seen_links.add(job["link"])
                all_jobs.append(job)

        logger.info(f"SkyKiwi page {page}: {len(jobs)} items")
        time.sleep(1.5)

    if fetch_details:
        for job in all_jobs:
            if not job.get("summary"):
                _fetch_detail(session, job)
                time.sleep(1)

    logger.info(f"SkyKiwi total unique jobs: {len(all_jobs)}")
    return all_jobs
