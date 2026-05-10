import tkinter as tk

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

# --- Κείμενο 1: Η υπάρχουσα λίστα με τα ονόματα και τα ΑΜ ---
lista_mathiton = """Συμμετέχοντες | Αριθμός Μητρώου |
------------------|-----------------|
Μιχαήλ Άγγελος... | 1115538         |
Κωνσταντίνος...   | 1119106         |
Θεοφάνης...       | 1115472         |"""

# Προσοχή: Το βάζουμε μέσα στο 'content_frame', ΟΧΙ στο 'root'
left_label = tk.Label(content_frame, text=lista_mathiton, justify="left", font=("Consolas", 10))
# Το κολλάμε στα ΑΡΙΣΤΕΡΑ τουf αόρατου κουτιού
left_label.pack(side=tk.LEFT)

# --- Κείμενο 2: Το ΝΕΟ σου Label που θα μπει δίπλα ---
# Προσοχή: Το βάζουμε και αυτό στο 'content_frame'
right_label = tk.Label(content_frame, text="Τμήμα Μηχανικών Η/Υ και Πληροφορικής\n Πανεπιστήμιο Πατρών", justify="left", fg="black",font=("Arial", 12, "bold"))
# Το κολλάμε κι αυτό στα ΑΡΙΣΤΕΡΑ (άρα θα μπει ακριβώς δίπλα από το προηγούμενο)
# Το padx=50 του δίνει μια απόσταση 50 pixels από τη λίστα για να μην κολλάνε
right_label.pack(side=tk.LEFT, padx=50)


# 3. Έναρξη του event loop
root.mainloop()