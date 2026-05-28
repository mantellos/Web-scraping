import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import re
import os
import csv


# ─── Parsing helpers ────────────────────────────────────────────────────────

def _parse_duration_hours(value: str) -> float:
    """Μετατρέπει διάρκεια σε ώρες (για τα γραφήματα)."""
    if not value:
        return 0
    v = str(value).lower()
    nums = [int(s) for s in re.findall(r"\d+", v)]
    if not nums:
        return 0
    num = nums[0]
    if "month" in v:
        return num * 40
    if "week" in v:
        return num * 10
    if "day" in v:
        return num * 8
    return num


def _parse_cost(value: str) -> float:
    """Μετατρέπει κόστος σε float δολάρια."""
    if not value or not value.strip():
        return 0.0
    v = value.strip().lower()
    if v in ("free", "0", "δωρεάν"):
        return 0.0
    m = re.search(r"[\d,.]+", v)
    if m:
        try:
            return float(m.group().replace(",", "."))
        except ValueError:
            return 0.0
    return 0.0


def load_courses_from_csv(csv_file: str) -> list:
    """Φορτώνει τα μαθήματα από CSV (column-oriented format)."""
    courses = []
    if not os.path.isfile(csv_file):
        return courses
    try:
        with open(csv_file, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        if not rows:
            return courses
        fields = [row[0] for row in rows[1:]]
        titles = rows[0][1:]
        for i, title in enumerate(titles):
            course = {"Τίτλος μαθήματος": title}
            for j, field in enumerate(fields):
                val = rows[j + 1][i + 1] if (j + 1 < len(rows) and i + 1 < len(rows[j + 1])) else ""
                course[field] = val
            courses.append(course)
    except Exception as e:
        print(f"Σφάλμα φόρτωσης CSV: {e}")
    return courses


# ─── Chart functions ─────────────────────────────────────────────────────────

def chart_bar_duration(ax, courses: list):
    """Bar Chart – 5 μαθήματα με τη μεγαλύτερη χρονική διάρκεια."""
    parsed = []
    for c in courses:
        hours = _parse_duration_hours(c.get("Διάρκεια", ""))
        if hours > 0:
            title = c.get("Τίτλος μαθήματος", "Άγνωστο")
            short = title[:24] + "…" if len(title) > 24 else title
            parsed.append((short, hours))

    parsed.sort(key=lambda x: x[1], reverse=True)
    top5 = parsed[:5]

    if not top5:
        ax.text(0.5, 0.5, "Δεν υπάρχουν δεδομένα", ha="center", va="center",
                transform=ax.transAxes, fontsize=13)
        return

    names, hours_vals = zip(*top5)
    colors = ["#4361EE", "#3A86FF", "#4CC9F0", "#7209B7", "#F72585"]
    bars = ax.barh(list(names), list(hours_vals),
                   color=colors[:len(names)], edgecolor="white",
                   linewidth=0.8, height=0.55)

    for bar, val in zip(bars, hours_vals):
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}h", va="center", ha="left",
                fontsize=9, color="#333333")

    ax.set_xlabel("Διάρκεια (ώρες)", fontsize=10, labelpad=8)
    ax.set_title("Top-5 Μαθήματα – Μεγαλύτερη Χρονική Διάρκεια",
                 fontsize=12, fontweight="bold", pad=12)
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


def chart_pie_difficulty(ax, courses: list):
    """Pie Chart – Κατανομή επιπέδου δυσκολίας."""
    difficulty_map = {
        "introductory": "Εισαγωγικό", "beginner": "Εισαγωγικό",
        "intermediate": "Μέτριο", "medium": "Μέτριο", "transitional": "Μέτριο",
        "advanced": "Προχωρημένο",
    }
    counts = Counter()
    for c in courses:
        raw = c.get("Επίπεδο δυσκολίας", "").strip().lower()
        label = difficulty_map.get(raw, "Άλλο")
        counts[label] += 1

    if not counts:
        ax.text(0.5, 0.5, "Δεν υπάρχουν δεδομένα", ha="center", va="center",
                transform=ax.transAxes, fontsize=13)
        return

    labels = list(counts.keys())
    sizes  = list(counts.values())
    palette = {
        "Εισαγωγικό":  "#4CC9F0",
        "Μέτριο":      "#4361EE",
        "Προχωρημένο": "#F72585",
        "Άλλο":        "#AAB4C8",
    }
    colors = [palette.get(l, "#999999") for l in labels]

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct="%1.1f%%", startangle=140,
        wedgeprops={"edgecolor": "white", "linewidth": 1.8},
        pctdistance=0.72
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_color("white")
        at.set_fontweight("bold")

    legend_patches = [
        mpatches.Patch(color=palette.get(l, "#999999"),
                       label=f"{l}  ({counts[l]})")
        for l in labels
    ]
    ax.legend(handles=legend_patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.14), ncol=len(labels),
              fontsize=9, frameon=False)
    ax.set_title("Κατανομή Επιπέδου Δυσκολίας",
                 fontsize=12, fontweight="bold", pad=12)


