import re

# ── Βάρη αξιολόγησης ──────────────────────────────────────────────────────────
WEIGHTS = {
    "Κόστος": 0.40,
    "Διάρκεια": 0.30,
    "Επίπεδο δυσκολίας": 0.20,
    "Γλώσσα διδασκαλίας": 0.10,
}


# ── Βοηθητικές συναρτήσεις κανονικοποίησης ────────────────────────────────────

def _parse_cost(value: str) -> float | None:
    """
    Μετατρέπει τιμή κόστους σε αριθμό δολαρίων.
    'Free' / '0' → 0.0  |  '275$' → 275.0  |  '' / None → None (ελλιπές)
    """
    if not value or not value.strip():
        return None
    v = value.strip().lower()
    if v in ("free", "0", "δωρεάν"):
        return 0.0
    m = re.search(r"[\d,.]+", v)
    if m:
        return float(m.group().replace(",", "."))
    return None


def _parse_duration_days(value: str) -> float | None:
    """
    Μετατρέπει διάρκεια σε μέρες.
    '6 Weeks' → 42  |  '3 months' → 90  |  '20 days' → 20  |  '' → None
    """
    if not value or not value.strip():
        return None
    v = value.strip().lower()
    m_weeks = re.search(r"(\d+)\s*week", v)
    m_months = re.search(r"(\d+)\s*month", v)
    m_days = re.search(r"(\d+)\s*day", v)
    if m_months:
        return float(m_months.group(1)) * 30
    if m_weeks:
        return float(m_weeks.group(1)) * 7
    if m_days:
        return float(m_days.group(1))
    return None


def _parse_difficulty(value: str) -> float | None:
    """
    Αντιστοιχίζει επίπεδο δυσκολίας σε τιμή 0–1.
    Introductory/Beginner → 0.25 | Medium/Intermediate/Transitional → 0.5 | Advanced → 1.0
    """
    if not value or not value.strip():
        return None
    v = value.strip().lower()
    if v in ("introductory", "beginner", "εύκολο"):
        return 0.25
    if v in ("intermediate", "medium", "transitional", "μέτριο"):
        return 0.50
    if v in ("advanced", "δύσκολο"):
        return 1.00
    return None


def _parse_language(value: str) -> float | None:
    """
    Αγγλική γλώσσα → 1.0 (ευρεία χρησιμότητα)
    Άλλες γλώσσες  → 0.5
    Κενό           → None
    """
    if not value or not value.strip():
        return None
    return 1.0 if "english" in value.strip().lower() else 0.5


# ── Κύρια συνάρτηση βαθμολόγησης ──────────────────────────────────────────────

def compute_score(course: dict) -> float:
    """
    Υπολογίζει το composite score ενός μαθήματος (0–100).

    Χειρισμός ελλιπών δεδομένων (dynamic adjustment):
      Αν κάποιο πεδίο λείπει, το βάρος του ΔΕΝ χάνεται·
      αναδιανέμεται αναλογικά στα υπόλοιπα διαθέσιμα πεδία.
    """
    raw = {
        "Κόστος": _parse_cost(course.get("Κόστος", "")),
        "Διάρκεια": _parse_duration_days(course.get("Διάρκεια", "")),
        "Επίπεδο δυσκολίας": _parse_difficulty(course.get("Επίπεδο δυσκολίας", "")),
        "Γλώσσα διδασκαλίας": _parse_language(course.get("Γλώσσα διδασκαλίας", "")),
    }

    # Κανονικοποίηση Κόστους: το χαμηλότερο κόστος = υψηλότερο score
    # Χρησιμοποιούμε εκθετική απόσβεση: score = e^(-cost/200)
    import math
    if raw["Κόστος"] is not None:
        raw["Κόστος"] = math.exp(-raw["Κόστος"] / 200.0)

    # Κανονικοποίηση Διάρκειας: δεν υπάρχει συγκεκριμένο max · χρησιμοποιούμε
    # soft cap στις 180 μέρες (6 μήνες) → score = min(days/180, 1.0)
    if raw["Διάρκεια"] is not None:
        raw["Διάρκεια"] = min(raw["Διάρκεια"] / 180.0, 1.0)

    # Τα "Επίπεδο" και "Γλώσσα" είναι ήδη στο [0,1]

    # Αθροίζουμε μόνο τα διαθέσιμα πεδία (δυναμική αναδιανομή βαρών)
    available = {k: v for k, v in raw.items() if v is not None}
    if not available:
        return 0.0

    total_weight = sum(WEIGHTS[k] for k in available)
    score = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight

    return round(score * 100, 2)  # 0–100


# ── Κατάταξη λίστας μαθημάτων ─────────────────────────────────────────────────

def rank_courses(courses: list, top_n: int = 3) -> list[dict]:
    """
    Δέχεται λίστα από dict-μαθήματα και επιστρέφει τα top_n
    ταξινομημένα κατά φθίνον composite score.

    Κάθε dict εμπλουτίζεται με κλειδί 'composite_score'.
    """
    scored = []
    for c in courses:
        c = dict(c)  # αντίγραφο – δεν τροποποιούμε τα αρχικά
        c["composite_score"] = compute_score(c)
        scored.append(c)

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored[:top_n]
