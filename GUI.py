import tkinter as tk
from tkinter import ttk
import subprocess
import os
import csv
import math
import re

venv_python = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")

WEIGHTS = {
    "Κόστος":             0.40,
    "Διάρκεια":           0.30,
    "Επίπεδο δυσκολίας":  0.20,
    "Γλώσσα διδασκαλίας": 0.10,
}


def _parse_cost(value: str):
    if not value or not value.strip():
        return None
    v = value.strip().lower()
    if v in ("free", "0", "δωρεάν"):
        return 0.0
    m = re.search(r"[\d,.]+", v)
    if m:
        return float(m.group().replace(",", "."))
    return None


def _parse_duration_days(value: str):
    if not value or not value.strip():
        return None
    v = value.strip().lower()
    m_months = re.search(r"(\d+)\s*month", v)
    m_weeks  = re.search(r"(\d+)\s*week",  v)
    m_days   = re.search(r"(\d+)\s*day",   v)
    if m_months:
        return float(m_months.group(1)) * 30
    if m_weeks:
        return float(m_weeks.group(1)) * 7
    if m_days:
        return float(m_days.group(1))
    return None

def _parse_difficulty(value: str):
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


def _parse_language(value: str):
    if not value or not value.strip():
        return None
    return 1.0 if "english" in value.strip().lower() else 0.5


def compute_score(course: dict) -> float:
    """
    Υπολογίζει composite score 0-100.
    Ελλιπή πεδία: το βάρος τους αναδιανέμεται δυναμικά στα υπόλοιπα.
    """
    cost_raw = _parse_cost(course.get("Κόστος", ""))
    dur_raw = _parse_duration_days(course.get("Διάρκεια", ""))
    diff_raw = _parse_difficulty(course.get("Επίπεδο δυσκολίας", ""))
    lang_raw = _parse_language(course.get("Γλώσσα διδασκαλίας", ""))

    # Κανονικοποίηση κόστους: e^(-cost/200) → φθηνό = υψηλό score
    cost_norm = math.exp(-cost_raw / 200.0) if cost_raw is not None else None
    # Κανονικοποίηση διάρκειας: soft cap 180 ημέρες
    dur_norm = min(dur_raw / 180.0, 1.0) if dur_raw is not None else None

    raw = {
        "Κόστος": cost_norm,
        "Διάρκεια": dur_norm,
        "Επίπεδο δυσκολίας": diff_raw,
        "Γλώσσα διδασκαλίας": lang_raw,
    }

    available = {k: v for k, v in raw.items() if v is not None}
    if not available:
        return 0.0

    total_weight = sum(WEIGHTS[k] for k in available)
    score = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight
    return round(score * 100, 2)


def rank_courses(courses: list, top_n: int = 3) -> list:
    """Επιστρέφει τα top_n μαθήματα ταξινομημένα κατά φθίνον composite score."""
    scored = []
    for c in courses:
        c = dict(c)
        c["composite_score"] = compute_score(c)
        scored.append(c)
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored[:top_n]


#-----------------------
#-----------------------

def fetch_api():
    print("Πατήθηκε η Συλλογή μέσω του API!")
    script_path = os.path.join(os.path.dirname(__file__), "Web-Data-API.py")
    subprocess.Popen(["python", script_path])

def fetch_scrape():
    print("Πατήθηκε η Συλλογή μέσω Scraping!")
    script_path = os.path.join(os.path.dirname(__file__), "Scraping.py")
    subprocess.Popen(["python", script_path])

def load_csv_to_table(tree):
    filename = os.path.join(os.path.dirname(__file__), "courses_data.csv")
    try:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return

        # Στήλες = 1η γραμμή (τίτλοι μαθημάτων)
        headers = [row[0] for row in rows[1:]]  # πεδία
        titles  = rows[0][1:]                   # τίτλοι μαθημάτων

        # Ορισμός στηλών στον πίνακα
        tree["columns"] = headers
        tree["show"] = "headings"
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=160, anchor="center")

        # Καθαρισμός και εισαγωγή δεδομένων
        tree.delete(*tree.get_children())
        for i in range(len(titles)):
            row_values = [rows[j + 1][i + 1] for j in range(len(headers))]
            tree.insert("", "end", values=row_values)

    except FileNotFoundError:
        print(f"Δεν βρέθηκε το αρχείο: {filename}")
    except Exception as e:
        print(f"Σφάλμα: {e}")


