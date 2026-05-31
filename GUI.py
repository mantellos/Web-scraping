import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

"""Graphical user interface for the Course Browser application.

This module builds a Tkinter-based UI that allows users to load,
filter, scrape, fetch (API) and visualize course data stored as CSV.
"""

from data_processor import CourseRepository
from ranking import rank_courses
from graphs import open_graphs_window
from web_api import fetch_api_data
from Scraping import scrape_all_web_sources

BASE_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(BASE_DIR, "courses_data.csv")
repository = CourseRepository(CSV_FILE)

COLUMNS = repository.get_headers()

COLUMN_LABELS = {
    "title": "Τίτλος Μαθήματος",
    "provider": "Πάροχος",
    "category": "Κατηγορία",
    "difficulty": "Δυσκολία",
    "cost": "Κόστος",
    "duration": "Διάρκεια",
    "language": "Γλώσσα",
}


def refresh_table(courses: list[dict]):
    """Refresh the main Treeview table with provided courses.

    Args:
        courses: A list of normalized course dictionaries.
    """
    tree.delete(*tree.get_children())
    for course in courses:
        tree.insert("", "end", values=tuple(course.get(col, "") for col in COLUMNS))


def load_courses():
    """Load courses from the repository and refresh the UI table.

    Returns:
        The list of loaded course dictionaries.
    """
    courses = repository.load_courses()
    refresh_table(courses)
    return courses


def run_api_pipeline():
    """Run the external API collection pipeline and persist new courses.

    The function fetches courses using ``fetch_api_data``, appends any
    new records to the repository, and updates the table view.
    """
    courses = fetch_api_data()
    if not courses:
        messagebox.showwarning("API", "Δεν βρέθηκαν δεδομένα από το API.")
        return
    added = repository.append_courses(courses)
    load_courses()
    messagebox.showinfo("API", f"Προστέθηκαν {added} νέα μαθήματα από το API.")


def run_scraping_pipeline():
    """Run the web scraping pipeline and store any new courses.

    The function scrapes configured sites and appends new records to the
    repository before refreshing the UI table.
    """
    courses = scrape_all_web_sources()
    if not courses:
        messagebox.showwarning("Scraping", "Δεν βρέθηκαν δεδομένα κατά το scraping.")
        return
    added = repository.append_courses(courses)
    load_courses()
    messagebox.showinfo("Scraping", f"Προστέθηκαν {added} νέα μαθήματα μετά το scraping.")


def export_csv():
    """Export currently stored courses to a user-selected CSV file.

    Opens a save dialog and writes the CSV using the repository export
    helper.
    """
    courses = repository.load_courses()
    if not courses:
        messagebox.showwarning("Εξαγωγή", "Δεν υπάρχουν δεδομένα για εξαγωγή.")
        return
    filepath = filedialog.asksaveasfilename(
        title="Αποθήκευση CSV",
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("All Files", "*")],
    )
    if not filepath:
        return
    repository.export_courses(filepath, courses)
    messagebox.showinfo("Εξαγωγή", f"Το αρχείο αποθηκεύτηκε:\n{filepath}")


def apply_filters(courses, combos, target_tree):
    """Filter a set of courses based on combobox selections and update a tree.

    Args:
        courses: List of course dicts to filter.
        combos: Mapping of logical keys to ttk.Combobox widgets.
        target_tree: The Treeview to update with filtered rows.
    """
    filtered = []
    for course in courses:
        match = True
        for key, combo_widget in combos.items():
            selected_value = combo_widget.get()
            actual_value = course.get(key) or "Άγνωστο"
            if selected_value != "Όλα" and selected_value != actual_value:
                match = False
                break
        if match:
            filtered.append(course)
            
    target_tree.delete(*target_tree.get_children())
    for course in filtered:
        target_tree.insert("", "end", values=tuple(course.get(col, "") for col in COLUMNS))


