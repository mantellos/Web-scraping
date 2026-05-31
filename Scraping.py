import json
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SITES = [
    {
        "url": "https://pll.harvard.edu/course/using-python-research",
        "provider": "Harvard University",
        "classes": ["topics--teaser", "field__item"],
    },
    {
        "url": "https://pll.harvard.edu/course/cs50-lawyers",
        "provider": "Harvard University",
        "classes": ["topics--teaser", "field__item"],
    },
    {
        "url": "https://online.yale.edu/programs/foundations-animal-ethics",
        "provider": "Yale University",
        "classes": ["badge badge-primary"],
    },
    {
        "url": "https://online.yale.edu/programs/foundations-of-bioethics",
        "provider": "Yale University",
        "classes": ["badge badge-primary"],
    },
    {
        "url": "https://www.tuni.fi/en/tau/open-university/course-offering/5g-mobile-communications",
        "provider": "Tampere University",
        "classes": ["badge badge-primary"],
    },
]

FIELD_MAP = {
    "course language": "language",
    "language": "language",
    "difficulty": "difficulty",
    "price": "cost",
    "duration": "duration",
    "study fields": "category",
    "subject": "category",
    "time commitment": "duration",
    "course length": "duration",
    "workload": "duration",
}


def _clean_text(value: str) -> str:
    return value.strip() if isinstance(value, str) else ""


def _best_text(tags):
    for tag in tags:

        text = _clean_text(tag.get_text())
        if text:
            return text
    return ""


def _parse_iso_duration(value: str) -> str:
    if not value:
        return ""
    match = re.match(
        r"^P(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?)?$",
        value,
        re.IGNORECASE,
    )
    if not match:
        return ""
    groups = match.groupdict()
    if groups["weeks"]:
        return f"{groups['weeks']} weeks"
    if groups["days"]:
        return f"{groups['days']} days"
    hours = groups.get("hours")
    minutes = groups.get("minutes")
    if hours and minutes:
        return f"{hours} hours {minutes} minutes"
    if hours:
        return f"{hours} hours"
    if minutes:
        return f"{minutes} minutes"
    return ""


def _extract_duration_from_json_ld(soup: BeautifulSoup) -> str:
    """Extract duration from JSON-LD script blocks when available.

        Args:
            soup: BeautifulSoup object of the page HTML.

        Returns:
            A normalized duration string if found, otherwise empty string.
        """
    for script in soup.find_all("script", type="application/ld+json"):
        content = script.string
        if not content:
            continue
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            continue
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            duration = item.get("duration") or item.get("timeRequired")
            result = _parse_iso_duration(duration)
            if result:
                return result
    return ""


def _extract_duration_from_script_text(html: str) -> str:
    """Try to locate an ISO duration embedded in JavaScript or inline text.

       Args:
           html: Raw HTML text of the page.

       Returns:
           A parsed duration string or empty string if none found.
       """
    match = re.search(r"duration\s*[:=]\s*['\"](P[T0-9HMS]+)['\"]", html, re.IGNORECASE)
    if match:
        return _parse_iso_duration(match.group(1))
    return ""


def _find_scraped_duration(soup: BeautifulSoup, html: str) -> str:
    """Locate the most likely duration on a scraped page.

        The function attempts several heuristics in order: JSON-LD, script
        text, nearby sibling elements for keywords, and common CSS classes.

        Args:
            soup: BeautifulSoup object for the page.
            html: Raw HTML text for fallback regex searching.

        Returns:
            A duration string or empty string if none matched.
        """
    # Try known page structures and JSON-LD first.
    result = _extract_duration_from_json_ld(soup)
    if result:
        return result
    result = _extract_duration_from_script_text(html)
    if result:
        return result

    for keyword in ["duration", "time commitment", "workload", "course length"]:
        tag = soup.find(string=re.compile(re.escape(keyword), re.IGNORECASE))
        if tag:
            parent = tag.find_parent()
            if parent is not None:
                sibling = parent.find_next_sibling()
                if sibling is not None:
                    duration_text = _clean_text(sibling.get_text(strip=True))
                    if duration_text:
                        return duration_text

    duration_tag = soup.find(class_=re.compile(r"data-grid-item__duration|field--name-field-duration|field--name-field-pace", re.IGNORECASE))
    if duration_tag:
        duration_text = _clean_text(duration_tag.get_text(strip=True))
        if duration_text:
            return duration_text

    for tag in soup.find_all(class_="field__item"):
        text = _clean_text(tag.get_text(strip=True))
        if re.search(r"\d+\s*(?:week|weeks|hour|hours|day|days|month|months|min|mins|minute|minutes)", text, re.IGNORECASE):
            return text
    return ""


def _normalize_scraped_course(data: dict) -> dict:
    return {
        "title": _clean_text(data.get("title", "")),
        "provider": _clean_text(data.get("provider", "")),
        "category": _clean_text(data.get("category", "")),
        "difficulty": _clean_text(data.get("difficulty", "")),
        "cost": _clean_text(data.get("cost", "")),
        "duration": _clean_text(data.get("duration", "")),
        "language": _clean_text(data.get("language", "")),
    }


def scrape_course(url: str, classes: list[str], provider: str) -> dict:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Scraping failed for {url}: {type(exc).__name__} {exc}")
        return _normalize_scraped_course({
            "title": "",
            "provider": provider,
            "category": "",
            "difficulty": "",
            "cost": "",
            "duration": "",
            "language": "",
        })

    soup = BeautifulSoup(response.text, "html.parser")
    data = {
        "title": _clean_text(soup.find("h1").get_text(strip=True)) if soup.find("h1") else "",
        "provider": provider,
        "category": "",
        "difficulty": "",
        "cost": "",
        "duration": _find_scraped_duration(soup, response.text),
        "language": "",
    }

    for keyword, target in FIELD_MAP.items():
        tag = soup.find(string=re.compile(re.escape(keyword), re.IGNORECASE))
        if tag:
            parent = tag.find_parent()
            if parent is not None:
                sibling = parent.find_next_sibling()
                if sibling is not None:
                    value = _clean_text(sibling.get_text(strip=True))
                    if value:
                        data[target] = value
                        continue

    for css_class in classes:
        if css_class == "field__item":
            items = soup.find_all(class_="field__item")
            if items:
                data["difficulty"] = _best_text(items)
        else:
            items = soup.find_all(class_=css_class.split())
            if items:
                data["category"] = _best_text(items)

    return _normalize_scraped_course(data)


def scrape_all_web_sources() -> list[dict]:
    courses = []
    for site in SITES:
        print(f"Scraping {site['url']}")
        courses.append(scrape_course(site["url"], site["classes"], site["provider"]))
    return courses


def main() -> None:
    courses = scrape_all_web_sources()
    print(f"Scraped {len(courses)} courses.")
    for course in courses:
        print(course)


if __name__ == "__main__":
    main()
