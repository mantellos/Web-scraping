import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from data_processor import CourseRepository
from ranking import rank_courses
from graphs import open_graphs_window
from web_api import fetch_api_data
from Scraping import scrape_all_web_sources

BASE_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(BASE_DIR, "courses_data.csv")
repository = CourseRepository(CSV_FILE)

COLUMNS = [
    "title",
    "provider",
    "category",
    "difficulty",
    "cost",
    "duration",
    "language",
]

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
    tree.delete(*tree.get_children())
    for course in courses:
        tree.insert("", "end", values=tuple(course.get(col, "") for col in COLUMNS))


def load_courses():
    courses = repository.load_courses()
    refresh_table(courses)
    return courses


def run_api_pipeline():
    courses = fetch_api_data()
    if not courses:
        messagebox.showwarning("API", "Δεν βρέθηκαν δεδομένα από το API.")
        return
    added = repository.append_courses(courses)
    load_courses()
    messagebox.showinfo("API", f"Προστέθηκαν {added} νέα μαθήματα από το API.")


def run_scraping_pipeline():
    courses = scrape_all_web_sources()
    if not courses:
        messagebox.showwarning("Scraping", "Δεν βρέθηκαν δεδομένα κατά το scraping.")
        return
    added = repository.append_courses(courses)
    load_courses()
    messagebox.showinfo("Scraping", f"Προστέθηκαν {added} νέα μαθήματα μετά το scraping.")


def export_csv():
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


def open_filter_window():
    courses = repository.load_courses()
    if not courses:
        messagebox.showinfo("Φίλτρα", "Δεν υπάρχουν δεδομένα. Φορτώστε πρώτα το CSV.")
        return

    popup = tk.Toplevel(root)
    popup.title("Φίλτρα Αναζήτησης")
    popup.geometry("1040x560")
    popup.resizable(True, True)

    values = {
        "category": ["Όλα"] + sorted({course.get("category", "Unknown") for course in courses}),
        "difficulty": ["Όλα"] + sorted({course.get("difficulty", "Unknown") for course in courses}),
        "cost": ["Όλα"] + sorted({course.get("cost", "Άγνωστο") for course in courses}),
        "language": ["Όλα"] + sorted({course.get("language", "Unknown") for course in courses}),
    }

    control_frame = tk.Frame(popup)
    control_frame.pack(fill="x", padx=14, pady=12)

    labels = ["Κατηγορία", "Δυσκολία", "Κόστος", "Γλώσσα"]
    keys = ["category", "difficulty", "cost", "language"]
    combos = {}

    for index, key in enumerate(keys):
        tk.Label(control_frame, text=labels[index] + ":", font=("Arial", 10)).grid(row=0, column=index * 2, padx=6, pady=6, sticky="e")
        combo = ttk.Combobox(control_frame, values=values[key], state="readonly", width=24)
        combo.set(values[key][0])
        combo.grid(row=0, column=index * 2 + 1, padx=6, pady=6)
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

    def apply_filters():
        selected = {key: combos[key].get() for key in keys}
        filtered = []
        for course in courses:
            if (selected["category"] in ("Όλα", course.get("category", ""))
                    and selected["difficulty"] in ("Όλα", course.get("difficulty", ""))
                    and selected["cost"] in ("Όλα", course.get("cost", ""))
                    and selected["language"] in ("Όλα", course.get("language", ""))):
                filtered.append(course)
        filter_tree.delete(*filter_tree.get_children())
        for course in filtered:
            filter_tree.insert("", "end", values=tuple(course.get(col, "") for col in COLUMNS))

    apply_button = tk.Button(control_frame, text="Φίλτρο", command=apply_filters, font=("Arial", 10, "bold"))
    apply_button.grid(row=0, column=8, padx=12, pady=6)
    apply_filters()


def open_ranking_window():
    courses = repository.load_courses()
    if not courses:
        messagebox.showinfo("Κατάταξη", "Δεν υπάρχουν δεδομένα. Φορτώστε πρώτα το CSV.")
        return

    top_courses = rank_courses(courses, top_n=3)
    popup = tk.Toplevel(root)
    popup.title("Top 3 Μαθήματα")
    popup.geometry("860x520")
    popup.resizable(True, True)

    heading = tk.Label(popup, text="Top 3 Μαθήματα", font=("Arial", 14, "bold"))
    heading.pack(pady=12)

    columns = ("rank", "title", "provider", "category", "difficulty", "cost", "duration", "language", "score")
    tree_frame = tk.Frame(popup)
    tree_frame.pack(fill="both", expand=True, padx=12, pady=8)
    ranking_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    ranking_tree.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=ranking_tree.yview)
    scrollbar.pack(side="right", fill="y")
    ranking_tree.configure(yscrollcommand=scrollbar.set)

    headings = {
        "rank": "Θέση",
        "title": "Τίτλος",
        "provider": "Πάροχος",
        "category": "Κατηγορία",
        "difficulty": "Δυσκολία",
        "cost": "Κόστος",
        "duration": "Διάρκεια",
        "language": "Γλώσσα",
        "score": "Score",
    }
    widths = {key: 100 for key in columns}
    widths["title"] = 220
    widths["provider"] = 120
    widths["score"] = 80

    for col in columns:
        ranking_tree.heading(col, text=headings[col])
        ranking_tree.column(col, width=widths[col], anchor="center")
    for index, course in enumerate(top_courses, start=1):
        ranking_tree.insert("", "end", values=(
            index,
            course.get("title", ""),
            course.get("provider", ""),
            course.get("category", ""),
            course.get("difficulty", ""),
            course.get("cost", ""),
            course.get("duration", ""),
            course.get("language", ""),
            f"{course.get('composite_score', 0):.1f}",
        ))


root = tk.Tk()
root.title("Course Browser")
root.geometry("1000x660")

header_frame = tk.Frame(root)
header_frame.pack(fill="x", padx=20, pady=10)

info_text = (
    "Συμμετέχοντες | ΑΜ\n"
    "Μιχαήλ Άγγελος Δημηρίδης | 1115538\n"
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

btn_graphs = tk.Button(button_frame, text="Γραφήματα", command=lambda: open_graphs_window(root, CSV_FILE), width=12, bg="#8e44ad", fg="white")
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
