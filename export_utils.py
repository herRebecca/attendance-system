import csv
from tkinter import messagebox


def export_csv(file_path, headers, rows):
    """Write rows to a CSV file and show a status dialog."""
    try:
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)
    except Exception as exc:
        messagebox.showerror("Export Failed", f"Could not save CSV: {exc}")
        return False

    messagebox.showinfo("Export Complete", f"CSV saved to {file_path}")
    return True
