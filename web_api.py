import requests

URLS = [
    {
        "name": "Stepik_API",
        "url": "https://stepik.org/api/courses?search=python&language=en&is_public=true",
        "key": "courses",
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    },
    {
        "name": "Coursera_API",
        "url": "https://api.coursera.org/api/courses.v1?fields=name,description&limit=10",
        "key": "elements",
        "headers": {},
    },
]


def _normalize_course_data(raw_course: dict, source_url: str) -> dict:
    if "coursera.org" in source_url:
        return {
            "title": raw_course.get("name", "Unknown Course"),
            "provider": raw_course.get("provider", "Coursera"),
            "category": raw_course.get("courseType", ""),
            "difficulty": raw_course.get("level", "Not specified"),
            "cost": str(raw_course.get("price", "")),
            "duration": raw_course.get("duration", ""),
            "language": raw_course.get("primaryLanguages", ""),
        }
    if "futurelearn.com" in source_url:
        data = raw_course.get("degree", raw_course.get("course", raw_course))
        if isinstance(data, dict):
            org = data.get("organisation", {}).get("name") if isinstance(data.get("organisation"), dict) else None
            return {
                "title": data.get("title", data.get("name", "FutureLearn Course")),
                "provider": org or "FutureLearn",
                "category": data.get("subject", data.get("category", "")),
                "difficulty": data.get("level", "Not specified"),
                "cost": str(data.get("price", "")),
                "duration": data.get("duration", ""),
                "language": data.get("language", ""),
            }
    if "stepik.org" in source_url:
        return {
            "title": raw_course.get("title", "Stepik Course"),
            "provider": raw_course.get("provider", "Stepik"),
            "category": raw_course.get("subject", raw_course.get("category", "")),
            "difficulty": raw_course.get("level", "Not specified"),
            "cost": str(raw_course.get("price", "")),
            "duration": raw_course.get("duration", ""),
            "language": raw_course.get("primaryLanguages", ""),
        }
    return {
        "title": raw_course.get("name", raw_course.get("title", "Unknown Course")),
        "provider": raw_course.get("provider", "Unknown Provider"),
        "category": raw_course.get("courseType", raw_course.get("subject", "")),
        "difficulty": raw_course.get("level", "Not specified"),
        "cost": str(raw_course.get("price", "")),
        "duration": raw_course.get("duration", ""),
        "language": raw_course.get("primaryLanguages", raw_course.get("language", "")),
    }


def fetch_api_data() -> list[dict]:
    all_courses = []
    for item in URLS:
        try:
            response = requests.get(item["url"], headers=item.get("headers", {}), timeout=7, verify=False)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            print(f"[{item['name']}] API Error: {type(exc).__name__} - {exc}")
            continue
        except ValueError as exc:
            print(f"[{item['name']}] Invalid JSON response: {exc}")
            continue
        raw_courses = data.get(item["key"], [])
        if isinstance(raw_courses, dict):
            raw_courses = [raw_courses]
        if not raw_courses:
            print(f"[{item['name']}] No courses found in API response.")
            continue
        for raw_course in raw_courses:
            normalized = _normalize_course_data(raw_course, item["url"])
            normalized["provider"] = normalized.get("provider") or item["name"].split("_")[0]
            all_courses.append(normalized)
        print(f"[{item['name']}] Retrieved {len(raw_courses)} courses.")
    return all_courses
