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
}


def _clean_text(value: str) -> str:
    return value.strip() if isinstance(value, str) else ""


def _best_text(tags):
    for tag in tags:
        text = _clean_text(tag.get_text())
        if text:
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
        "duration": "",
        "language": "",
    }

    for keyword, target in FIELD_MAP.items():
        tag = soup.find(string=re.compile(re.escape(keyword), re.IGNORECASE))
        if tag:
            parent = tag.find_parent()
            if parent is not None:
                sibling = parent.find_next_sibling()
                if sibling is not None:
                    data[target] = _clean_text(sibling.get_text(strip=True))
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
