import json
import logging
import os
import sys
from pathlib import Path

from config import SEEK_KEYWORDS, SEEK_LOCATION, SEEN_JOBS_FILE
from scrapers.seek import scrape_all_keywords
from scrapers.skykiwi import scrape_skykiwi
from matcher import match_jobs
from notifier import save_html, save_and_open

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

IS_CI = os.getenv("CI") == "true"


def load_seen_jobs(path: str) -> set[str]:
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen: set[str], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)


def deduplicate(jobs: list[dict], seen: set[str]) -> list[dict]:
    new_jobs = []
    for job in jobs:
        url = job.get("link", "")
        if url and url not in seen:
            seen.add(url)
            new_jobs.append(job)
    return new_jobs


def main():
    logger.info(f"=== Job Scraper started (CI={IS_CI}) ===")

    try:
        logger.info("Scraping Seek...")
        seek_jobs = scrape_all_keywords(SEEK_KEYWORDS, location=SEEK_LOCATION)
    except Exception as e:
        logger.error(f"Seek scraping failed: {e}")
        seek_jobs = []

    try:
        logger.info("Scraping SkyKiwi...")
        skykiwi_jobs = scrape_skykiwi(max_pages=5, fetch_details=True)
    except Exception as e:
        logger.error(f"SkyKiwi scraping failed: {e}")
        skykiwi_jobs = []

    all_jobs = seek_jobs + skykiwi_jobs
    logger.info(f"Total scraped: {len(all_jobs)} jobs")

    matched = match_jobs(all_jobs)
    logger.info(f"Matched: {len(matched)} jobs")

    if IS_CI:
        # In CI, always write HTML with all matched jobs (no deduplication)
        save_html(matched)
    else:
        # Local: deduplicate against seen jobs, open browser for new ones
        seen = load_seen_jobs(SEEN_JOBS_FILE)
        logger.info(f"Loaded {len(seen)} previously seen jobs")

        new_jobs = deduplicate(matched, seen)
        logger.info(f"New (unseen): {len(new_jobs)} jobs")

        if new_jobs:
            save_and_open(new_jobs)
            save_seen_jobs(seen, SEEN_JOBS_FILE)
            logger.info(f"Saved {len(seen)} total seen URLs")
        else:
            logger.info("No new jobs found.")

    logger.info("=== Job Scraper finished ===")


if __name__ == "__main__":
    main()