def load_csv_data():
    filename = os.path.join(os.path.dirname(__file__), "courses_data.csv")
    courses = []
    try:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return courses

        fields = [row[0] for row in rows[1:]]
        titles = rows[0][1:]

        for i, title in enumerate(titles):
            course = {"Τίτλος μαθήματος": title}
            for j, field in enumerate(fields):
                course[field] = rows[j + 1][i + 1]
            courses.append(course)

    except FileNotFoundError:
        print("Δεν βρέθηκε το αρχείο CSV")
    except Exception as e:
        print(f"Σφάλμα: {e}")

    return courses  # 👈 εξω από το try/except


def normalize_difficulty(value):
    """Κανονικοποίηση δυσκολίας σε Εύκολο / Μέτριο / Δύσκολο."""
    v = value.strip().lower()
    if v in ["introductory", "beginner"]:
        print(f">>> Εύκολο για '{v}'")
        return "Εύκολο"
    elif v in ["intermediate", "transitional", "medium"]:  # 👈 προστέθηκαν
        print(f">>> Μέτριο για '{v}'")
        return "Μέτριο"
    elif v in ["advanced"]:
        return "Δύσκολο"
    print(f">>> Επιστρέφω Άγνωστο για '{v}'")
    return "Άγνωστο"

def get_max_cost(all_courses):
    """Βρίσκει το μέγιστο κόστος από τα δεδομένα."""
    max_cost = 0
    for c in all_courses:
        value = c.get("Κόστος", "").strip().replace("$", "").replace(" ", "")
        try:
            cost = float(value)
            if cost > max_cost:
                max_cost = cost
        except ValueError:
            continue
    return max_cost

def normalize_cost(value,max_cost):
    """Κανονικοποίηση κόστους σε Δωρεάν / Επί πληρωμή."""
    v = value.strip().lower()
    if "free" in v or v == "0":
        return "Δωρεάν"
    try:
        cost = float(value.strip().replace("$", "").replace(" ", ""))
        if cost == max_cost:
            return f"{int(max_cost)}$"
        return "Επί πληρωμή"
    except ValueError:
        return "Επί πληρωμή"


def normalize_category(value):
    """Κανονικοποίηση κατηγορίας — παίρνει την 1η αν υπάρχουν πολλές."""
    v = value.strip().lower()
    if "computer science" in v:
        return "Computer Science"
    elif "data processing" in v or "data science" in v:
        return "Data Processing"
    elif "health" in v:
        return "Health & Medicine"
    elif "finance" in v:
        return "Finance"
    elif "philosof" in v:  # 👈 philosofy ή philosophy
        return "Philosophy"
    elif "engineering" in v:
        return "Engineering"
    return value.strip() if value.strip() else "Άγνωστο"


def apply_filters(combo_category, combo_difficulty, combo_cost, combo_language, all_courses, headers):
    """Φιλτράρει τον πίνακα βάσει των επιλογών στα combobox."""
    sel_category   = combo_category.get()
    sel_difficulty = combo_difficulty.get()
    sel_cost       = combo_cost.get()
    sel_language = combo_language.get()
    print(f"Επιλογές: cat={sel_category} | diff={sel_difficulty} | cost={sel_cost}")
    clean_headers = [h for h in headers if h != "Πεδίο"]

    tree.delete(*tree.get_children())
    #print(all_courses[0])
    # Φτιάξε τις στήλες αν δεν υπάρχουν
    if not tree["columns"]:
        tree["columns"] = headers
        tree["show"] = "headings"
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=160, anchor="center")

    for course in all_courses:
        cat  = normalize_category(course.get("Θεματική κατηγορία", ""))
        diff = normalize_difficulty(course.get("Επίπεδο δυσκολίας", ""))
        cost = normalize_cost(course.get("Κόστος", ""))
        lang = course.get("Γλώσσα διδασκαλίας", "")

        #print(f"cat={cat} | diff={diff} | cost={cost}")
        # Αν η επιλογή είναι "Όλα" ή ταιριάζει → εμφάνισε
        if (sel_category   in ("Όλα", cat) and
            sel_difficulty in ("Όλα", diff) and
            sel_cost       in ("Όλα", cost) and
            sel_language in ("Όλα", lang)):

            values = [course.get(h, "") for h in headers]
            tree.insert("", "end", values=values)

