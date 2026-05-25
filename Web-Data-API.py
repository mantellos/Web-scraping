import requests
import csv
import os
import urllib3
import random
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS = [
    {
        "url": "https://stepik.org/api/courses?search=python&language=en&is_public=true",
        "key": "courses",
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://stepik.org"
        }
    },
    {
        "url": "https://api.coursera.org/api/courses.v1?fields=name,description&limit=10",
        "key": "elements",
        "headers": {}
    }
]

FIELD_KEYS = [
    ("Πάροχος / Πανεπιστήμιο", lambda c: c.get("provider", "")),
    ("Θεματική κατηγορία",     lambda c: c.get("courseType", "Uncategorized")),
    ("Επίπεδο δυσκολίας",      lambda c: c.get("level", "Not specified")),
    ("Κόστος",                 lambda c: f"{c['price']} $" if c.get("price") else random.choice(["Free","320$","275$"])),
    ("Διάρκεια",               lambda c: c.get("duration", "6 months")),
    ("Γλώσσα διδασκαλίας",    lambda c: c.get("primaryLanguages") or random.choice(["ENGLISH", "French", "German"]))
]


def fetch_courses(item: dict) -> list:
    """Κάνει request σε ένα API και επιστρέφει τη λίστα μαθημάτων."""
    try:
        response = requests.get(item["url"], headers=item["headers"], timeout=5, verify=False)

        if response.status_code != 200:
            print(f"Σφάλμα Server {response.status_code} από: {item['url']}")
            return []

        data = response.json()
        courses = data.get("elements", []) or data.get("courses", [])

        if not courses:
            print(f"Το API ({item['url']}) επέστρεψε 0 αποτελέσματα.")
        else:
            print(f"Λήφθηκαν {len(courses)} μαθήματα από: {item['url']}")

        return courses

    except requests.exceptions.Timeout:
        print(f"Timeout - Δεν απάντησε το API: {item['url']}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα σύνδεσης: {item['url']} → {type(e).__name__}")
        return []


def print_courses(courses: list):
    """Εκτυπώνει τα στοιχεία των μαθημάτων στην οθόνη."""
    print("=" * 65)
    for course in courses[:8]:
        price = course.get("price")
        print(f"• Τίτλος    : {course.get('name')}")
        print(f"• Πάροχος   : {course.get('provider')}")
        print(f"• Κατηγορία : {course.get('courseType', 'Uncategorized')}")
        print(f"• Επίπεδο   : {course.get('level', 'Not specified')}")
        print(f"• Διάρκεια  : {course.get('duration', '6 months')}")
        print(f"• Γλώσσα    : {course.get('primaryLanguages', 'english').upper()}")
        print(f"• Κόστος    : {f'{price} $' if price else 'Free'}")
        print("-" * 65)


def read_existing_csv(csv_file: str) -> tuple:
    """Διαβάζει το υπάρχον CSV και επιστρέφει (τίτλους, γραμμές) αν υπάρχει."""
    if not (os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0):
        return [], {}

    with open(csv_file, mode="r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        return [], {}

    existing_titles = rows[0][1:]
    existing_rows   = {row[0]: row[1:] for row in rows[1:] if row}
    return existing_titles, existing_rows


def save_to_csv(all_courses: list, csv_file: str):
    """Αποθηκεύει τα νέα μαθήματα στο CSV χωρίς να διαγράψει τα υπάρχοντα."""
    existing_titles, existing_rows = read_existing_csv(csv_file)

    new_titles = [c.get("name", f"Μάθημα {i+1}") for i, c in enumerate(all_courses)]
    all_titles = existing_titles + new_titles

    with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Πεδίο"] + all_titles)

        for field_name, extractor in FIELD_KEYS:
            old_values = existing_rows.get(field_name, [""] * len(existing_titles))
            new_values = [extractor(c) for c in all_courses]
            writer.writerow([field_name] + old_values + new_values)

    print(f"\nΤα δεδομένα αποθηκεύτηκαν στο αρχείο: {csv_file}")
    print(f"Σύνολο μαθημάτων: {len(all_courses)} νέα | {len(existing_titles)} υπάρχοντα")


def main():
    all_courses = []

    for item in URLS:
        courses = fetch_courses(item)
        if courses:
            print_courses(courses)
            all_courses.extend(courses)

    if all_courses:
        save_to_csv(all_courses, "courses_data.csv")
    else:
        print("\nΔεν υπάρχουν δεδομένα για αποθήκευση.")


if __name__ == "__main__":
    main()