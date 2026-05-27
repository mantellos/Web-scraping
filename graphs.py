import matplotlib.pyplot as plt
from collections import Counter
import tkinter.messagebox as messagebox


def _parse_duration_hours(value):
    """Εξάγει τη διάρκεια σε ώρες. Προσαρμόζεται ανάλογα με τα δεδομένα του CSV."""
    if not value:
        return 0
    val_str = str(value).lower()

    # Βρίσκουμε τον πρώτο αριθμό μέσα στο κείμενο
    nums = [int(s) for s in val_str.split() if s.isdigit()]
    if not nums:
        return 0

    num = nums[0]

    # Μετατροπή σε ώρες ανάλογα με το λεκτικό (παράδειγμα λογικής)
    if "Week" in val_str or "εβδομ" in val_str:
        return num * 10  # Υποθέτουμε π.χ. 10 ώρες / εβδομάδα
    elif "months" in val_str or "μήν" in val_str:
        return num * 40  # Υποθέτουμε π.χ. 40 ώρες / μήνα

    return num  # Αν λέει απλώς "15 hours" επιστρέφει το 15