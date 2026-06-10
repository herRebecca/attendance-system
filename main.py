

import tkinter as tk
from tkinter import messagebox

# app imports
from db import init_db, add_student, validate_student
from auth import login_user
from student_ui import StudentDashboard
from lecturer_ui import LecturerDashboard
from admin_ui import AdminDashboard
from ui_theme import COLORS, button, configure_root, panel


def main():
    """Create the main application window and show the entry portal."""
    root = tk.Tk()
    root.title("Attendance Management System")

    # initialize window relative to the user's screen and allow resizing
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    init_w = int(screen_w * 0.9)
    init_h = int(screen_h * 0.9)
    x = (screen_w - init_w) // 2
    y = (screen_h - init_h) // 2
    root.geometry(f"{init_w}x{init_h}+{x}+{y}")
    root.minsize(480, 520)
    root.resizable(True, True)
    configure_root(root)

    # ensure database exists before any login or registration actions
    init_db()

    header = tk.Frame(root, bg="#111827", height=100)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text="Attendance Management System",
        font=("Segoe UI", 21, "bold"),
        bg="#111827",
        fg="white"
    ).pack(pady=(24, 4))

    tk.Label(
        header,
        text="Group 8 · CSC 302",
        font=("Segoe UI", 10),
        bg="#111827",
        fg="#CBD5E1"
    ).pack()

    body = tk.Frame(root, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=28, pady=24)

    tk.Label(
        body,
        text="Select your portal",
        font=("Segoe UI", 12, "bold"),
        bg=COLORS["app_bg"],
        fg=COLORS["text"]
    ).pack(pady=(0, 22))

    card_row = tk.Frame(body, bg=COLORS["app_bg"])
    card_row.pack(fill="x")

    def make_card(parent, icon_text, title, subtitle, accent, cmd, button_text):
        # Create a styled card with a title, description and action button.
        card = panel(parent, cursor="hand2")
        card.pack(side="left", expand=True, fill="both",
                  padx=(0, 8) if title == "Student Portal" else (8, 0))

        inner = tk.Frame(card, bg=COLORS["panel_bg"], padx=20, pady=24)
        inner.pack(fill="both", expand=True)

        icon_frame = tk.Frame(inner, bg=accent, width=48, height=48)
        icon_frame.pack(pady=(0, 12))
        icon_frame.pack_propagate(False)
        tk.Label(
            icon_frame,
            text=icon_text,
            font=("Segoe UI", 18),
            bg=accent,
            fg="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            inner,
            text=title,
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["panel_bg"],
            fg=COLORS["text"]
        ).pack()

        tk.Label(
            inner,
            text=subtitle,
            font=("Segoe UI", 10),
            bg=COLORS["panel_bg"],
            fg=COLORS["muted"],
            wraplength=156,
            justify="center"
        ).pack(pady=(6, 16))

        action_button = button(
            inner,
            text=button_text,
            command=cmd,
        )
        action_button.pack()
        return card

    make_card(
        card_row,
        icon_text="👤",
        title="Student Portal",
        subtitle="Log in to view your assigned courses and attendance reports.",
        accent="#2563EB",
        cmd=lambda: open_student_login(root),
        button_text="Student Login"
    )

    make_card(
        card_row,
        icon_text="🎓",
        title="Lecturer / Admin",
        subtitle="Access lecturer attendance and admin management screens.",
        accent="#0F766E",
        cmd=lambda: open_lecturer_login(root),
        button_text="Lecturer / Admin Login"
    )

    reg_frame = tk.Frame(body, bg=COLORS["app_bg"])
    reg_frame.pack(pady=(24, 0))

    tk.Label(
        reg_frame,
        text="New student? ",
        font=("Segoe UI", 10),
        bg=COLORS["app_bg"],
        fg=COLORS["muted"]
    ).pack(side="left")

    reg_link = tk.Label(
        reg_frame,
        text="Register here",
        font=("Segoe UI", 10, "underline"),
        bg=COLORS["app_bg"],
        fg=COLORS["primary"],
        cursor="hand2"
    )
    reg_link.pack(side="left")
    reg_link.bind("<Button-1>", lambda event: open_student_register(root))

    tk.Label(
        body,
        text="Department of Computer Science · v1.0",
        font=("Segoe UI", 9),
        bg=COLORS["app_bg"],
        fg=COLORS["muted"]
    ).pack(side="bottom", pady=(14, 0))

    root.mainloop()

