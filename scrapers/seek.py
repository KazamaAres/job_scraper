import random
import time
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://nz.seek.com"
CHALICE_API = "https://chalice-search-api.cloud.seek.com.au/search"

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-NZ,en;q=0.9",
    "seek-request-brand": "seek",
    "seek-request-country": "NZ",
    "X-Api-Key": "2c72f592-b8b8-4ff4-bb08-e2c66f00ed61",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin": "https://nz.seek.com",
    "Referer": "https://nz.seek.com/",
}


def _parse_job(item: dict) -> dict:
    job_id = item.get("id", "")
    salary = item.get("salary", "")
    if isinstance(salary, dict):
        salary = salary.get("label", "") or salary.get("display", "")
    listing_date = item.get("listingDate", "")
    if listing_date and len(listing_date) >= 10:
        listing_date = listing_date[:10]
    return {
        "title": item.get("title", ""),
        "company": (item.get("advertiser") or {}).get("description", ""),
        "location": item.get("location", "") or item.get("suburb", ""),
        "salary": str(salary) if salary else "",
        "date": listing_date,
        "link": f"{BASE_URL}/job/{job_id}" if job_id else "",
        "source": "seek.co.nz",
    }


def scrape_seek(keyword: str, location: str = "Auckland", max_pages: int = 3) -> list[dict]:
    jobs = []
    for page in range(1, max_pages + 1):
        params = {
            "siteKey": "NZ-Main",
            "sourcesystem": "houston",
            "keywords": keyword,
            "where": location,
            "page": page,
            "pageSize": 22,
            "locale": "en-NZ",
        }
        try:
            resp = requests.get(
                CHALICE_API, params=params, headers=_HEADERS, timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as e:
            logger.error(f"Seek API HTTP {e.response.status_code} for '{keyword}' page {page}")
            break
        except Exception as e:
            logger.error(f"Seek API failed for '{keyword}' page {page}: {e}")
            break

        items = data.get("data", [])
        if not items:
            logger.debug(f"Seek: '{keyword}' page {page} — no results, stopping")
            break

        for item in items:
            job = _parse_job(item)
            if job["link"]:
                jobs.append(job)

        logger.info(f"Seek: '{keyword}' page {page} — {len(items)} jobs")
        time.sleep(random.uniform(0.5, 1.5))

    return jobs


def scrape_all_keywords(keywords: list[str], location: str = "Auckland") -> list[dict]:
    all_jobs = []
    seen_links: set[str] = set()

    for keyword in keywords:
        logger.info(f"Scraping Seek for: {keyword}")
        jobs = scrape_seek(keyword, location)
        for job in jobs:
            link = job.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                all_jobs.append(job)
        time.sleep(random.uniform(1.0, 2.0))

    logger.info(f"Seek total unique jobs: {len(all_jobs)}")
    return all_jobs
