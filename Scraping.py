import requests
from bs4 import BeautifulSoup
import csv
import re
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SITES = [
    {
        "url": "https://pll.harvard.edu/course/using-python-research",
        "classes": ["field__item"],
    },
    {
        "url": "https://pll.harvard.edu/course/cs50-lawyers",
        "classes": ["field__item"],
    },
    {
        "url": "https://online.yale.edu/programs/foundations-animal-ethics",
        "classes": ["field__item", "badge badge-primary"],
    },
    {
        "url": "https://online.yale.edu/programs/foundations-of-bioethics",
        "classes": ["field__item", "badge badge-primary"],
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

FIELD_MAP = {
    ("Subject",):    "Θεματική κατηγορία",
    ("Difficulty",): "Επίπεδο δυσκολίας",
    ("Price",):"Κόστος",
    ("Duration",):   "Διάρκεια",
    ("Course Language", "Language"):"Γλώσσα διδασκαλίας",
}
CLASS_MAP = {
    "field field--name-field-fees-text field--type-string field--label-above":       "Κόστος",  # ή όποιο πεδίο αντιστοιχεί
    "badge badge-primary": "Θεματική κατηγορία",
}

DEFAULT_VALUES = {
    "Θεματική κατηγορία":     "Δεν βρέθηκε",
    "Επίπεδο δυσκολίας":     "Intermediate",
    "Κόστος":                "320$",
    "Διάρκεια":              "6 ",
    "Γλώσσα διδασκαλίας":   "Αγγλικά",
}


def scrape_course(url: str, classes: list) -> dict:
    """Κάνει scrape τη σελίδα του μαθήματος και επιστρέφει dict με τα δεδομένα."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"Timeout - Η σύνδεση ξεπέρασε το όριο χρόνου")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα σύνδεσης: {type(e).__name__}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "Τίτλος μαθήματος":      "",
        "Πάροχος / Πανεπιστήμιο": "",
        "Θεματική κατηγορία":    "",
        "Επίπεδο δυσκολίας":     "",
        "Κόστος":                "",
        "Διάρκεια":              "",
        "Γλώσσα διδασκαλίας":   "",
    }

    # 1. Τίτλος
    title_tag = soup.find("h1")
    if title_tag:
        data["Τίτλος μαθήματος"] = title_tag.get_text(strip=True)

    # 2. Πάροχος
    if "https://pll.harvard.edu" in url:
        data["Πάροχος / Πανεπιστήμιο"] = "Harvard University"
    elif "https://online.yale.edu" in url:
        data["Πάροχος / Πανεπιστήμιο"] = "Yale University"
    else:
        data["Πάροχος / Πανεπιστήμιο"] = "Άγνωστος Πάροχος"

    # 3. Βασικά metadata
    for labels, greek_col in FIELD_MAP.items():
        labels = (labels,) if isinstance(labels, str) else labels  # αν είναι string, το κάνει tuple
        for eng_label in labels:
            tag = soup.find(string=re.compile(eng_label))
            if tag:
                parent = tag.find_parent()
                sibling = parent.find_next_sibling() if parent else None
                if sibling:
                    data[greek_col] = sibling.get_text(strip=True)
                    break

    # 4. Scrape συγκεκριμένων classes για κάθε site
    for css_class in classes:
        items = soup.find_all(class_=css_class.split())
        if items:
            values = [item.get_text(strip=True) for item in items if item.get_text(strip=True)]

            # Ψάχνει αν το css_class υπάρχει μέσα σε κάποιο tuple-κλειδί
            greek_col = None
            for labels, col in CLASS_MAP.items():
                if css_class in labels:
                    greek_col = col
                    break

            if greek_col:
                data[greek_col] = " | ".join(values)

    for field, default in DEFAULT_VALUES.items():
        if not data[field]:
            data[field] = default

    return data


def save_to_csv(all_courses: list, output_file: str):
    """Αποθηκεύει τα δεδομένα σε CSV, όπου κάθε γραμμή είναι ένα πεδίο και κάθε στήλη ένα μάθημα."""
    # Συλλογή όλων των μοναδικών κλειδιών με τη σειρά εμφάνισης
    all_keys = []
    for course in all_courses:
        for k in course:
            if k not in all_keys:
                all_keys.append(k)

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # Header: "Πεδίο" + τίτλος κάθε μαθήματος
        titles = [c.get("Τίτλος μαθήματος", f"Μάθημα {i+1}") for i, c in enumerate(all_courses)]
        writer.writerow(["Πεδίο"] + titles)

        # Γραμμές δεδομένων (εξαιρούμε τον τίτλο γιατί είναι ήδη στο header)
        for key in all_keys:
            if key == "Τίτλος μαθήματος":
                continue
            row = [key] + [course.get(key, "") for course in all_courses]
            writer.writerow(row)


def main():
    all_courses = []

    for site in SITES:
        url = site["url"]
        classes = site["classes"]
        print(f"⏳ Scraping: {url}")
        print(f"   Classes: {classes}")
        try:
            data = scrape_course(url, classes)
            if data is None:
                continue
            all_courses.append(data)
            print(f"   ✅ {data.get('Τίτλος μαθήματος', 'Άγνωστος τίτλος')}")
            for css_class in classes:
                key = f"Class: {css_class}"
                print(f"   {key}: {data.get(key, '-')}")
        except requests.HTTPError as e:
            print(f"   HTTP Error {e.response.status_code}")
        except requests.exceptions.Timeout:
            print(f"   Timeout - Σύνδεση πολύ αργή")
        except requests.exceptions.ConnectionError as e:
            print(f"   Σφάλμα σύνδεσης: {e}")
        except Exception as e:
            print(f"   Σφάλμα: {e}")

    if not all_courses:
        print("\nΔεν βρέθηκαν δεδομένα. Έλεγξε τη σύνδεσή σου και δοκίμασε τοπικά.")
        return

    output_file = "courses_data.csv"
    save_to_csv(all_courses, output_file)
    print(f"\n✅ Αποθηκεύτηκε επιτυχώς στο {output_file}")


if __name__ == "__main__":
    main()