# ─────────────────────────────────────────────────────────────
# Dialogs and navigation (defined after main for clarity)
# these use the running `root` as parent when called via lambdas
# ─────────────────────────────────────────────────────────────
def labeled_entry(parent, label_text, show=None, pady=(8, 0)):
    """Create a label and entry pair."""
    tk.Label(parent, text=label_text).pack(pady=pady)
    entry = tk.Entry(parent, show=show)
    entry.pack()
    return entry


def primary_button(parent, text, command):
    """Create a high-contrast primary button."""
    return button(parent, text, command)


def open_login_dialog(parent, title, geometry, field_labels, submit_text, submit_handler):
    """Open a simple login dialog and return its entered values on submit."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry(geometry)
    win.resizable(False, False)

    entries = [
        labeled_entry(win, label, show="*" if "Password" in label else None, pady=(12, 0) if index == 0 else (8, 0))
        for index, label in enumerate(field_labels)
    ]

    def submit():
        submit_handler(win, [entry.get().strip() for entry in entries])

    primary_button(win, submit_text, submit).pack(pady=12)
    return win


def open_student_login(parent):
    """Open the student login dialog and launch the student dashboard."""
    def submit(win, values):
        matric, password = values
        student = validate_student(matric, password)
        if not student:
            messagebox.showerror("Login Failed", "Invalid matric number or password.")
            return
        win.destroy()
        top = tk.Toplevel(parent)
        StudentDashboard(top, student)

    open_login_dialog(
        parent,
        "Student Login",
        "340x180",
        ["Matric Number:", "Password:"],
        "Login",
        submit
    )


def open_lecturer_login(parent):
    """Open the lecturer/admin login dialog and route to the correct dashboard."""
    def submit(win, values):
        username, password = values
        result = login_user(username, password)
        if not result:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return
        role, user = result
        win.destroy()
        top = tk.Toplevel(parent)
        if role == "lecturer":
            LecturerDashboard(top, user)
        elif role == "admin":
            AdminDashboard(top, user)
        else:
            messagebox.showerror("Login Error", "Unexpected role returned.")

    open_login_dialog(
        parent,
        "Lecturer / Admin Login",
        "360x200",
        ["Username:", "Password:"],
        "Login",
        submit
    )


def open_student_register(parent):
    """Open a registration form for new students."""
    win = tk.Toplevel(parent)
    win.title("Student Registration")
    win.geometry("420x260")
    win.resizable(False, False)

    frm = tk.Frame(win, padx=12, pady=12)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text="Matric Number:").grid(row=0, column=0, sticky="w")
    matric_ent = tk.Entry(frm)
    matric_ent.grid(row=0, column=1, pady=6)

    tk.Label(frm, text="Full Name:").grid(row=1, column=0, sticky="w")
    name_ent = tk.Entry(frm)
    name_ent.grid(row=1, column=1, pady=6)

    tk.Label(frm, text="Password:").grid(row=2, column=0, sticky="w")
    pwd_ent = tk.Entry(frm, show="*")
    pwd_ent.grid(row=2, column=1, pady=6)

    tk.Label(frm, text="Level:").grid(row=3, column=0, sticky="w")
    level_ent = tk.Entry(frm)
    level_ent.grid(row=3, column=1, pady=6)

    def submit():
        matric = matric_ent.get().strip()
        name = name_ent.get().strip()
        password = pwd_ent.get().strip()
        level = level_ent.get().strip()
        if not all((matric, name, password, level)):
            messagebox.showwarning("Missing Fields", "Please fill in all fields.")
            return
        try:
            add_student(matric, name, password, level)
        except Exception as e:
            messagebox.showerror("Error", f"Could not register student: {e}")
            return
        messagebox.showinfo("Success", "Student registered successfully.")
        win.destroy()

    primary_button(frm, "Register", submit).grid(row=4, column=0, columnspan=2, pady=12)


if __name__ == "__main__":
    main()
