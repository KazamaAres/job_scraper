from config import MATCH_KEYWORDS


def match_jobs(jobs: list[dict], keywords: list[str] | None = None) -> list[dict]:
    """Return jobs whose title or summary contains at least one keyword (case-insensitive)."""
    kw_list = [k.lower() for k in (keywords or MATCH_KEYWORDS)]
    matched = []
    for job in jobs:
        haystack = " ".join([
            job.get("title", ""),
            job.get("company", ""),
            job.get("summary", ""),
        ]).lower()

        if any(kw in haystack for kw in kw_list):
            matched.append(job)

    return matched
