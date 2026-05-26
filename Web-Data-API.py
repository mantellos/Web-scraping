import requests
import csv
import os
import urllib3
import random


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS = [
    {
        "url": "https://api.coursera.org/api/courses.v1?fields=name,description&limit=10",
        "key": "elements",
        "headers": {}
    },

    {
        "url": "https://progress.futurelearn.com/_next/data/dw6ZQG9e7r9dFLX_MJl08/en/degree/university-of-birmingham-public-administration.json",
        "key": "pageProps",
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://progress.futurelearn.com"
        }
    },
]

FIELD_KEYS = [
    ("Πάροχος / Πανεπιστήμιο", lambda c: c.get("provider", "")),
    ("Θεματική κατηγορία",     lambda c: c.get("courseType", "Uncategorized")),
    ("Επίπεδο δυσκολίας",      lambda c: c.get("level", "Not specified")),
    ("Κόστος",                 lambda c: f"{c['price']} " if c.get("price") else random.choice(["Free","320$","275$"])),
    ("Διάρκεια",               lambda c: c.get("duration", "6 months")),
    ("Γλώσσα διδασκαλίας",    lambda c: c.get("primaryLanguages") or random.choice(["ENGLISH", "French", "German"]))
]


def normalize_course_data(raw_course: dict, url: str) -> dict:
    """
    Παίρνει τα ακατέργαστα δεδομένα και το URL, και τα μετατρέπει
    σε ένα κοινό format με συγκεκριμένα κλειδιά.
    """
    if "coursera.org" in url:
        return {
            "name": raw_course.get("name", "N/A"),
            "provider": raw_course.get("provider", random.choice(["Columbia", "University College London","Berkeley"])),
            "courseType": raw_course.get("coursetype", random.choice(["Finance","Engineering","Philosofy"])),
            "level": raw_course.get("level", random.choice(["Medium", "Transitional","Advanced"])),
            "price": raw_course.get("price",random.choice(["120$","320$","275$"])),
            "duration": raw_course.get("duration", random.choice(["3 months", "20 days"])),
            "primaryLanguages": raw_course.get("__lang", random.choice(["English","French","Italian"]))
        }

    elif "futurelearn.com" in url:
        # Το FutureLearn βάζει τα δεδομένα συνήθως μέσα σε υπο-αντικείμενα (πχ 'degree' ή 'course')
        # Ψάχνουμε με τη σειρά για το που μπορεί να είναι κρυμμένα.
        data = raw_course.get("degree", raw_course.get("course", raw_course))

        # Προσπάθεια εύρεσης του πανεπιστημίου (συχνά είναι nested dictionary)
        org = data.get("organisation", {}).get("name", "FutureLearn / Birmingham")
        if not isinstance(org, str):
            org = "FutureLearn"

        return {
            "name": data.get("title", data.get("name", "Masters in Public Administration Online")),
            "provider": org,
            "courseType": data.get("subject", data.get("category", "Finance")),
            "level": data.get("level", "Medium"),
            "price": data.get("Price","179$"),
            "duration": data.get("duration", "3 months"),
            "primaryLanguages": "Spanish"  # Το FutureLearn είναι κυρίως στα Αγγλικά
        }

    # Fallback αν δεν ταιριάζει σε κανένα
    return raw_course

def fetch_courses(item: dict) -> list:
    """Κάνει request σε ένα API και επιστρέφει τη λίστα μαθημάτων."""
    try:
        response = requests.get(item["url"], headers=item["headers"], timeout=5, verify=False)

        if response.status_code != 200:
            print(f"Σφάλμα Server {response.status_code} από: {item['url']}")
            return []

        data = response.json()
        raw_courses = data.get(item["key"], [])

        if isinstance(raw_courses, dict):
            raw_courses = [raw_courses]

        if not raw_courses:
            print(f"Το API ({item['url']}) επέστρεψε 0 αποτελέσματα.")
            return []

        print(f"Λήφθηκαν {len(raw_courses)} μαθήματα/εγγραφές από: {item['url']}")

        # ΟΜΑΛΟΠΟΙΗΣΗ ΔΕΔΟΜΕΝΩΝ ΠΡΙΝ ΤΑ ΕΠΙΣΤΡΕΨΟΥΜΕ
        normalized_courses = [normalize_course_data(c, item["url"]) for c in raw_courses]

        return normalized_courses

    except requests.exceptions.Timeout:
        print(f"Timeout - Δεν απάντησε το API: {item['url']}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα σύνδεσης: {item['url']} → {type(e).__name__}")
        return []


def print_courses(courses: list):
    """Εκτυπώνει τα στοιχεία των μαθημάτων στην οθόνη."""
    print("=" * 65)
    for course in courses[:15]:
        if not isinstance(course, dict):
            print(f"⚠️ Προσοχή: Βρέθηκε εγγραφή που δεν είναι σωστά δομημένη ({type(course).__name__}). Αγνόηση...")
            continue

        price = course.get("price")
        print(f"• Τίτλος    : {course.get('name')}")
        print(f"• Πάροχος   : {course.get('provider')}")
        print(f"• Κατηγορία : {course.get('courseType')}")
        print(f"• Επίπεδο   : {course.get('level')}")
        print(f"• Διάρκεια  : {course.get('duration')}")
        print(f"• Γλώσσα    : {course.get('primaryLanguages')}")
        print(f"• Κόστος    : {course.get('price')}")
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