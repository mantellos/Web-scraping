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
        "url": "https://api.coursera.org/api/courses.v1?fields=name,description,workload,primaryLanguages,language,slug,courseType&limit=10",
        "key": "elements",
        "headers": {},
    },
]


def _format_time_to_complete(value) -> str:
    if value is None or value == "":
        return ""
    try:
        minutes = int(float(value))
    except (TypeError, ValueError):
        return ""
    if minutes <= 0:
        return ""
    hours = minutes // 60
    if hours > 0:
        return f"{hours} hours"
    return f"{minutes} minutes"


def _normalize_api_duration(raw_course: dict, source_url: str) -> str:
    if "stepik.org" in source_url:
        workload = str(raw_course.get("workload", "") or "").strip()
        if workload:
            return workload
        duration = raw_course.get("duration")
        if duration:
            return str(duration).strip()
        return _format_time_to_complete(raw_course.get("time_to_complete"))

    if "coursera.org" in source_url:
        workload = str(raw_course.get("workload", "") or "").strip()
        if workload:
            return workload
        duration = raw_course.get("duration")
        if duration:
            return str(duration).strip()
        return ""

    if "futurelearn.com" in source_url:
        duration = raw_course.get("duration")
        if duration:
            return str(duration).strip()
        return ""

    duration = raw_course.get("duration")
    if duration:
        return str(duration).strip()
    return ""


def _normalize_course_data(raw_course: dict, source_url: str) -> dict:
    """Map provider-specific course payload to a standard dict schema.

       The normalized schema contains the following keys: ``title``,
       ``provider``, ``category``, ``difficulty``, ``cost``, ``duration``,
       and ``language``.

       Args:
           raw_course: Raw course payload from a provider API.
           source_url: The provider API URL to infer provider-specific keys.

       Returns:
           A dictionary with normalized course fields.
       """
    if "coursera.org" in source_url:
        return {
            "title": raw_course.get("name", "Unknown Course"),
            "provider": raw_course.get("provider", "Coursera"),
            "category": raw_course.get("courseType", ""),
            "difficulty": raw_course.get("level", "Not specified"),
            "cost": str(raw_course.get("price", "")),
            "duration": _normalize_api_duration(raw_course, source_url),
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
                "duration": _normalize_api_duration(data, source_url),
                "language": data.get("language", ""),
            }
    if "stepik.org" in source_url:
        return {
            "title": raw_course.get("title", "Stepik Course"),
            "provider": raw_course.get("provider", "Stepik"),
            "category": raw_course.get("subject", raw_course.get("category", "")),
            "difficulty": raw_course.get("level", "Not specified"),
            "cost": str(raw_course.get("price", "")),
            "duration": _normalize_api_duration(raw_course, source_url),
            "language": raw_course.get("primaryLanguages", ""),
        }
    return {
        "title": raw_course.get("name", raw_course.get("title", "Unknown Course")),
        "provider": raw_course.get("provider", "Unknown Provider"),
        "category": raw_course.get("courseType", raw_course.get("subject", "")),
        "difficulty": raw_course.get("level", "Not specified"),
        "cost": str(raw_course.get("price", "")),
        "duration": _normalize_api_duration(raw_course, source_url),
        "language": raw_course.get("primaryLanguages", raw_course.get("language", "")),
    }


def fetch_api_data() -> list[dict]:
    """Fetch course lists from configured API endpoints and normalize them.

        The function iterates over the global ``URLS`` list, performs HTTP GET
        requests, parses JSON responses and normalizes each course record using
        _normalize_course_data.

        Returns:
            A list of normalized course dictionaries.
        """
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