def open_filter_window():
    """Open a filter window allowing users to filter courses by fields.

    The window presents Comboboxes for various categorical fields and a
    tree view that shows the filtered results.
    """
    courses = repository.load_courses()
    if not courses:
        messagebox.showinfo("Φίλτρα", "Δεν υπάρχουν δεδομένα. Φορτώστε πρώτα το CSV.")
        return

    popup = tk.Toplevel(root)
    popup.title("Φίλτρα Αναζήτησης")
    popup.geometry("1040x560")
    popup.resizable(True, True)

    values = {}
    for key in ["category", "difficulty", "cost", "duration","language"]:
        values[key] = ["Όλα"] + sorted({str(course.get(key) or "Άγνωστο") for course in courses})

    combos = {}
    filterable_keys = [k for k in COLUMNS if k not in ["title", "provider"]]

    control_frame = tk.Frame(popup)
    control_frame.pack(fill="x", padx=14, pady=12)

    for index, key in enumerate(filterable_keys):
        label_text = COLUMN_LABELS.get(key, key.capitalize()) + ":"
        tk.Label(control_frame, text=label_text, font=("Arial", 10)).grid(row=0, column=index * 2, padx=6)
    
        combo = ttk.Combobox(control_frame, values=values[key], state="readonly")
        combo.set("Όλα")
        combo.grid(row=0, column=index * 2 + 1, padx=6)
        combos[key] = combo
    
    filter_frame = tk.Frame(popup)
    filter_frame.pack(fill="both", expand=True, padx=10, pady=10)

    filter_tree = ttk.Treeview(filter_frame, columns=COLUMNS, show="headings")
    vsb = ttk.Scrollbar(filter_frame, orient="vertical", command=filter_tree.yview)
    hsb = ttk.Scrollbar(filter_frame, orient="horizontal", command=filter_tree.xview)
    filter_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    filter_tree.pack(fill="both", expand=True)

    for col in COLUMNS:
        filter_tree.heading(col, text=COLUMN_LABELS[col])
        filter_tree.column(col, width=130, anchor="w")

    apply_button = tk.Button(control_frame, text="Φίλτρο", command=lambda: apply_filters(courses, combos, filter_tree), font=("Arial", 10, "bold"))
    apply_button.grid(row=0, column=8, padx=12, pady=6)
    apply_filters(courses, combos, filter_tree)


# ── Αντικατέστησε την open_ranking_window στο GUI.py με αυτή ──

def open_ranking_window():
    """Open a window displaying the top-N ranked courses.

    The ranking is computed using the ``rank_courses`` function from
    the ``ranking`` module and displayed in a read-only Treeview.
    """
    courses = repository.load_courses()
    if not courses:
        messagebox.showinfo("Κατάταξη", "Δεν υπάρχουν δεδομένα. Φορτώστε πρώτα το CSV.")
        return

    from ranking import get_categories, rank_courses

    popup = tk.Toplevel(root)
    popup.title("Top 3 Μαθήματα")
    popup.geometry("980x600")
    popup.resizable(True, True)

    tk.Label(popup, text="Top 3 Μαθήματα — Φίλτρα Αναζήτησης",
             font=("Arial", 14, "bold")).pack(pady=10)

    # ── Φίλτρα ──
    filter_frame = tk.LabelFrame(popup, text="Φίλτρα", font=("Arial", 10, "bold"),
                                 padx=10, pady=8)
    filter_frame.pack(fill="x", padx=16, pady=6)

    def _unique_sorted(key):
        return ["Όλα"] + sorted({
            str(c.get(key, "")).strip()
            for c in courses
            if str(c.get(key, "")).strip()
        })

    filters = {}

    fields = [
        ("Κατηγορία", "category"),
        ("Γλώσσα", "language"),
        ("Δυσκολία", "difficulty"),
        ("Κόστος", "cost"),
        ("Διάρκεια", "duration"),
    ]

    for col, (label, key) in enumerate(fields):
        tk.Label(filter_frame, text=label + ":", font=("Arial", 10)) \
            .grid(row=0, column=col * 2, padx=(10, 2), sticky="e")
        combo = ttk.Combobox(filter_frame, values=_unique_sorted(key),
                             state="readonly", width=16, font=("Arial", 10))
        combo.set("Όλα")
        combo.grid(row=0, column=col * 2 + 1, padx=(0, 10))
        filters[key] = combo

    tk.Button(filter_frame, text="🔍  Εύρεση Top-3",
              font=("Arial", 10, "bold"), bg="#f1c40f", relief="flat",
              padx=12, pady=4,
              command=lambda: _refresh_ranking()) \
        .grid(row=0, column=len(fields) * 2, padx=16)

    # ── Treeview ──
    columns = ("rank", "title", "provider", "category", "difficulty",
               "cost", "duration", "language", "score")
    tree_frame = tk.Frame(popup)
    tree_frame.pack(fill="both", expand=True, padx=12, pady=8)

    ranking_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=ranking_tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=ranking_tree.xview)
    ranking_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    ranking_tree.pack(fill="both", expand=True)

    headings = {
        "rank": "Θέση", "title": "Τίτλος", "provider": "Πάροχος",
        "category": "Κατηγορία", "difficulty": "Δυσκολία",
        "cost": "Κόστος", "duration": "Διάρκεια",
        "language": "Γλώσσα", "score": "Score",
    }
    widths = {
        "rank": 45, "title": 220, "provider": 120, "category": 110,
        "difficulty": 90, "cost": 75, "duration": 110,
        "language": 75, "score": 65,
    }
    for col in columns:
        ranking_tree.heading(col, text=headings[col])
        ranking_tree.column(col, width=widths[col], anchor="center")

    result_label = tk.Label(popup, text="", font=("Arial", 10, "italic"), fg="#555")
    result_label.pack(pady=(0, 8))

    def _refresh_ranking():
        # Χτίσε το filtered pool με βάση όλα τα φίλτρα
        pool = []
        for course in courses:
            match = True
            for key, combo in filters.items():
                selected = combo.get().strip()
                if selected == "Όλα":
                    continue
                if str(course.get(key, "")).strip() != selected:
                    match = False
                    break
            if match:
                pool.append(course)

        ranking_tree.delete(*ranking_tree.get_children())

        if not pool:
            result_label.config(text="Δεν βρέθηκαν μαθήματα με τα επιλεγμένα φίλτρα.")
            return

        # Ranking μέσα στο filtered pool (χωρίς category filter — ήδη φιλτραρισμένο)
        top_courses = rank_courses(pool, top_n=3)

        for i, course in enumerate(top_courses, start=1):
            ranking_tree.insert("", "end", values=(
                i,
                course.get("title", ""),
                course.get("provider", ""),
                course.get("category", ""),
                course.get("difficulty", ""),
                course.get("cost", ""),
                course.get("duration", ""),
                course.get("language", ""),
                f"{course.get('composite_score', 0):.1f}",
            ))

        active = [
            f"{k}={filters[k].get()}"
            for k in filters
            if filters[k].get() != "Όλα"
        ]
        summary = ", ".join(active) if active else "χωρίς φίλτρα"
        result_label.config(
            text=f"Top-{len(top_courses)} από {len(pool)} μαθήματα  |  Φίλτρα: {summary}"
        )

    _refresh_ranking()

