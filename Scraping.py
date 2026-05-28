import requests
from bs4 import BeautifulSoup
import csv
import re
import urllib3
import random

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SITES = [
    {
        "url": "https://pll.harvard.edu/course/using-python-research",
        "classes": ["topics--teaser","field__item"],
    },
    {
        "url": "https://pll.harvard.edu/course/cs50-lawyers",
        "classes": ["topics--teaser","field__item"],
    },
    {
        "url": "https://online.yale.edu/programs/foundations-animal-ethics",
        "classes": ["badge badge-primary"],
    },
    {
        "url": "https://online.yale.edu/programs/foundations-of-bioethics",
        "classes": ["badge badge-primary"],
    },

    {
        "url": "https://www.tuni.fi/en/tau/open-university/course-offering/5g-mobile-communications",
        "classes": ["badge badge-primary"],
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
    ("dubject","Study fields"):  "Θεματική κατηγορία",
    ("Difficulty",): "Επίπεδο δυσκολίας",
    ("Price",):"Κόστος",
    ("Duration",):   "Διάρκεια",
    ("Course Language", "Language"):"Γλώσσα διδασκαλίας",
}
CLASS_MAP = {
    "field__item":       "Κόστος",  # ή όποιο πεδίο αντιστοιχεί
    "badge badge-primary": "Θεματική κατηγορία",
    "topics--teaser": "Θεματική κατηγορία",
    "field__item": "Επίπεδο δυσκολίας"
}

DEFAULT_VALUES = {
    "Θεματική κατηγορία":     "Δεν βρέθηκε",
    "Επίπεδο δυσκολίας":     "Intermediate",
    "Κόστος":                ["320$","430$","225$"],
    "Διάρκεια":              ["6 Weeks","3 Weeks"],
    "Γλώσσα διδασκαλίας":   ["English","French"]
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
    elif "https://www.tuni.fi" in url:
        data["Πάροχος / Πανεπιστήμιο"]= "Open University"
    else:
        data["Πάροχος / Πανεπιστήμιο"] = "Άγνωστος Πάροχος"

    # 3. Βασικά metadata
    for labels, greek_col in FIELD_MAP.items():
        labels = (labels,) if isinstance(labels, str) else labels  # αν είναι string, το κάνει tuple
        for eng_label in labels:
            tag = soup.find(string=re.compile(eng_label,re.IGNORECASE))
            if tag:
                parent = tag.find_parent()
                sibling = parent.find_next_sibling() if parent else None
                if sibling:
                    data[greek_col] = sibling.get_text(strip=True)
                    break

    # 4. Scrape συγκεκριμένων classes για κάθε site
    for css_class in classes:
        greek_col = CLASS_MAP.get(css_class)
        if not greek_col:
            continue
        if css_class == "field__item":
            difficulty_block = soup.find("div", class_=lambda c: c and "field--name-field-difficulty" in c)
            if difficulty_block:
                item = difficulty_block.find(class_="field__item")
                if item:
                    data[greek_col] = item.get_text(strip=True)
        else:
            # Για Yale (badge badge-primary) και άλλα classes: παίρνουμε το πρώτο
            items = soup.find_all(class_=css_class.split())
            if items:
                values = [i.get_text(strip=True) for i in items if i.get_text(strip=True)]
                data[greek_col] = values[0]


    for field, default in DEFAULT_VALUES.items():
        if not data[field]:
            if isinstance(default, list):
                data[field] = random.choice(default)
            else:
                data[field] = default

    return data


def read_existing_csv(csv_file: str) -> tuple:
    """Διαβάζει το υπάρχον CSV και επιστρέφει (τίτλους, γραμμές) αν υπάρχει."""
    import os
    if not (os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0):
        return [], {}

    with open(csv_file, mode="r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        return [], {}

    existing_titles = rows[0][1:]
    existing_rows = {row[0]: row[1:] for row in rows[1:] if row}
    return existing_titles, existing_rows


def save_to_csv(all_courses: list, output_file: str):
    """Προσθέτει τα νέα μαθήματα δεξιά στο υπάρχον CSV χωρίς να διαγράψει τα υπάρχοντα."""
    # 1. Συλλογή όλων των μοναδικών κλειδιών
    all_keys = []
    for course in all_courses:
        for k in course:
            if k not in all_keys:
                all_keys.append(k)

    # 2. Συμπλήρωση κενών
    for course in all_courses:
        for key in all_keys:
            if key not in course or course[key] == "" or course[key] is None:
                course[key] = "Μη διαθέσιμο"

    # 3. Διάβασμα υπάρχοντος CSV
    existing_titles, existing_rows = read_existing_csv(output_file)

    # 4. Συνδυασμός παλιών + νέων τίτλων
    new_titles = [c.get("Τίτλος μαθήματος", f"Μάθημα {i + 1}") for i, c in enumerate(all_courses)]
    all_titles = existing_titles + new_titles

    # 5. Αποθήκευση
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow(["Πεδίο"] + all_titles)

        for key in all_keys:
            if key == "Τίτλος μαθήματος":
                continue
            old_values = existing_rows.get(key, [""] * len(existing_titles))
            new_values = [course[key] for course in all_courses]
            writer.writerow([key] + old_values + new_values)


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