def chart_line_cost_duration(ax, courses: list):
    """Line Plot – Συσχέτιση Κόστους και Διάρκειας (Top-5 διάρκεια)."""
    parsed = []
    for c in courses:
        hours = _parse_duration_hours(c.get("Διάρκεια", ""))
        cost  = _parse_cost(c.get("Κόστος", ""))
        title = c.get("Τίτλος μαθήματος", "")
        if hours > 0:
            short = title[:18] + "…" if len(title) > 18 else title
            parsed.append((short, hours, cost))

    parsed.sort(key=lambda x: x[1], reverse=True)
    top5 = parsed[:5]

    if not top5:
        ax.text(0.5, 0.5, "Δεν υπάρχουν δεδομένα", ha="center", va="center",
                transform=ax.transAxes, fontsize=13)
        return

    names, hours_vals, costs = zip(*top5)

    # Ταξινόμηση κατά αύξουσα διάρκεια για ομαλή γραμμή
    sorted_data = sorted(zip(hours_vals, costs, names), key=lambda x: x[0])
    h_sorted, c_sorted, n_sorted = zip(*sorted_data)

    ax.plot(list(h_sorted), list(c_sorted),
            color="#4361EE", linewidth=2.5,
            marker="o", markersize=9,
            markerfacecolor="#F72585",
            markeredgecolor="white", markeredgewidth=1.5, zorder=3)

    for h, c, n in zip(h_sorted, c_sorted, n_sorted):
        ax.annotate(n, (h, c),
                    textcoords="offset points", xytext=(7, 6),
                    fontsize=7.5, color="#333333",
                    bbox=dict(boxstyle="round,pad=0.2",
                              fc="white", alpha=0.75, ec="none"))

    ax.fill_between(list(h_sorted), list(c_sorted), alpha=0.08, color="#4361EE")
    ax.set_xlabel("Διάρκεια (ώρες)", fontsize=10, labelpad=8)
    ax.set_ylabel("Κόστος ($)", fontsize=10, labelpad=8)
    ax.set_title("Συσχέτιση Κόστους & Διάρκειας  (Top-5 Διάρκεια)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


# ─── Main popup window ────────────────────────────────────────────────────────

def open_graphs_window(parent, csv_file: str = "courses_data.csv"):
    """Ανοίγει παράθυρο με επιλογή γραφήματος και εμφάνιση σε canvas."""
    courses = load_courses_from_csv(csv_file)
    if not courses:
        messagebox.showinfo("Γραφήματα",
                            "Δεν βρέθηκαν δεδομένα.\nΦορτώστε πρώτα το CSV.")
        return

    win = tk.Toplevel(parent)
    win.title("📊 Ανάλυση & Οπτικοποίηση")
    win.geometry("900x620")
    win.resizable(True, True)
    win.configure(bg="#F0F4FF")

    # Τίτλος
    tk.Label(win,
             text="📊  Ανάλυση & Οπτικοποίηση με Matplotlib",
             font=("Georgia", 14, "bold"),
             bg="#F0F4FF", fg="#1a1a2e").pack(pady=(14, 4))

    # Επιλογή γραφήματος
    ctrl = tk.Frame(win, bg="#F0F4FF")
    ctrl.pack(pady=6)

    tk.Label(ctrl, text="Επιλογή γραφήματος:",
             font=("Arial", 11), bg="#F0F4FF").grid(row=0, column=0, padx=8)

    chart_options = [
        "Bar Chart – Διάρκεια (Top-5)",
        "Pie Chart – Επίπεδο δυσκολίας",
        "Line Plot – Κόστος & Διάρκεια",
    ]
    combo = ttk.Combobox(ctrl, values=chart_options,
                         state="readonly", width=34, font=("Arial", 11))
    combo.set(chart_options[0])
    combo.grid(row=0, column=1, padx=8)

    # Canvas area
    canvas_frame = tk.Frame(win, bg="#F0F4FF")
    canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

    current_canvas = {"widget": None}

    def draw_chart(*_):
        if current_canvas["widget"]:
            current_canvas["widget"].get_tk_widget().destroy()

        fig = Figure(figsize=(8.4, 4.8), dpi=96, facecolor="#F0F4FF")
        ax  = fig.add_subplot(111, facecolor="#FAFBFF")
        fig.subplots_adjust(left=0.16, right=0.96, top=0.88, bottom=0.16)

        sel = combo.get()
        if "Bar" in sel:
            chart_bar_duration(ax, courses)
        elif "Pie" in sel:
            chart_pie_difficulty(ax, courses)
        elif "Line" in sel:
            chart_line_cost_duration(ax, courses)

        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        current_canvas["widget"] = canvas

    combo.bind("<<ComboboxSelected>>", draw_chart)

    # Κουμπί αποθήκευσης
    def save_chart():
        if not current_canvas["widget"]:
            return
        fig  = current_canvas["widget"].figure
        label = combo.get().split("–")[0].strip().replace(" ", "_")
        path  = os.path.join(
            os.path.dirname(os.path.abspath(csv_file)),
            f"chart_{label}.png"
        )
        fig.savefig(path, dpi=150, bbox_inches="tight")
        messagebox.showinfo("Αποθήκευση", f"Αποθηκεύτηκε:\n{path}")

    tk.Button(win, text="💾  Αποθήκευση γραφήματος",
              font=("Arial", 10), bg="#4361EE", fg="white",
              relief="flat", padx=12, pady=4,
              command=save_chart).pack(pady=(0, 12))

    draw_chart()  # αρχικό γράφημα