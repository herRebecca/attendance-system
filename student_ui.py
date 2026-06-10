import tkinter as tk
from tkinter import filedialog
from db import get_student_courses, get_student_attendance
from export_utils import export_csv
from ui_theme import COLORS, button, configure_root, panel


class StudentDashboard:
    """Student dashboard for viewing assigned courses and attendance reports."""

    def __init__(self, root, student):
        self.root = root
        self.student = student

        self.root.title("Student Dashboard")
        configure_root(self.root)

        self.build_ui()

    # ─────────────────────────────
    # MAIN UI
    # ─────────────────────────────
    def build_ui(self):

        # HEADER
        header = tk.Frame(self.root, bg="#2563EB", height=88)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"Welcome, {self.student[2]}",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg="#2563EB"
        ).pack(pady=(18, 2))

        tk.Label(
            header,
            text="Student Dashboard",
            font=("Segoe UI", 10),
            fg="#DBEAFE",
            bg="#2563EB"
        ).pack()

        # BODY
        body = tk.Frame(self.root, bg=COLORS["app_bg"])
        body.pack(fill="both", expand=True, padx=24, pady=22)

        tk.Label(
            body,
            text="Your Courses",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["app_bg"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 10))

        self.card_frame = tk.Frame(body, bg=COLORS["app_bg"])
        self.card_frame.pack(fill="both", expand=True)

        self.load_courses()

    # ─────────────────────────────
    # LOAD COURSES
    # ─────────────────────────────
    def load_courses(self):

        student_id = self.student[0]
        courses = get_student_courses(student_id)

        if not courses:
            empty = panel(self.card_frame, padx=18, pady=18)
            empty.pack(fill="x", pady=10)
            tk.Label(
                empty,
                text="No courses assigned yet.",
                font=("Segoe UI", 11, "bold"),
                bg=COLORS["panel_bg"],
                fg=COLORS["text"]
            ).pack(anchor="w")
            tk.Label(
                empty,
                text="Assigned courses will appear here once the admin adds them.",
                bg=COLORS["panel_bg"],
                fg=COLORS["muted"]
            ).pack(anchor="w", pady=(4, 0))
            return

        for course in courses:
            self.make_course_card(course)

    # ─────────────────────────────
    # COURSE CARD
    # ─────────────────────────────
    def make_course_card(self, course):

        course_id, code, title = course

        card = panel(self.card_frame, padx=18, pady=16)
        card.pack(fill="x", pady=10)

        tk.Label(
            card,
            text=f"{code} - {title}",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["panel_bg"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        button(
            card,
            text="View Attendance",
            command=lambda c=course_id: self.show_attendance(c)
        ).pack(anchor="e", pady=(12, 0))

    # ─────────────────────────────
    # ATTENDANCE VIEW
    # ─────────────────────────────
    def show_attendance(self, course_id):

        win = tk.Toplevel(self.root)
        win.title("Attendance Report")
        win.geometry("500x400")
        configure_root(win)

        data = get_student_attendance(self.student[0], course_id)
        records = data["records"]
        present = sum(1 for _, status in records if status == "Present")
        total = len(records)
        absent = total - present

        tk.Label(
            win,
            text=f"Attendance: {data['percentage']}%",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["app_bg"],
            fg=COLORS["text"]
        ).pack(pady=(16, 4))

        tk.Label(
            win,
            text=f"Present: {present}   Absent: {absent}   Total sessions: {total}",
            font=("Segoe UI", 10),
            bg=COLORS["app_bg"],
            fg=COLORS["muted"]
        ).pack(pady=(0, 10))

        def export_attendance_csv():
            """Export the student's attendance records for this course to CSV."""
            file_path = filedialog.asksaveasfilename(
                parent=win,
                title="Save attendance report as CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"student_{self.student[1]}_course_{course_id}.csv"
            )
            if not file_path:
                return
            export_csv(file_path, ["Attendance Date", "Status"], records)

        button(
            win,
            text="Export to CSV",
            command=export_attendance_csv,
            variant="secondary"
        ).pack(pady=(0, 10))

        # RECORD LIST
        for date, status in records:

            color = "#15803D" if status == "Present" else COLORS["danger"]

            row = panel(win, padx=12, pady=8)
            row.pack(fill="x", padx=20, pady=5)

            tk.Label(row, text=date, bg=COLORS["panel_bg"], fg=COLORS["text"]).pack(side="left")
            tk.Label(row, text=status, fg=color, bg=COLORS["panel_bg"], font=("Segoe UI", 10, "bold")).pack(side="right")
