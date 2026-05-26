import tkinter as tk
from tkinter import ttk
import subprocess
import os
import csv

venv_python = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")

def fetch_api():
    print("Πατήθηκε η Συλλογή μέσω του API!")
    script_path = os.path.join(os.path.dirname(__file__), "Web-Data-API.py")
    subprocess.Popen(["python", script_path])

def fetch_scrape():
    print("Πατήθηκε η Συλλογή μέσω Scraping!")
    script_path = os.path.join(os.path.dirname(__file__), "Scraping.py")
    subprocess.Popen(["python", script_path])

def load_csv_to_table():
    """Διαβάζει το CSV και γεμίζει τον πίνακα."""
    filename = os.path.join(os.path.dirname(__file__), "courses_data.csv")
    try:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return

        headers = [row[0] for row in rows]

        tree["columns"] = headers
        tree["show"] = "headings"

        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=160, anchor="center")

        tree.delete(*tree.get_children())

        num_courses = len(rows[0]) - 1
        for i in range(num_courses):
            row_values = [rows[j][i + 1] for j in range(len(rows))]
            tree.insert("", "end", values=row_values)

    except FileNotFoundError:
        print(f"Δεν βρέθηκε το αρχείο: {filename}")


def load_csv_data():
    """Φορτώνει τα δεδομένα από το CSV και επιστρέφει λίστα με dicts."""
    filename = os.path.join(os.path.dirname(__file__), "courses_data.csv")
    courses = []
    try:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return courses

        # Η 1η στήλη είναι τα ονόματα πεδίων
        fields = [row[0] for row in rows]
        num_courses = len(rows[0]) - 1

        for i in range(num_courses):
            course = {fields[j]: rows[j][i + 1] for j in range(len(fields))}
            courses.append(course)

    except FileNotFoundError:
        print("Δεν βρέθηκε το αρχείο CSV")
    return courses


def normalize_difficulty(value):
    """Κανονικοποίηση δυσκολίας σε Εύκολο / Μέτριο / Δύσκολο."""
    v = value.strip().lower()
    if v in ["Introductory", "beginner"]:
        return "Εύκολο"
    elif v in ["Intermediate", "transitional", "medium"]:  # 👈 προστέθηκαν
        return "Μέτριο"
    elif v in ["advanced"]:
        return "Δύσκολο"
    return "Άγνωστο"

def normalize_cost(value):
    """Κανονικοποίηση κόστους σε Δωρεάν / Επί πληρωμή."""
    v = value.strip().lower()
    if "free" in v or v == "0":
        return "Δωρεάν"
    return "Επί πληρωμή"


def normalize_category(value):
    """Κανονικοποίηση κατηγορίας — παίρνει την 1η αν υπάρχουν πολλές."""
    v = value.strip()
    # Αν έχει πολλές κατηγορίες συνενωμένες, παίρνουμε την πρώτη
    for keyword in ["Computer Science", "Data Processing", "Health & Medicine",
                    "Finance", "Philosofy", "Engineering"]:
        if keyword in v:
            return keyword
    return v if v else "Άγνωστο"


def apply_filters(combo_category, combo_difficulty, combo_cost,all_courses,headers):
    """Φιλτράρει τον πίνακα βάσει των επιλογών στα combobox."""
    sel_category   = combo_category.get()
    sel_difficulty = combo_difficulty.get()
    sel_cost       = combo_cost.get()

    clean_headers = [h for h in headers if h != "Πεδίο"]

    tree.delete(*tree.get_children())
    print(all_courses[0])
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

        print(f"cat={cat} | diff={diff} | cost={cost}")
        # Αν η επιλογή είναι "Όλα" ή ταιριάζει → εμφάνισε
        if (sel_category   in ("Όλα", cat) and
            sel_difficulty in ("Όλα", diff) and
            sel_cost       in ("Όλα", cost)):

            values = [course.get(h, "") for h in headers]
            tree.insert("", "end", values=values)

def open_filter_window():
    """Ανοίγει pop-up παράθυρο με τα φίλτρα."""
    popup = tk.Toplevel(root)
    popup.title("Φίλτρα Αναζήτησης")
    popup.geometry("720x500")
    popup.resizable(False, False)

    all_courses = load_csv_data()
    headers = list(all_courses[0].keys()) if all_courses else []
    if not all_courses:
        tk.Label(popup, text=" Δεν βρέθηκαν δεδομένα!", font=("Arial", 12)).pack(pady=20)
        return
    categories = ["Όλα"] + sorted(set(normalize_category(c.get("Θεματική κατηγορία", "")) for c in all_courses))
    difficulties = ["Όλα"] + sorted(set(normalize_difficulty(c.get("Επίπεδο δυσκολίας", "")) for c in all_courses))
    costs = ["Όλα"] + sorted(set(normalize_cost(c.get("Κόστος", "")) for c in all_courses))

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

    # Κόστος
    tk.Label(filter_frame, text="Κόστος:", font=("Arial", 11)).grid(row=0, column=4, padx=5)
    combo_cost = ttk.Combobox(filter_frame, values=costs, state="readonly", width=18)
    combo_cost.set("Όλα")
    combo_cost.grid(row=0, column=5, padx=5)

    # Κουμπί εφαρμογής φίλτρων
    btn_filter = tk.Button(filter_frame, text="🔍 Φίλτρο", font=("Arial", 11), command=apply_filters(combo_category, combo_difficulty, combo_cost,all_courses, headers))
    btn_filter.grid(row=0, column=6, padx=15)


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

btn_load = tk.Button(root, text="Φόρτωση Δεδομένων", font=("Arial", 11), command=load_csv_to_table)
btn_load.pack(pady=30)

btn_open_filters = tk.Button(root, text="🔍 Φίλτρα", font=("Arial", 12), command=open_filter_window)
btn_open_filters.pack(pady=30)


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