import tkinter as tk
import subprocess
import os
import sys

venv_python = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")

def fetch_api():
    print("Πατήθηκε η Συλλογή μέσω του API!")
    script_path = os.path.join(os.path.dirname(__file__), "Web-Data-API.py")
    subprocess.Popen(["python", script_path])

def fetch_scrape():
    print("Πατήθηκε η Συλλογή μέσω Scraping!")
    script_path = os.path.join(os.path.dirname(__file__), "Scraping.py")
    subprocess.Popen(["python", script_path])


# 1. Δημιουργία κύριου παραθύρου
root = tk.Tk()
root.title("Information")
root.geometry("820x520")  # πλάτος x ύψος σε pixels
# 2. Widgets (στοιχεία διεπαφής)
label = tk.Label(root, text="Univeristy Courses: ", font=("Arial", 20))
label.pack(pady=10)

# 2. Φτιάχνουμε το "αόρατο κουτί" (Frame) για να μπουν τα στοιχεία δίπλα-δίπλα

content_frame = tk.Frame(root)
# Τοποθετούμε το κουτί στα αριστερά του παραθύρου
content_frame.pack(anchor="w", padx=20)

lista_mathiton = """Συμμετέχοντες | Αριθμός Μητρώου |
--------------|-------------------|
Μιχαήλ Άγγελος Δημηρίδης | 1115538|
Κωνσταντίνος Μαντέλλος   | 1119106|
Θεοφάνης Τζεφρώνης       | 1115472|"""

# Προσοχή: Το βάζουμε μέσα στο 'content_frame', ΟΧΙ στο 'root'
left_label = tk.Label(content_frame, text=lista_mathiton, justify="left", font=("Consolas", 10))
# Το κολλάμε στα ΑΡΙΣΤΕΡΑ του αόρατου κουτιού
left_label.pack(side=tk.LEFT)

right_label = tk.Label(content_frame, text="Τμήμα Μηχανικών Η/Υ και Πληροφορικής\n Πανεπιστήμιο Πατρών", justify="left", fg="black",font=("Arial", 12, "bold"))
# Το padx=50 του δίνει μια απόσταση 50 pixels από τη λίστα για να μην κολλάνε
right_label.pack(side=tk.LEFT, padx=50)

# 4. Δημιουργία νέου Frame ΜΟΝΟ για τα κουμπιά
button_frame = tk.Frame(root)
# Το expand=True λέει στο Frame να απλωθεί και να πιάσει όλο τον διαθέσιμο κενό χώρο, κεντράροντας τα περιεχόμενά του!
button_frame.pack(pady=50)

# Δημιουργία των κουμπιών (τα βάζουμε μέσα στο button_frame)
# Πρόσθεσα λίγο πλάτος (width) και γραμματοσειρά (font) για να φαίνονται πιο ωραία, μπορείς να τα αλλάξεις.
btn_api = tk.Button(button_frame, text="Συλλογή μέσω API", width=20, font=("Arial", 12), command=fetch_api)
btn_api.pack(side=tk.LEFT, padx=40) # Το padx=20 βάζει κενό ΑΝΑΜΕΣΑ στα κουμπιά

btn_scrape = tk.Button(button_frame, text="Συλλογή μέσω Scraping", width=20, font=("Arial", 12), command=fetch_scrape)
btn_scrape.pack(side=tk.LEFT, padx=40)


# Έναρξη του event loop
root.mainloop()