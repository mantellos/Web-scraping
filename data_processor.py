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

_GREEK_HEADER_MAP: dict[str, str] = {
    "πεδίο": "title",
    "τίτλος": "title",
    "τίτλος μαθήματος": "title",
    "πάροχος / πανεπιστήμιο": "provider",
    "πάροχος": "provider",
    "θεματική κατηγορία": "category",
    "κατηγορία": "category",
    "επίπεδο δυσκολίας": "difficulty",
    "δυσκολία": "difficulty",
    "κόστος": "cost",
    "διάρκεια": "duration",
    "γλώσσα διδασκαλίας": "language",
    "γλώσσα": "language",
}

# Τα αγγλικά system keys για normalize στο load_courses()
_EN_HEADER_MAP: dict[str, str] = {
    "title": "title",
    "provider": "provider",
    "category": "category",
    "difficulty": "difficulty",
    "cost": "cost",
    "duration": "duration",
    "language": "language",
}

# Συνδυασμός και των δύο για χρήση στο normalize μόνο
_ALL_HEADER_MAP = {**_GREEK_HEADER_MAP, **_EN_HEADER_MAP}


def _is_transposed(first_field: str) -> bool:
    """True ΜΟΝΟ αν η πρώτη στήλη είναι ελληνικό label (πχ 'Πεδίο'), ΟΧΙ αν είναι 'title'."""
    key = first_field.lstrip("\ufeff").strip().lower()
    return key in _GREEK_HEADER_MAP and _GREEK_HEADER_MAP[key] == "title"


def _has_valid_header(csv_path: str) -> bool:
    """Ελέγχει αν η 1η γραμμή του CSV είναι το σωστό header."""
    try:
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            first = next(csv.reader(f), [])
        cleaned = [c.lstrip("\ufeff").strip() for c in first]
        return cleaned == CSV_HEADERS
    except Exception:
        return False


def _repair_header(csv_path: str) -> None:
    """Προσθέτει header αν λείπει — χωρίς να πειράξει τα δεδομένα."""
    if _has_valid_header(csv_path):
        return
    print("[Repository] Missing header detected — repairing...")
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    # Αφαίρεσε τυχόν παλιό transposed header αν υπάρχει
    if rows and rows[0] and rows[0][0].lstrip("\ufeff").strip().lower() in _GREEK_HEADER_MAP:
        rows = rows[1:]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)
    print("[Repository] Header repaired.")


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
    """Normalize difficulty field to one of Beginner/Intermediate/Advanced.

      Args:
          raw: Raw course dict.

      Returns:
          A normalized difficulty string.
      """

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
    """Normalize language information using explicit fields or title hints.

      Args:
          raw: Raw course dict.
          title: Course title (used as a fallback for detection).

      Returns:
          Normalized language string.
      """


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
    """Normalize a raw course payload into the canonical schema.

        Args:
            course_data: Raw course dictionary from scraping or API sources.

        Returns:
            A dict containing keys matching ``CSV_HEADERS``.
        """
    title = _normalize_text(course_data, ["title", "name", "course_title", "Τίτλος μαθήματος", "Τίτλος"],
                            "Unknown Title")
    provider = _normalize_text(course_data, ["provider", "Πάροχος / Πανεπιστήμιο", "Πάροχος", "institution"],
                               "Unknown Provider")

    return {
        "title": title,
        "provider": provider,
        "category": _normalize_category(course_data, title),
        "difficulty": _normalize_difficulty(course_data),
        "cost": _normalize_cost(course_data),
        "duration": _normalize_text(course_data, ["duration", "length", "Διάρκεια", "time"], "Unknown Duration"),
        "language": _normalize_language(course_data, title),
    }