root = tk.Tk()
root.title("Course Browser")
root.geometry("1000x660")

header_frame = tk.Frame(root)
header_frame.pack(fill="x", padx=20, pady=10)

info_text = (
    "Συμμετέχοντες | ΑΜ\n"
    "Μιχαήλ Άγγελος Δεμιρίδης | 1115538\n"
    "Κωνσταντίνος Μαντέλλος   | 1119106\n"
    "Θεοφάνης Τζεφρώνης       | 1115472"
)
left_label = tk.Label(header_frame, text=info_text, justify="left", font=("Consolas", 10))
left_label.pack(side="left")

right_label = tk.Label(header_frame, text="Τμήμα Μηχανικών Η/Υ και Πληροφορικής\nΠανεπιστήμιο Πατρών", justify="right", font=("Arial", 11, "bold"))
right_label.pack(side="right")

button_frame = tk.Frame(root)
button_frame.pack(fill="x", padx=20, pady=10)

btn_api = tk.Button(button_frame, text="Συλλογή μέσω API", command=run_api_pipeline, width=20, bg="#27ae60", fg="white")
btn_api.pack(side="left", padx=6)

btn_scrape = tk.Button(button_frame, text="Συλλογή μέσω Scraping", command=run_scraping_pipeline, width=20, bg="#2980b9", fg="white")
btn_scrape.pack(side="left", padx=6)

btn_load = tk.Button(button_frame, text="Φόρτωση Δεδομένων", command=load_courses, width=18)
btn_load.pack(side="left", padx=6)

btn_filters = tk.Button(button_frame, text="Φίλτρα", command=open_filter_window, width=12)
btn_filters.pack(side="left", padx=6)

btn_ranking = tk.Button(button_frame, text="Top-3", command=open_ranking_window, width=12, bg="#f1c40f")
btn_ranking.pack(side="left", padx=6)

btn_graphs = tk.Button(button_frame, text="Γραφήματα", command=lambda: open_graphs_window(root, csv_file=CSV_FILE), width=12, bg="#8e44ad", fg="white")
btn_graphs.pack(side="left", padx=6)

btn_export = tk.Button(button_frame, text="Εξαγωγή CSV", command=export_csv, width=14, bg="#16a085", fg="white")
btn_export.pack(side="left", padx=6)

frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=20, pady=10)

scroll_y = ttk.Scrollbar(frame, orient="vertical")
scroll_x = ttk.Scrollbar(frame, orient="horizontal")

tree = ttk.Treeview(frame, columns=COLUMNS, show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.config(command=tree.yview)
scroll_x.config(command=tree.xview)
scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
tree.pack(fill="both", expand=True)

for col in COLUMNS:
    tree.heading(col, text=COLUMN_LABELS[col])
    tree.column(col, width=130, anchor="w")

load_courses()
root.mainloop()