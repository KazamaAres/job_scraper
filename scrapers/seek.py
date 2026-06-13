import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urlencode, quote_plus

logger = logging.getLogger(__name__)

BASE_URL = "https://www.seek.co.nz"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-NZ,en;q=0.9",
}


def _build_url(keyword: str, location: str, page: int = 1) -> str:
    params = {"q": keyword, "where": location, "page": page}
    return f"{BASE_URL}/{quote_plus(keyword.replace(' ', '-'))}-jobs/in-{quote_plus(location.replace(' ', '-'))}?{urlencode({'page': page})}"


def _parse_job_card(card) -> dict | None:
    try:
        title_tag = card.select_one("a[data-automation='jobTitle']")
        company_tag = card.select_one("a[data-automation='jobCompany']")
        location_tag = card.select_one("a[data-automation='jobLocation']")
        salary_tag = card.select_one("span[data-automation='jobSalary']")
        date_tag = card.select_one("span[data-automation='jobListingDate']")

        if not title_tag:
            return None

        href = title_tag.get("href", "")
        link = href if href.startswith("http") else BASE_URL + href

        return {
            "title": title_tag.get_text(strip=True),
            "company": company_tag.get_text(strip=True) if company_tag else "",
            "location": location_tag.get_text(strip=True) if location_tag else "",
            "salary": salary_tag.get_text(strip=True) if salary_tag else "",
            "link": link,
            "date": date_tag.get_text(strip=True) if date_tag else "",
            "source": "seek.co.nz",
        }
    except Exception as e:
        logger.warning(f"Failed to parse job card: {e}")
        return None


def scrape_seek(keyword: str, location: str = "Auckland", max_pages: int = 3) -> list[dict]:
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, max_pages + 1):
        params = {"q": keyword, "where": location, "page": page}
        url = f"{BASE_URL}/jobs?" + urlencode(params)
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Seek request failed for '{keyword}' page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Seek renders job cards with data-automation attribute
        cards = soup.select("article[data-automation='normalJob'], article[data-automation='featuredJob']")
        if not cards:
            # Fallback selector for alternate page structure
            cards = soup.select("div[data-automation='jobCard']")

        if not cards:
            logger.debug(f"No cards found for '{keyword}' page {page}, stopping.")
            break

        for card in cards:
            job = _parse_job_card(card)
            if job:
                jobs.append(job)

        logger.info(f"Seek: '{keyword}' page {page} — {len(cards)} cards found")
        time.sleep(1.5)

    return jobs


def scrape_all_keywords(keywords: list[str], location: str = "Auckland") -> list[dict]:
    all_jobs = []
    seen_links = set()

    for keyword in keywords:
        logger.info(f"Scraping Seek for: {keyword}")
        jobs = scrape_seek(keyword, location)
        for job in jobs:
            if job["link"] not in seen_links:
                seen_links.add(job["link"])
                all_jobs.append(job)
        time.sleep(2)

    logger.info(f"Seek total unique jobs: {len(all_jobs)}")
    return all_jobs
