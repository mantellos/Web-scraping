import requests
import pandas as pd

url = "https://go.apis.huit.harvard.edu/ats/course/v2/search"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # Αν τα δεδομένα είναι λίστα από dicts:
    df = pd.DataFrame(data)

    # Αν τα δεδομένα είναι nested (π.χ. {"results": [...]}):
    # df = pd.DataFrame(data["results"])

    df.to_csv("api_data.csv", index=False, encoding="utf-8")  # ❌ "api_csv" → ✅ "api_data.csv" (χρειάζεται extension)
    print("Το αρχείο δημιουργήθηκε με επιτυχία")
else:
    print(f"Σφάλμα: {response.status_code} - {response.text}")  #error message