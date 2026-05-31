"""Graphing helpers for course visualizations.

This module provides functions to render bar, pie and line charts used
by the GUI. It consumes normalized course dictionaries and uses
matplotlib to produce the figures embedded in a Tkinter canvas.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import re
import os
from data_processor import CourseRepository

def _parse_duration_hours(value: str) -> float:
    """Convert a duration string to an approximate number of hours.

    The function recognizes common tokens such as "weeks", "days",
    "months" and numerical values and returns an approximate hour
    equivalent used for sorting and plotting.

    Args:
        value: Human-readable duration string (e.g. "10 weeks", "40 hours").

    Returns:
        Approximate duration in hours as a float. Zero on unrecognized input.
    """
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
    """Parse a cost string and return a float USD value when possible.

    Args:
        value: Cost string (examples: "$40", "Free", "40,00").

    Returns:
        Parsed float value or 0.0 when not parseable or free.
    """
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


FIELD_ALIASES = {
    "title": ["title", "Τίτλος μαθήματος", "Τίτλος Μαθήματος"],
    "provider": ["provider", "Πάροχος"],
    "category": ["category", "Κατηγορία"],
    "difficulty": ["difficulty", "Επίπεδο δυσκολίας", "Δυσκολία"],
    "cost": ["cost", "Κόστος"],
    "duration": ["duration", "Διάρκεια"],
    "language": ["language", "Γλώσσα"],
}


def _get_field_by_system_key(course: dict, key_type: str, default: str = "") -> str:
    """Return the value for a logical field considering aliases.

    Many course dictionaries use different keys for the same concept
    (for example, "duration" vs "time"). This helper searches through
    known aliases and returns the normalized string value.

    Args:
        course: The course dictionary to inspect.
        key_type: Logical key name as used in FIELD_ALIASES.
        default: Fallback returned value when nothing found.

    Returns:
        String value for the requested logical key or the default.
    """
    aliases = FIELD_ALIASES.get(key_type, [key_type])
    for alias in aliases:
        if alias in course:
            return str(course[alias]).strip() if course[alias] is not None else default
        # Έλεγχος για πεζά/κεφαλαία ή κενά
        for actual_key in course.keys():
            if actual_key.strip().lower() == alias.strip().lower():
                return str(course[actual_key]).strip() if course[actual_key] is not None else default
    return default


def chart_bar_duration(ax, courses: list):
    """Render a horizontal bar chart of top-5 longest courses.

    Args:
        ax: Matplotlib Axes object to draw on.
        courses: Iterable of normalized course dicts.
    """
    parsed = []
    for c in courses:
        raw_duration = _get_field_by_system_key(c, "duration", "")
        hours = _parse_duration_hours(raw_duration)
        duration = raw_duration if raw_duration else "Άγνωστο"
        if hours > 0:
            title = _get_field_by_system_key(c, "title", "Μάθημα")
            short = title[:24] + "…" if len(title) > 24 else title
            parsed.append((short, hours))

    parsed.sort(key=lambda x: x[1], reverse=True)
    top5 = parsed[:5]

    if not top5:
        ax.text(0.5, 0.5, "Δεν βρέθηκαν έγκυρα δεδομένα διάρκειας\n(π.χ. 10 weeks, 40 hours)", 
                ha="center", va="center", transform=ax.transAxes, fontsize=11, color="red")
        ax.set_title("Top-5 Μαθήματα – Μεγαλύτερη Χρονική Διάρκεια", fontsize=12, fontweight="bold", pad=12)
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
    """Render a pie chart showing difficulty distribution.

    Args:
        ax: Matplotlib Axes object to draw on.
        courses: Iterable of normalized course dicts.
    """
    difficulty_map = {
        "introductory": "Εισαγωγικό", "beginner": "Εισαγωγικό", "εισαγωγικό": "Εισαγωγικό",
        "intermediate": "Μέτριο", "medium": "Μέτριο", "transitional": "Μέτριο", "μέτριο": "Μέτριο",
        "advanced": "Προχωρημένο", "hard": "Προχωρημένο", "προχωρημένο": "Προχωρημένο",
    }
    counts = Counter()
    for c in courses:
        raw = _get_field_by_system_key(c, "difficulty", "").strip().lower()
        label = difficulty_map.get(raw, "Άλλο")
        counts[label] += 1

    if not counts or sum(counts.values()) == 0:
        ax.text(0.5, 0.5, "Δεν υπάρχουν δεδομένα δυσκολίας", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="red")
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
    """Render a line plot correlating cost with duration (top-5 by duration).

    Args:
        ax: Matplotlib Axes object to draw on.
        courses: Iterable of normalized course dicts.
    """
    parsed = []
    for c in courses:
        raw_duration = _get_field_by_system_key(c, "duration", "")
        hours = _parse_duration_hours(raw_duration)
        cost  = _parse_cost(_get_field_by_system_key(c, "cost", ""))
        if hours > 0:
            title = _get_field_by_system_key(c, "title", "Μάθημα")
            short = title[:18] + "…" if len(title) > 18 else title
            parsed.append((short, hours, cost))

    parsed.sort(key=lambda x: x[1], reverse=True)
    top5 = parsed[:5]

    if not top5:
        ax.text(0.5, 0.5, "Δεν βρέθηκαν επαρκή δεδομένα κόστους/διάρκειας", ha="center", va="center",
                transform=ax.transAxes, fontsize=11, color="red")
        ax.set_title("Συσχέτιση Κόστους & Διάρκειας  (Top-5 Διάρκεια)", fontsize=12, fontweight="bold", pad=12)
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


def open_graphs_window(parent, csv_file: str = "courses_data.csv", courses: list[dict] | None = None):
    """Open a Tkinter window that displays selectable charts.

    The function embeds matplotlib figures into a Tkinter canvas and
    allows saving rendered charts to PNG files.

    Args:
        parent: The parent Tkinter widget.
        csv_file: Path to CSV used by default when loading repository data.
        courses: Optional list of course dicts to visualize; if omitted,
            the function loads courses from the repository using csv_file.
    """
    if courses is None:
        cr = CourseRepository(csv_file)
        courses = cr.load_courses()
    if not courses:
        messagebox.showinfo("Γραφήματα", "Δεν βρέθηκαν δεδομένα.\nΦορτώστε πρώτα το CSV.")
        return

    win = tk.Toplevel(parent)
    win.title("📊 Ανάλυση & Οπτικοποίηση")
    win.geometry("900x620")
    win.resizable(True, True)
    win.configure(bg="#F0F4FF")

    tk.Label(win,
             text="📊  Ανάλυση & Οπτικοποίηση με Matplotlib",
             font=("Georgia", 14, "bold"),
             bg="#F0F4FF", fg="#1a1a2e").pack(pady=(14, 4))

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

    current_canvas: dict[str, FigureCanvasTkAgg | None] = {"widget": None}

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

    draw_chart()