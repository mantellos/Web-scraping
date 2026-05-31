import csv, os

CSV_FILE = os.path.join(os.path.dirname(__file__), "courses_data.csv")

print("=== 1. Υπάρχει το αρχείο; ===")
print(f"{CSV_FILE} → {os.path.isfile(CSV_FILE)}")

print("\n=== 2. Πρώτες 5 γραμμές (raw bytes) ===")
with open(CSV_FILE, "rb") as f:
    for i, line in enumerate(f):
        if i >= 5: break
        print(repr(line))

print("\n=== 3. DictReader fieldnames ===")
with open(CSV_FILE, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    print("fieldnames:", reader.fieldnames)
    row = next(iter(reader), None)
    print("first row:", row)

print("\n=== 4. Ποιο data_processor φορτώνεται; ===")
import data_processor
print(data_processor.__file__)

print("\n=== 5. load_courses() ===")
from data_processor import CourseRepository
repo = CourseRepository(CSV_FILE)
courses = repo.load_courses()
print(f"Courses: {len(courses)}")
if courses:
    print("Πρώτο:", courses[0])
else:
    print("ΚΕΝΟ — τίποτα δεν φορτώθηκε")