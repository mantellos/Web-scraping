import math
import re

WEIGHTS = {
    "cost": 0.40,
    "duration": 0.30,
    "difficulty": 0.20,
    "language": 0.10,
}


def _parse_cost(value: str) -> float | None:
    if not value or not str(value).strip():
        return None
    v = str(value).strip().lower()
    if v in ("free", "0", "δωρεάν"):
        return 0.0
    m = re.search(r"[\d,.]+", v)
    if m:
        try:
            return float(m.group().replace(",", "."))
        except ValueError:
            return None
    return None


def _parse_duration_days(value: str) -> float | None:
    if not value or not str(value).strip():
        return None
    v = str(value).strip().lower()
    m_months = re.search(r"(\d+)\s*month", v)
    m_weeks = re.search(r"(\d+)\s*week", v)
    m_days = re.search(r"(\d+)\s*day", v)
    if m_months:
        return float(m_months.group(1)) * 30
    if m_weeks:
        return float(m_weeks.group(1)) * 7
    if m_days:
        return float(m_days.group(1))
    return None


def _parse_difficulty(value: str) -> float | None:
    if not value or not str(value).strip():
        return None
    v = str(value).strip().lower()
    if any(token in v for token in ["introductory", "beginner", "easy", "1"]):
        return 0.25
    if any(token in v for token in ["intermediate", "medium", "transitional", "2"]):
        return 0.50
    if any(token in v for token in ["advanced", "hard", "expert", "3"]):
        return 1.00
    return None


def _parse_language(value: str) -> float | None:
    if not value or not str(value).strip():
        return None
    return 1.0 if "english" in str(value).strip().lower() else 0.5


def compute_score(course: dict) -> float:
    raw = {
        "cost": _parse_cost(course.get("cost", "")),
        "duration": _parse_duration_days(course.get("duration", "")),
        "difficulty": _parse_difficulty(course.get("difficulty", "")),
        "language": _parse_language(course.get("language", "")),
    }
    if raw["cost"] is not None:
        raw["cost"] = math.exp(-raw["cost"] / 200.0)
    if raw["duration"] is not None:
        raw["duration"] = min(raw["duration"] / 180.0, 1.0)
    available = {k: v for k, v in raw.items() if v is not None}
    if not available:
        return 0.0
    total_weight = sum(WEIGHTS[k] for k in available)
    score = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight
    return round(score * 100, 2)

def get_categories(courses: list[dict]) -> list[str]:
    """Επιστρέφει ταξινομημένη λίστα μοναδικών κατηγοριών."""
    cats = sorted({
        c.get("category", "").strip()
        for c in courses
        if c.get("category", "").strip()
    })
    return cats

def rank_courses(
        courses: list[dict],
        top_n: int = 3,
        category: str | None = None,
) -> list[dict]:
    """
    Επιστρέφει τα top_n μαθήματα με το υψηλότερο composite score.
    Αν δοθεί category, φιλτράρει πρώτα μόνο αυτή την κατηγορία.
    """
    pool = courses
    if category and category.strip():
        pool = [
            c for c in courses
            if c.get("category", "").strip().lower() == category.strip().lower()
        ]

    scored = []
    for course in pool:
        item = dict(course)
        item["composite_score"] = compute_score(item)
        scored.append(item)

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored[:top_n]
