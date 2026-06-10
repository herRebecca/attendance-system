import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import date

from db import (
    get_lecturer_courses,
    get_students_for_course,
    get_course_sessions,
    get_session_attendance,
    get_student_attendance,
    create_session,
    save_attendance_batch
)
from export_utils import export_csv
from ui_theme import COLORS, button, configure_root, panel


class LecturerDashboard:
    """Lecturer dashboard where assigned courses and attendance marking are shown."""

    def __init__(self, root, lecturer):
        self.root = root
        self.lecturer = lecturer

        self.root.title("Lecturer Dashboard")
        configure_root(self.root)

        self.build_ui()

    # ─────────────────────────────
    # MAIN UI
    # ─────────────────────────────
    def build_ui(self):

        header = tk.Frame(self.root, bg="#0F766E", height=88)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"Welcome {self.lecturer[1]}",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg="#0F766E"
        ).pack(pady=(18, 2))

        tk.Label(
            header,
            text="Lecturer Dashboard",
            font=("Segoe UI", 10),
            fg="#CCFBF1",
            bg="#0F766E"
        ).pack()

        body = tk.Frame(self.root, bg=COLORS["app_bg"])
        body.pack(fill="both", expand=True, padx=24, pady=22)

        tk.Label(
            body,
            text="Your Courses",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["app_bg"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        self.card_frame = tk.Frame(body, bg=COLORS["app_bg"])
        self.card_frame.pack(fill="both", expand=True)

        self.load_courses()

    # ─────────────────────────────
    # LOAD COURSES
    # ─────────────────────────────
    def load_courses(self):

        courses = get_lecturer_courses(self.lecturer[0])

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
                text="Assigned courses will appear here after admin setup.",
                bg=COLORS["panel_bg"],
                fg=COLORS["muted"]
            ).pack(anchor="w", pady=(4, 0))
            return

        for course in courses:
            self.make_course_card(course)

    # ─────────────────────────────
    # COURSE CARD (YES — CARDS)
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

        btn_frame = tk.Frame(card, bg=COLORS["panel_bg"])
        btn_frame.pack(anchor="e", pady=(12, 0))

        button(
            btn_frame,
            text="Course Reports",
            command=lambda c=course_id: self.open_course_reports(c),
            variant="secondary"
        ).pack(side="right", padx=(0, 8))

        button(
            btn_frame,
            text="Mark Attendance",
            command=lambda c=course_id: self.open_attendance(c)
        ).pack(side="right")

    # ─────────────────────────────
    # ATTENDANCE WINDOW
    # ─────────────────────────────
    def open_attendance(self, course_id):

        win = tk.Toplevel(self.root)
        win.title("Mark Attendance")
        win.geometry("600x500")
        configure_root(win)

        session_id = create_session(
            course_id,
            self.lecturer[0],
            str(date.today())
        )

        tk.Label(
            win,
            text="Tick Present / Leave unchecked = Absent",
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(16, 10))

        students = get_students_for_course(course_id)

        vars_dict = {}

        # STUDENT LIST
        for student_id, name, matric in students:

            frame = panel(win, padx=12, pady=8)
            frame.pack(fill="x", padx=20, pady=5)

            var = tk.IntVar()
            vars_dict[student_id] = var

            tk.Checkbutton(
                frame,
                text=f"{name} ({matric})",
                variable=var,
                bg=COLORS["panel_bg"],
                fg=COLORS["text"],
                activebackground=COLORS["panel_bg"],
                selectcolor=COLORS["panel_bg"]
            ).pack(anchor="w")

        # SAVE BUTTON
        def submit():
            attendance_rows = [
                (student_id, "Present" if var.get() == 1 else "Absent")
                for student_id, var in vars_dict.items()
            ]
            save_attendance_batch(session_id, attendance_rows)

            win.destroy()
            messagebox.showinfo("Success", "Attendance saved successfully!")

        button(
            win,
            text="Save Attendance",
            command=submit
        ).pack(pady=20)

    def open_course_reports(self, course_id):
        """Open a report generator window for this course."""
        win = tk.Toplevel(self.root)
        win.title("Course Reports")
        win.geometry("900x620")
        configure_root(win)

        left_frame = tk.LabelFrame(
            win,
            text="Per Student Report",
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_frame = tk.LabelFrame(
            win,
            text="Per Session Report",
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        students = get_students_for_course(course_id)
        student_map = {f"{name} ({matric})": sid for sid, name, matric in students}
        student_var = tk.StringVar()
        student_keys = list(student_map.keys()) or ["(no students)"]
        student_var.set(student_keys[0])
        tk.Label(left_frame, text="Choose student:", bg=COLORS["panel_bg"], fg=COLORS["text"]).pack(anchor="w")
        student_menu = tk.OptionMenu(left_frame, student_var, *student_keys)
        if not student_map:
            student_menu.configure(state="disabled")
        student_menu.pack(fill="x", pady=5)

        student_report_box = tk.Text(left_frame, wrap="word", state="disabled", width=48, height=24)
        student_report_box.pack(fill="both", expand=True, pady=(10, 0))

        def show_student_report():
            selected = student_var.get()
            if selected not in student_map:
                return
            student_id = student_map[selected]
            data = get_student_attendance(student_id, course_id)
            records = data["records"]
            present = sum(1 for _, status in records if status == "Present")
            total = len(records)
            absent = total - present
            report = [
                f"Student: {selected}",
                f"Total sessions: {total}",
                f"Present: {present}",
                f"Absent: {absent}",
                f"Attendance: {data['percentage']}%",
                "",
                "Session details:",
            ]
            if records:
                for attendance_date, status in records:
                    report.append(f"{attendance_date}: {status}")
            else:
                report.append("No attendance records yet.")
            student_report_box.configure(state="normal")
            student_report_box.delete("1.0", "end")
            student_report_box.insert("1.0", "\n".join(report))
            student_report_box.configure(state="disabled")

        def export_student_csv():
            selected = student_var.get()
            if selected not in student_map:
                return
            student_id = student_map[selected]
            data = get_student_attendance(student_id, course_id)
            csv_rows = [(attendance_date, status) for attendance_date, status in data["records"]]
            file_path = filedialog.asksaveasfilename(
                parent=win,
                title="Save student report as CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"{selected.replace(' ', '_')}_attendance.csv"
            )
            if not file_path:
                return
            export_csv(file_path, ["Attendance Date", "Status"], csv_rows)

        button(left_frame, "Generate Student Report", show_student_report).pack(pady=8)
        button(left_frame, "Export Student CSV", export_student_csv, variant="secondary").pack(pady=(0, 8))

        sessions = get_course_sessions(course_id)
        session_map = {f"{attendance_date} (ID {session_id})": session_id for session_id, attendance_date in sessions}
        session_var = tk.StringVar()
        session_keys = list(session_map.keys()) or ["(no sessions)"]
        session_var.set(session_keys[0])
        tk.Label(right_frame, text="Choose session:", bg=COLORS["panel_bg"], fg=COLORS["text"]).pack(anchor="w")
        session_menu = tk.OptionMenu(right_frame, session_var, *session_keys)
        if not session_map:
            session_menu.configure(state="disabled")
        session_menu.pack(fill="x", pady=5)

        session_report_box = tk.Text(right_frame, wrap="word", state="disabled", width=48, height=24)
        session_report_box.pack(fill="both", expand=True, pady=(10, 0))

        def show_session_report():
            selected = session_var.get()
            if selected not in session_map:
                return
            session_id = session_map[selected]
            rows = get_session_attendance(session_id)
            present = sum(1 for _, _, _, status in rows if status == "Present")
            total = len(rows)
            absent = total - present
            report = [
                f"Session: {selected}",
                f"Total students: {total}",
                f"Present: {present}",
                f"Absent: {absent}",
                f"Attendance rate: {round((present / total) * 100, 2) if total else 0}%",
                "",
                "Student attendance:",
            ]
            if rows:
                for _, name, matric, status in rows:
                    report.append(f"{name} ({matric}): {status}")
            else:
                report.append("No attendance records stored for this session.")
            session_report_box.configure(state="normal")
            session_report_box.delete("1.0", "end")
            session_report_box.insert("1.0", "\n".join(report))
            session_report_box.configure(state="disabled")

        def export_session_csv():
            selected = session_var.get()
            if selected not in session_map:
                return
            session_id = session_map[selected]
            rows = get_session_attendance(session_id)
            csv_rows = [(name, matric, status) for _, name, matric, status in rows]
            file_path = filedialog.asksaveasfilename(
                parent=win,
                title="Save session report as CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"session_report_{session_id}.csv"
            )
            if not file_path:
                return
            export_csv(file_path, ["Student Name", "Matric Number", "Status"], csv_rows)

        button(right_frame, "Generate Session Report", show_session_report).pack(pady=8)
        button(right_frame, "Export Session CSV", export_session_csv, variant="secondary").pack(pady=(0, 8))
