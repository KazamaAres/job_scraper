import json
import logging
import sys
from pathlib import Path

from config import SEEK_KEYWORDS, SEEK_LOCATION, SEEN_JOBS_FILE
from scrapers.seek import scrape_all_keywords
from scrapers.skykiwi import scrape_skykiwi
from matcher import match_jobs
from notifier import save_and_open

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


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
    logger.info("=== Job Scraper started ===")

    seen = load_seen_jobs(SEEN_JOBS_FILE)
    logger.info(f"Loaded {len(seen)} previously seen jobs")

    # 1. Scrape
    logger.info("Scraping Seek...")
    seek_jobs = scrape_all_keywords(SEEK_KEYWORDS, location=SEEK_LOCATION)

    logger.info("Scraping SkyKiwi...")
    skykiwi_jobs = scrape_skykiwi(max_pages=5, fetch_details=True)

    all_jobs = seek_jobs + skykiwi_jobs
    logger.info(f"Total scraped: {len(all_jobs)} jobs")

    # 2. Match
    matched = match_jobs(all_jobs)
    logger.info(f"Matched: {len(matched)} jobs")

    # 3. Deduplicate
    new_jobs = deduplicate(matched, seen)
    logger.info(f"New (unseen): {len(new_jobs)} jobs")

    # 4. Save HTML and open browser
    if new_jobs:
        save_and_open(new_jobs)
        save_seen_jobs(seen, SEEN_JOBS_FILE)
        logger.info(f"Saved {len(seen)} total seen URLs")
    else:
        logger.info("No new jobs found.")

    logger.info("=== Job Scraper finished ===")


if __name__ == "__main__":
    main()
