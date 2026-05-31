import csv
import os
import re
from typing import Iterable

CSV_HEADERS = [
    "title",
    "provider",
    "category",
    "difficulty",
    "cost",
    "duration",
    "language",
]


def _get_first_value(raw: dict, keys: list[str], default: str = "") -> str:
    for key in keys:
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(value, list):
            if value:
                return str(value[0]).strip()
            continue
        if isinstance(value, str):
            if value.strip():
                return value.strip()
            continue
        if value is not None:
            return str(value).strip()
    return default


def _normalize_text(raw: dict, keys: list[str], default: str = "") -> str:
    return _get_first_value(raw, keys, default)


def _infer_category_by_title(title: str) -> str:
    if not title or title == "Unknown Title":
        return "Uncategorized"
    text = title.lower()
    keyword_map = {
        "Machine Learning": ["machine learning", "ml", "deep learning", "neural", "artificial intelligence", "ai"],
        "Data Science": ["data science", "data analysis", "analytics", "data mining", "data engineering"],
        "Programming": ["python", "java", "c++", "c#", "programming", "software", "code", "coding"],
        "Web Development": ["web development", "web design", "frontend", "backend", "javascript", "html", "css"],
        "Cloud": ["cloud", "aws", "azure", "gcp", "google cloud"],
        "Cybersecurity": ["security", "cybersecurity", "hacking", "network security"],
        "Business": ["business", "management", "marketing", "entrepreneurship", "finance"],
        "Ethics": ["ethics", "bioethics", "lawyers", "law", "ethics"],
        "Communication": ["communication", "communications", "speech", "presentation"],
        "Mathematics": ["mathematics", "math", "statistics", "algebra", "calculus"],
        "Design": ["design", "ux", "ui", "graphic"],
        "Health": ["health", "medicine", "medical", "bioethics", "biology"],
    }
    for category, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return "Uncategorized"


def _detect_language_by_title(title: str) -> str:
    if not title or title == "Unknown Title":
        return "Unknown"
    if re.search(r"[\u0370-\u03FF\u1F00-\u1FFF]", title):
        return "Greek"
    if re.search(r"[\u0400-\u04FF\u0500-\u052F]", title):
        return "Russian"
    if re.search(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", title):
        return "Arabic"
    return "English"


def _normalize_category(raw: dict, title: str) -> str:
    value = _get_first_value(raw, ["category", "courseType", "Θεματική κατηγορία", "subject", "Study fields"], "")
    if value:
        cleaned = value.strip()
        if cleaned.lower() not in ("uncategorized", "other", "not specified", ""):
            return cleaned.title()
    return _infer_category_by_title(title)


def _normalize_difficulty(raw: dict) -> str:
    source = _get_first_value(raw, ["difficulty", "level", "Επίπεδο δυσκολίας"], "")
    if not source:
        return "Unknown"
    low = source.strip().lower()
    if any(keyword in low for keyword in ["introductory", "beginner", "easy", "1"]):
        return "Beginner"
    if any(keyword in low for keyword in ["intermediate", "medium", "transitional", "2"]):
        return "Intermediate"
    if any(keyword in low for keyword in ["advanced", "expert", "hard", "3"]):
        return "Advanced"
    return source.strip().title()


def _normalize_language(raw: dict, title: str) -> str:
    source = _get_first_value(raw, ["language", "primaryLanguages", "primaryLanguage", "Γλώσσα διδασκαλίας"], "")
    if not source:
        return _detect_language_by_title(title)
    low = str(source).strip().lower()
    if low.startswith("en"):
        return "English"
    if low.startswith("el") or "greek" in low or "ελλην" in low:
        return "Greek"
    if low.startswith("ar") or "arabic" in low:
        return "Arabic"
    if low.startswith("ru") or "russian" in low or "рус" in low:
        return "Russian"
    if low.startswith("fr"):
        return "French"
    if low.startswith("de"):
        return "German"
    return str(source).strip().title()


def _normalize_cost(raw: dict) -> str:
    value = _get_first_value(raw, ["cost", "price", "Κόστος"], "")
    if not value:
        return "Free"
    low_val = str(value).strip().lower()
    if low_val in ("free", "0", "δωρεάν", "none", ""):
        return "Free"
    return str(value).strip()


def normalize_course_data(course_data: dict) -> dict:
    # Included fallback keys commonly populated by scraping frameworks
    title = _normalize_text(course_data, ["title", "name", "course_title", "Τίτλος μαθήματος", "Τίτλος"], "Unknown Title")
    provider = _normalize_text(course_data, ["provider", "Πάροχος / Πανεπιστήμιο", "Πάροχος", "institution"], "Unknown Provider")
    
    return {
        "title": title,
        "provider": provider,
        "category": _normalize_category(course_data, title),
        "difficulty": _normalize_difficulty(course_data),
        "cost": _normalize_cost(course_data),
        "duration": _normalize_text(course_data, ["duration", "length", "Διάρκεια", "time"], "Unknown Duration"),
        "language": _normalize_language(course_data, title),
    }


class CourseRepository:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._ensure_headers_exists()

    def _ensure_headers_exists(self) -> None:
        self._ensure_folder()
        if not os.path.isfile(self.csv_path):
            with open(self.csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()

    def _ensure_folder(self) -> None:
        folder = os.path.dirname(self.csv_path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)

    def get_headers(self) -> list[str]:
        return CSV_HEADERS
    
    def load_courses(self) -> list[dict]:
        courses: list[dict] = []
        if not os.path.isfile(self.csv_path):
            return courses
        try:
            with open(self.csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                
                if reader.fieldnames:
                    reader.fieldnames = [name.lstrip("\ufeff").strip() for name in reader.fieldnames]
               
                for row in reader:
                    if not row or not any(row.values()):
                        continue
                    
                    course_entry = {}
                    for key in CSV_HEADERS:
                        val = row.get(key)
                        course_entry[key] = str(val).strip() if val is not None else ""
                    
                    # Ensure we don't load entirely blank rows as valid courses
                    if course_entry["title"] and course_entry["title"] != "":
                        courses.append(course_entry)
        except Exception as e:
            print(f"[Repository Error] Failed reading storage CSV matrix: {e}")
            return courses
        return courses

    def save_courses(self, courses: Iterable[dict]) -> None:
        normalized = [normalize_course_data(course) for course in courses]
        self._ensure_folder()
        with open(self.csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(normalized)

    def append_courses(self, courses: Iterable[dict]) -> int:
        existing = self.load_courses()
        existing_titles = {
            course["title"].strip().lower() 
            for course in existing 
            if course.get("title") and course["title"].strip() != ""
        }
        
        normalized = []
        
        for raw_course in courses:
            course = normalize_course_data(raw_course)
            title_key = course["title"].strip().lower()
  
            if title_key not in existing_titles and title_key != "":
                normalized.append(course)
                existing_titles.add(title_key)
                
        if not normalized:
            return 0
            
        self._ensure_folder()
        file_exists = os.path.isfile(self.csv_path)
        
        with open(self.csv_path, mode="a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            if not file_exists or os.path.getsize(self.csv_path) == 0:
                writer.writeheader()
            writer.writerows(normalized)
            
        return len(normalized)

    def export_courses(self, filepath: str, courses: list[dict] | None = None) -> None:
        if courses is None:
            courses = self.load_courses()
        normalized = [normalize_course_data(course) for course in courses]
        folder = os.path.dirname(filepath)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(normalized)