def _migrate_csv(csv_path: str) -> None:
    """Μετατρέπει transposed CSV σε κανονική μορφή (rows = μαθήματα)."""
    if not os.path.isfile(csv_path):
        return
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        all_rows = list(csv.reader(f))
    if not all_rows:
        return
    first_cell = all_rows[0][0].lstrip("\ufeff").strip() if all_rows[0] else ""
    if not _is_transposed(first_cell):
        return

    print("[Repository] Transposed CSV detected — converting...")
    num_courses = len(all_rows[0]) - 1
    raw: list[dict] = [{} for _ in range(num_courses)]
    for row in all_rows:
        field_label = row[0].lstrip("\ufeff").strip().lower()
        sys_key = _GREEK_HEADER_MAP.get(field_label)
        if not sys_key:
            continue
        for i in range(num_courses):
            val = row[i + 1].strip() if i + 1 < len(row) else ""
            if val and sys_key not in raw[i]:
                raw[i][sys_key] = val

    courses = [
        {k: entry.get(k, "") for k in CSV_HEADERS}
        for entry in raw
        if entry.get("title", "").strip()
    ]
    # Dedup
    seen: set[str] = set()
    unique = []
    for c in courses:
        key = c["title"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()  # ← πάντα γράφει header
        writer.writerows(unique)
    print(f"[Repository] Converted {len(unique)} unique courses.")


class CourseRepository:
    """Create a repository backed by a CSV file path.

           Args:
               csv_path: Path to the CSV file used for storage.
           """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        _migrate_csv(self.csv_path)
        _repair_header(self.csv_path)
        self._ensure_headers_exists()

    def _ensure_headers_exists(self) -> None:
        """Ensure the CSV file exists and has the expected header row."""
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
        """Return the CSV header column names used by the repository."""
        return CSV_HEADERS

    def load_courses(self) -> list[dict]:
        """Load all course records from the CSV file.

               Returns:
                   A list of course dictionaries following the canonical schema.
               """
        courses: list[dict] = []
        if not os.path.isfile(self.csv_path):
            return courses
        try:
            with open(self.csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                if reader.fieldnames:
                    reader.fieldnames = [name.lstrip("\ufeff").strip() for name in reader.fieldnames]

                if reader.fieldnames and reader.fieldnames[0] not in ("title", *_GREEK_HEADER_MAP):
                    # Η 1η γραμμή είναι data, όχι header — επανάνοιγμα με explicit fieldnames
                    f.seek(0)
                    reader = csv.DictReader(f, fieldnames=CSV_HEADERS)

                if reader.fieldnames and _is_transposed(reader.fieldnames[0]):
                    _migrate_csv(self.csv_path)
                    return self.load_courses()

                for row in reader:
                    if not row or not any(row.values()):
                        continue
                    normalized_row: dict[str, str] = {}
                    for raw_key, val in row.items():
                        mapped = _ALL_HEADER_MAP.get(
                            raw_key.strip().lower(), raw_key.strip()
                        )
                        normalized_row[mapped] = str(val).strip() if val is not None else ""
                    course_entry = {key: normalized_row.get(key, "") for key in CSV_HEADERS}

                    # Ensure we don't load entirely blank rows as valid courses
                    if course_entry["title"] and course_entry["title"] != "":
                        courses.append(course_entry)
        except Exception as e:
            print(f"[Repository Error] Failed reading storage CSV matrix: {e}")
            return courses
        return courses

    def save_courses(self, courses: Iterable[dict]) -> None:
        """Overwrite the CSV file with the provided course records.

               Args:
                   courses: Iterable of raw course dicts; they will be normalized
                       before saving.
               """
        normalized = [normalize_course_data(course) for course in courses]
        self._ensure_folder()
        with open(self.csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(normalized)

    def append_courses(self, courses: Iterable[dict]) -> int:
        """Append new courses to the CSV backing file, avoiding duplicates.

               Args:
                   courses: Iterable of raw course dicts.

               Returns:
                   The number of newly appended records.
               """
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
        """Export courses to an arbitrary CSV filepath.

                Args:
                    filepath: Destination CSV path to write.
                    courses: Optional list of course dicts; when omitted the
                        repository's stored courses are exported.
                """
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