import requests
from bs4 import BeautifulSoup
import csv
import re

# ---------------------------------------------------------------
# ΣΗΜΕΙΩΣΗ: Τα sites πανεπιστημίων συχνά χρησιμοποιούν Cloudflare/WAF
# ---------------------------------------------------------------

URLS = [
    "https://pll.harvard.edu/course/using-python-research",
    "https://pll.harvard.edu/course/cs50-lawyers",
    "https://online.yale.edu/programs/foundations-animal-ethics",
    "https://online.yale.edu/programs/foundations-of-bioethics",
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
    "Subject": "Θεματική κατηγορία",
    "Difficulty": "Επίπεδο δυσκολίας",
    "Price": "Κόστος",
    "Duration": "Διάρκεια",
    "Language": "Γλώσσα διδασκαλίας"
}


def scrape_course(url: str) -> dict:
    """Κάνει scrape τη σελίδα του μαθήματος και επιστρέφει dict με τα δεδομένα."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Αρχικοποίηση με τα ΑΚΡΙΒΗ ονόματα που ζητήθηκαν
    data = {
        "Τίτλος μαθήματος": "",
        "Πάροχος / Πανεπιστήμιο": "",
        "Θεματική κατηγορία": "",
        "Επίπεδο δυσκολίας": "",
        "Κόστος": "",
        "Διάρκεια": "",
        "Γλώσσα διδασκαλίας": ""
    }

    # 1. Τίτλος
    title_tag = soup.find("h1")
    if title_tag:
        data["Τίτλος μαθήματος"] = title_tag.get_text(strip=True)

    # 2. Πάροχος / Πανεπιστήμιο (Δυναμικά ανάλογα το URL)
    if "harvard.edu" in url:
        data["Πάροχος / Πανεπιστήμιο"] = "Harvard University"
    elif "yale.edu" in url:
        data["Πάροχος / Πανεπιστήμιο"] = "Yale University"
    else:
        data["Πάροχος / Πανεπιστήμιο"] = "Άγνωστος Πάροχος"

    # 3. Βασικά metadata
    for eng_label, greek_col in FIELD_MAP.items():
        tag = soup.find(string=re.compile(eng_label))
        if tag:
            parent = tag.find_parent()
            sibling = parent.find_next_sibling() if parent else None
            if sibling:
                data[greek_col] = sibling.get_text(strip=True)

    return data


def save_to_csv(all_courses: list, output_file: str):
    """Αποθηκεύει τα δεδομένα σε CSV, όπου κάθε γραμμή είναι ένα πεδίο και κάθε στήλη ένα μάθημα."""
    # Κρατάμε τα κλειδιά από το πρώτο μάθημα (εφόσον όλα έχουν τα ίδια κλειδιά)
    keys = list(all_courses[0].keys()) if all_courses else []

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # Header row: Η λέξη "Πεδίο" και οι Τίτλοι των μαθημάτων
        titles = [c.get("Τίτλος μαθήματος", f"Μάθημα {i + 1}") for i, c in enumerate(all_courses)]
        writer.writerow(["Πεδίο"] + titles)

        # Data rows: Για κάθε πεδίο, παίρνουμε την τιμή του για κάθε μάθημα
        for key in keys:
            # Εξαιρούμε τον τίτλο από τις γραμμές δεδομένων γιατί υπάρχει ήδη στο header
            if key == "Τίτλος μαθήματος":
                continue

            row = [key] + [course.get(key, "") for course in all_courses]
            writer.writerow(row)


def main():
    all_courses = []

    for url in URLS:
        print(f"⏳ Scraping: {url}")
        try:
            data = scrape_course(url)
            all_courses.append(data)
            print(f"  ✅ {data.get('Τίτλος μαθήματος', 'Άγνωστος τίτλος')}")
        except requests.HTTPError as e:
            print(f"  ❌ HTTP Error {e.response.status_code} για {url}")
        except Exception as e:
            print(f"  ❌ Σφάλμα: {e}")

    if not all_courses:
        print("\n⚠️  Δεν βρέθηκαν δεδομένα. Έλεγξε τη σύνδεσή σου και δοκίμασε τοπικά.")
        return

    output_file = "courses_data.csv"
    save_to_csv(all_courses, output_file)
    print(f"\n📄 Αποθηκεύτηκε επιτυχώς στο {output_file}")


if __name__ == "__main__":
    main()