def open_filter_window():
    """Ανοίγει pop-up παράθυρο με τα φίλτρα."""
    popup = tk.Toplevel(root)
    popup.title("Φίλτρα Αναζήτησης")
    popup.geometry("1000x500")
    popup.resizable(False, False)

    all_courses = load_csv_data()
    for c in all_courses:
        print(c.get("Επίπεδο δυσκολίας", ""))
    headers = list(all_courses[0].keys()) if all_courses else []
    if not all_courses:
        tk.Label(popup, text=" Δεν βρέθηκαν δεδομένα!", font=("Arial", 12)).pack(pady=20)
        return
    categories = ["Όλα"] + sorted(set(normalize_category(c.get("Θεματική κατηγορία", "")) for c in all_courses))
    difficulties = ["Όλα"] + sorted(set(normalize_difficulty(c.get("Επίπεδο δυσκολίας", "")) for c in all_courses))
    max_cost = get_max_cost(all_courses)
    costs = ["Όλα"] + sorted(set(normalize_cost(c.get("Κόστος", ""), max_cost) for c in all_courses))
    languages = ["Όλα"] + sorted(set(c.get("Γλώσσα διδασκαλίας", "") for c in all_courses))

    filter_frame = tk.Frame(popup)
    filter_frame.pack(pady=20,padx=10)

    # Κατηγορία
    tk.Label(filter_frame, text="Κατηγορία:", font=("Arial", 11)).grid(row=0, column=0, padx=5)
    combo_category = ttk.Combobox(filter_frame, values=categories, state="readonly", width=18)
    combo_category.set("Όλα")
    combo_category.grid(row=0, column=1, padx=5)

    # Δυσκολία
    tk.Label(filter_frame, text="Δυσκολία:", font=("Arial", 11)).grid(row=0, column=2, padx=5)
    combo_difficulty = ttk.Combobox(filter_frame, values=difficulties, state="readonly", width=18)
    combo_difficulty.set("Όλα")
    combo_difficulty.grid(row=0, column=3, padx=5)

    # Γλώσσα
    tk.Label(filter_frame, text="Γλώσσα:", font=("Arial", 11)).grid(row=0, column=6, padx=5)
    combo_language = ttk.Combobox(filter_frame, values=languages, state="readonly", width=18)
    combo_language.set("Όλα")
    combo_language.grid(row=0, column=7, padx=5)

    # Κόστος
    tk.Label(filter_frame, text="Κόστος:", font=("Arial", 11)).grid(row=0, column=4, padx=5)
    combo_cost = ttk.Combobox(filter_frame, values=costs, state="readonly", width=18)
    combo_cost.set("Όλα")
    combo_cost.grid(row=0, column=5, padx=5)

    # Κουμπί εφαρμογής φίλτρων
    btn_filter = tk.Button(filter_frame, text="🔍 Φίλτρο", font=("Arial", 11),
                           command=lambda: apply_filters(combo_category, combo_difficulty, combo_cost,combo_language, all_courses,
                                                         headers))
    btn_filter.grid(row=0, column=8, padx=15)


