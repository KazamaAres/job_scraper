import random
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# seek.co.nz now redirects to nz.seek.com
BASE_URL = "https://nz.seek.com"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]


def _headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-NZ,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }


def _parse_card(card) -> dict | None:
    try:
        title_tag = card.select_one("a[data-automation='jobTitle']")
        if not title_tag:
            return None

        href = title_tag.get("href", "")
        link = href if href.startswith("http") else BASE_URL + href

        company_tag = card.select_one("a[data-automation='jobCompany']")
        location_tag = card.select_one("a[data-automation='jobLocation']")
        salary_tag = card.select_one("span[data-automation='jobSalary']")
        date_tag = card.select_one("span[data-automation='jobListingDate']")

        return {
            "title": title_tag.get_text(strip=True),
            "company": company_tag.get_text(strip=True) if company_tag else "",
            "location": location_tag.get_text(strip=True) if location_tag else "",
            "salary": salary_tag.get_text(strip=True) if salary_tag else "",
            "date": date_tag.get_text(strip=True) if date_tag else "",
            "link": link,
            "source": "seek.co.nz",
        }
    except Exception as e:
        logger.warning(f"Failed to parse card: {e}")
        return None


def scrape_seek(keyword: str, location: str = "Auckland", max_pages: int = 3) -> list[dict]:
    session = requests.Session()

    # Warm up session: visit homepage to acquire cookies and look like a real browser
    try:
        session.headers.update(_headers())
        session.get(BASE_URL, timeout=10)
        time.sleep(random.uniform(1.0, 2.0))
    except Exception:
        pass

    jobs = []
    for page in range(1, max_pages + 1):
        session.headers.update(_headers())
        url = f"{BASE_URL}/jobs?" + urlencode({"q": keyword, "where": location, "page": page})
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Seek request failed for '{keyword}' page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(
            "article[data-automation='normalJob'], article[data-automation='featuredJob']"
        )
        if not cards:
            cards = soup.select("div[data-automation='jobCard']")
        if not cards:
            logger.debug(f"No cards found for '{keyword}' page {page}, stopping.")
            break

        for card in cards:
            job = _parse_card(card)
            if job:
                jobs.append(job)

        logger.info(f"Seek: '{keyword}' page {page} — {len(cards)} cards")
        time.sleep(random.uniform(3.0, 6.0))

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
        time.sleep(random.uniform(2.0, 5.0))

    logger.info(f"Seek total unique jobs: {len(all_jobs)}")
    return all_jobs
