import requests
import csv
import pandas as pd
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

urls = [
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

all_courses = []

for item in urls:
    try:
        response = requests.get(item["url"], headers=item["headers"], timeout=5, verify=False)

        if response.status_code == 200:
            data = response.json()
            if "elements" in data:
                courses = data.get("elements", [])  # Coursera
            else:
                courses = data.get("courses", [])  # Stepik

            if not courses:
                print(f" Το API ({item['url']}) επέστρεψε 0 αποτελέσματα.")
            else:
                print(f"Λήφθηκαν {len(courses)} μαθήματα από: {item['url']}\n")
                print("=" * 65)

                for course in courses[:8]:
                    title    = course.get("name")
                    provider = course.get("provider")
                    category = course.get("courseType", "Uncategorized")
                    duration = course.get("duration","6 months")
                    lang     = course.get("primaryLanguages", "english").upper()
                    price    = course.get("price")
                    cost     = f"{price} $" if price else "Free"
                    level    = course.get("level", "Not specified")

                    print(f"• Τίτλος    : {title}")
                    print(f"• Πάροχος   : {provider}")
                    print(f"• Κατηγορία : {category}")
                    print(f"• Επίπεδο   : {level}")
                    print(f"• Διάρκεια  : {duration}")
                    print(f"• Γλώσσα    : {lang}")
                    print(f"• Κόστος    : {cost}")
                    print("-" * 65)

                all_courses.extend(courses)

        else:
            print(f"Σφάλμα Server {response.status_code} από: {item['url']}")

    except requests.exceptions.Timeout:
        print(f"Timeout - Δεν απάντησε το API: {item['url']}")
    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα σύνδεσης: {item['url']} → {type(e).__name__}")

csv_file = "courses_data.csv"

with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    fieldnames = ["Τίτλος μαθήματος", "Πάροχος / Πανεπιστήμιο", "Θεματική κατηγορία", "Επίπεδο δυσκολίας", "Κόστος", "Διάρκεια", "Γλώσσα διδασκαλίας"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()  # γράφει την πρώτη γραμμή με τα ονόματα των στηλών

    for course in all_courses:
        workload = course.get("workload")
        price    = course.get("price")

        writer.writerow({
            "Τίτλος μαθήματος"   : course.get("name"),
            "Πάροχος / Πανεπιστήμιο": course.get("provider"),
            "Θεματική κατηγορία": course.get("courseType", "Uncategorized"),
            "Επίπεδο δυσκολίας"   : course.get("level", "Not specified"),
            "Κόστος": f"{price} $" if price else "Free",
            "Διάρκεια": course.get("duration", "6 months"),
            "Γλώσσα διδασκαλίας": course.get("primaryLanguages", "english").upper(),
        })

print(f"\nΤα δεδομένα αποθηκεύτηκαν στο αρχείο: {csv_file}")
print(f"Σύνολο μαθημάτων: {len(all_courses)}")