def open_ranking_window():
    """
    Ανοίγει παράθυρο που εμφανίζει τα 3 κορυφαία μαθήματα
    βάσει composite score (Κόστος 40% | Διάρκεια 30% | Επίπεδο 20% | Γλώσσα 10%).
    Χειρίζεται ελλιπή δεδομένα δυναμικά.
    """
    all_courses = load_csv_data()
    if not all_courses:
        tk.messagebox.showinfo("Κατάταξη", "Δεν υπάρχουν δεδομένα. Φορτώστε πρώτα το CSV.")
        return

    top3 = rank_courses(all_courses, top_n=3)

    popup = tk.Toplevel(root)
    popup.title("Top-3 Μαθήματα – Composite Score")
    popup.geometry("860x520")
    popup.resizable(True, True)

    # ── Τίτλος ────────────────────────────────────────────────────────────────
    tk.Label(popup,
             text="🏆  Κατάταξη Κορυφαίων Μαθημάτων",
             font=("Arial", 15, "bold")).pack(pady=(14, 2))

    # ── Επεξήγηση βαρών ───────────────────────────────────────────────────────
    info = (
        "Composite Score  =  Κόστος × 40%  +  Διάρκεια × 30%  +  "
        "Επίπεδο × 20%  +  Γλώσσα × 10%\n"
        "Ελλιπή πεδία αντιμετωπίζονται δυναμικά (αναδιανομή βαρών)."
    )
    tk.Label(popup, text=info, font=("Consolas", 9), fg="gray40",
             justify="center").pack(pady=(0, 10))

    # ── Πίνακας αποτελεσμάτων ─────────────────────────────────────────────────
    cols = ("Θέση", "Τίτλος μαθήματος", "Κόστος", "Διάρκεια",
            "Επίπεδο", "Γλώσσα", "Score")
    widths = (50, 240, 90, 90, 110, 90, 70)

    frame = tk.Frame(popup)
    frame.pack(fill="both", expand=True, padx=18, pady=6)

    sv = tk.Scrollbar(frame, orient="vertical")
    sh = tk.Scrollbar(frame, orient="horizontal")
    tv = ttk.Treeview(frame, columns=cols, show="headings",
                      yscrollcommand=sv.set, xscrollcommand=sh.set)
    sv.config(command=tv.yview)
    sh.config(command=tv.xview)
    sv.pack(side="right", fill="y")
    sh.pack(side="bottom", fill="x")
    tv.pack(fill="both", expand=True)

    for col, w in zip(cols, widths):
        tv.heading(col, text=col)
        tv.column(col, width=w, anchor="center")

    medals = ["🥇", "🥈", "🥉"]
    for rank, course in enumerate(top3, start=1):
        tv.insert("", "end", values=(
            f"{medals[rank - 1]} {rank}",
            course.get("Τίτλος μαθήματος", "—"),
            course.get("Κόστος", "—"),
            course.get("Διάρκεια", "—"),
            course.get("Επίπεδο δυσκολίας", "—"),
            course.get("Γλώσσα διδασκαλίας", "—"),
            f"{course['composite_score']:.1f} / 100",
        ))

    # ── Ανάλυση score ανά μάθημα ──────────────────────────────────────────────
    tk.Label(popup, text="Ανάλυση Composite Score",
             font=("Arial", 11, "bold")).pack(pady=(8, 2))

    detail_frame = tk.Frame(popup)
    detail_frame.pack(fill="x", padx=18, pady=(0, 14))

    for rank, course in enumerate(top3, start=1):
        # Αναλυτική βαθμολογία ανά πεδίο
        cost_raw = _parse_cost(course.get("Κόστος", ""))
        dur_raw = _parse_duration_days(course.get("Διάρκεια", ""))
        diff_raw = _parse_difficulty(course.get("Επίπεδο δυσκολίας", ""))
        lang_raw = _parse_language(course.get("Γλώσσα διδασκαλίας", ""))

        cost_n = f"{math.exp(-cost_raw / 200) * 100:.0f}" if cost_raw is not None else "N/A"
        dur_n = f"{min(dur_raw / 180, 1) * 100:.0f}" if dur_raw is not None else "N/A"
        diff_n = f"{diff_raw * 100:.0f}" if diff_raw is not None else "N/A"
        lang_n = f"{lang_raw * 100:.0f}" if lang_raw is not None else "N/A"

        title_short = course.get("Τίτλος μαθήματος", "")[:38]
        text = (
            f"{medals[rank - 1]} {title_short}  →  "
            f"Κόστος: {cost_n}  |  Διάρκεια: {dur_n}  |  "
            f"Επίπεδο: {diff_n}  |  Γλώσσα: {lang_n}   "
            f"[Score: {course['composite_score']:.1f}]"
        )
        tk.Label(detail_frame, text=text, font=("Consolas", 9),
                 anchor="w", justify="left").pack(fill="x", pady=1)



# 1. Δημιουργία κύριου παραθύρου
root = tk.Tk()
root.title("Information")
root.geometry("1000x650")  # πλάτος x ύψος σε pixels
# 2. Widgets (στοιχεία διεπαφής)

label = tk.Label(root, text="University Courses: ", font=("Arial", 20))
label.pack(pady=10)

# 2. Φτιάχνουμε το "αόρατο κουτί" (Frame) για να μπουν τα στοιχεία δίπλα-δίπλα

content_frame = tk.Frame(root)
content_frame.pack(anchor="w", padx=20)

lista_mathiton = """Συμμετέχοντες | Αριθμός Μητρώου |
--------------|-------------------|
Μιχαήλ Άγγελος Δημηρίδης | 1115538|
Κωνσταντίνος Μαντέλλος   | 1119106|
Θεοφάνης Τζεφρώνης       | 1115472|"""

left_label = tk.Label(content_frame, text=lista_mathiton, justify="left", font=("Consolas", 10))
# Το κολλάμε στα ΑΡΙΣΤΕΡΑ του αόρατου κουτιού
left_label.pack(side=tk.LEFT)

right_label = tk.Label(content_frame, text="Τμήμα Μηχανικών Η/Υ και Πληροφορικής\n Πανεπιστήμιο Πατρών", justify="left", fg="black",font=("Arial", 12, "bold"))
# Το padx=50 του δίνει μια απόσταση 50 pixels από τη λίστα για να μην κολλάνε
right_label.pack(side=tk.LEFT, padx=50)

# 4. Δημιουργία νέου Frame ΜΟΝΟ για τα κουμπιά
button_frame = tk.Frame(root)
# Το expand=True λέει στο Frame να απλωθεί και να πιάσει όλο τον διαθέσιμο κενό χώρο, κεντράροντας τα περιεχόμενά του!
button_frame.pack(pady=50)

# Δημιουργία των κουμπιών (τα βάζουμε μέσα στο button_frame)
# Πρόσθεσα λίγο πλάτος (width) και γραμματοσειρά (font) για να φαίνονται πιο ωραία, μπορείς να τα αλλάξεις.
btn_api = tk.Button(button_frame, text="Συλλογή μέσω API", width=20, font=("Arial", 12), command=fetch_api)
btn_api.pack(side=tk.LEFT, padx=40) # Το padx=20 βάζει κενό ΑΝΑΜΕΣΑ στα κουμπιά

btn_scrape = tk.Button(button_frame, text="Συλλογή μέσω Scraping", width=20, font=("Arial", 12), command=fetch_scrape)
btn_scrape.pack(side=tk.LEFT, padx=40)

action_frame = tk.Frame(root)
action_frame.pack(pady=10)

btn_load = tk.Button(root, text="Φόρτωση Δεδομένων", font=("Arial", 11),
                     command=lambda: load_csv_to_table(tree))
btn_load.pack(pady=30)

btn_open_filters = tk.Button(root, text="🔍 Φίλτρα", font=("Arial", 12), command=open_filter_window)
btn_open_filters.pack(pady=30)


btn_ranking = tk.Button(action_frame, text="🏆 Top-3 Κατάταξη",
                        font=("Arial", 12), bg="#FFD700", fg="black",
                        command=open_ranking_window)
btn_ranking.pack(side=tk.LEFT, padx=15)

#-Pinakas
table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=10, pady=10)

scroll_x = tk.Scrollbar(table_frame, orient="horizontal")
scroll_y = tk.Scrollbar(table_frame, orient="vertical")

tree = ttk.Treeview(table_frame, xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

scroll_x.config(command=tree.xview)
scroll_y.config(command=tree.yview)

scroll_x.pack(side="bottom", fill="x")
scroll_y.pack(side="right", fill="y")
tree.pack(fill="both", expand=True)


# Έναρξη του event loop
root.mainloop()