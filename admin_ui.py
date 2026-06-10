import tkinter as tk
from tkinter import messagebox

from db import (
    add_student,
    add_course,
    add_lecturer,
    assign_student_course,
    assign_lecturer_course,
    unassign_student_course,
    unassign_lecturer_course,
    delete_student,
    delete_lecturer,
    get_all_students,
    get_all_courses,
    get_all_lecturers,
    get_student_course_assignments,
    get_lecturer_course_assignments
)
from ui_theme import COLORS, button, configure_root


class AdminDashboard:
    """Admin dashboard for course, student, and lecturer management."""

    def __init__(self, root, admin):
        self.root = root
        self.admin = admin
        self.assignment_frame = None
        self.delete_student_frame = None
        self.delete_lecturer_frame = None
        self.registered_frame = None
        self.body = None

        self.root.title("Admin Dashboard")
        configure_root(self.root)

        self.build_ui()

    def primary_button(self, parent, text, command):
        """Create a high-contrast admin action button."""
        return button(parent, text, command, variant="primary")

    # ─────────────────────────────
    # MAIN UI
    # ─────────────────────────────
    def build_ui(self):

        header = tk.Frame(self.root, bg="#111827", height=88)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"Admin Panel - {self.admin[1]}",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg="#111827"
        ).pack(pady=(18, 2))

        tk.Label(
            header,
            text="Manage students, lecturers, courses and assignments",
            font=("Segoe UI", 10),
            fg="#CBD5E1",
            bg="#111827"
        ).pack()

        self.body = self.create_scrollable_body()

        # ── SECTIONS ──
        self.student_section(self.body)
        self.course_section(self.body)
        self.lecturer_section(self.body)
        self.assignment_section(self.body)
        self.delete_student_section(self.body)
        self.delete_lecturer_section(self.body)
        self.registered_section(self.body)

    def create_scrollable_body(self):
        """Create a scrollable content area for the admin dashboard."""
        container = tk.Frame(self.root, bg=COLORS["app_bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        canvas = tk.Canvas(container, bg=COLORS["app_bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=COLORS["app_bg"])

        body.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return body

    # ─────────────────────────────
    # STUDENT SECTION
    # ─────────────────────────────
    def student_section(self, parent):
        entries = self.form_section(
            parent,
            "Add Student",
            [("Matric:", "matric"), ("Name:", "name"), ("Password:", "password", "*"), ("Level:", "level")],
            "Add Student",
            lambda values: add_student(values["matric"], values["name"], values["password"], values["level"]),
            "Student added",
            "Could not add student"
        )
        return entries

    # ─────────────────────────────
    # COURSE SECTION
    # ─────────────────────────────
    def course_section(self, parent):
        entries = self.form_section(
            parent,
            "Add Course",
            [("Code:", "code"), ("Title:", "title"), ("Level:", "level")],
            "Add Course",
            lambda values: add_course(values["code"], values["title"], values["level"]),
            "Course added",
            "Could not add course"
        )
        return entries

    # ─────────────────────────────
    # LECTURER SECTION
    # ─────────────────────────────
    def lecturer_section(self, parent):
        entries = self.form_section(
            parent,
            "Add Lecturer",
            [("Name:", "name"), ("Username:", "username"), ("Password:", "password", "*")],
            "Add Lecturer",
            lambda values: add_lecturer(values["name"], values["username"], values["password"]),
            "Lecturer added",
            "Could not add lecturer"
        )
        return entries

    def form_section(self, parent, title, fields, button_text, save_func, success_message, error_message):
        """Build a compact admin form and handle save feedback."""
        frame = tk.LabelFrame(
            parent,
            text=title,
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        frame.pack(fill="x", pady=10)

        entries = {}
        for column, field in enumerate(fields):
            label, key, *options = field
            tk.Label(frame, text=label, bg=COLORS["panel_bg"], fg=COLORS["text"]).grid(row=0, column=column, sticky="w")
            entry = tk.Entry(frame, show=options[0] if options else None)
            entry.grid(row=1, column=column, pady=6, padx=4)
            entries[key] = entry

        def save():
            values = {key: entry.get().strip() for key, entry in entries.items()}
            if any(not value for value in values.values()):
                messagebox.showwarning("Missing Fields", "Please fill in all fields.")
                return
            try:
                save_func(values)
            except Exception as e:
                messagebox.showerror("Error", f"{error_message}: {e}")
                return
            for entry in entries.values():
                entry.delete(0, "end")
            messagebox.showinfo("Success", success_message)
            self.refresh_dynamic_sections()

        self.primary_button(frame, button_text, save).grid(row=1, column=len(fields), padx=4)
        return entries

    # ─────────────────────────────
    # ASSIGNMENT SECTION
    # ─────────────────────────────
    def assignment_section(self, parent):

        self.assignment_frame = tk.LabelFrame(
            parent,
            text="Manage Course Assignments",
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        self.assignment_frame.pack(fill="x", pady=10)

        # STUDENT DROPDOWN
        students = get_all_students()
        student_map = {f"{s[1]} ({s[2]})": s[0] for s in students}

        student_var, student_menu = self.option_menu(self.assignment_frame, student_map, "(no students)")
        student_menu.grid(row=0, column=0, padx=4, pady=4)

        # COURSE DROPDOWN
        courses = get_all_courses()
        course_map = {f"{c[1]} - {c[2]}": c[0] for c in courses}

        course_var, course_menu = self.option_menu(self.assignment_frame, course_map, "(no courses)")
        course_menu.grid(row=0, column=1, padx=4, pady=4)

        def assign_student():
            if not student_map or not course_map:
                messagebox.showwarning("Missing Data", "Add at least one student and one course first.")
                return
            try:
                assign_student_course(
                    student_map[student_var.get()],
                    course_map[course_var.get()]
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not assign student: {e}")
                return
            messagebox.showinfo("Success", "Student assigned")
            self.refresh_dynamic_sections()

        student_button = self.primary_button(self.assignment_frame, "Assign Student", assign_student)
        if not student_map or not course_map:
            student_button.configure(state="disabled")
        student_button.grid(row=0, column=2, padx=4, pady=4)

        # LECTURERS
        lecturers = get_all_lecturers()
        lecturer_map = {f"{l[1]} ({l[2]})": l[0] for l in lecturers}

        lecturer_var, lecturer_menu = self.option_menu(self.assignment_frame, lecturer_map, "(no lecturers)")
        lecturer_menu.grid(row=1, column=0, padx=4, pady=4)

        course_var2, course_menu2 = self.option_menu(self.assignment_frame, course_map, "(no courses)")
        course_menu2.grid(row=1, column=1, padx=4, pady=4)

        def assign_lecturer():
            if not lecturer_map or not course_map:
                messagebox.showwarning("Missing Data", "Add at least one lecturer and one course first.")
                return
            try:
                assign_lecturer_course(
                    lecturer_map[lecturer_var.get()],
                    course_map[course_var2.get()]
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not assign lecturer: {e}")
                return
            messagebox.showinfo("Success", "Lecturer assigned")
            self.refresh_dynamic_sections()

        lecturer_button = self.primary_button(self.assignment_frame, "Assign Lecturer", assign_lecturer)
        if not lecturer_map or not course_map:
            lecturer_button.configure(state="disabled")
        lecturer_button.grid(row=1, column=2, padx=4, pady=4)

        student_assignments = get_student_course_assignments()
        student_assignment_map = {
            f"{matric} - {name} -> {code} {title}": (student_id, course_id)
            for student_id, course_id, matric, name, code, title in student_assignments
        }
        student_assignment_var, student_assignment_menu = self.option_menu(
            self.assignment_frame,
            student_assignment_map,
            "(no student assignments)"
        )
        student_assignment_menu.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(14, 4))

        def unassign_student():
            selected = student_assignment_var.get()
            if selected not in student_assignment_map:
                messagebox.showwarning("No Assignment", "There is no student-course assignment to remove.")
                return
            if not messagebox.askyesno("Confirm Unassign", f"Remove this assignment?\n\n{selected}"):
                return
            student_id, course_id = student_assignment_map[selected]
            try:
                unassign_student_course(student_id, course_id)
            except Exception as e:
                messagebox.showerror("Error", f"Could not unassign student: {e}")
                return
            messagebox.showinfo("Success", "Student unassigned from course")
            self.refresh_dynamic_sections()

        unassign_student_button = button(
            self.assignment_frame,
            "Unassign Student",
            unassign_student,
            variant="warning"
        )
        if not student_assignment_map:
            unassign_student_button.configure(state="disabled")
        unassign_student_button.grid(row=2, column=2, padx=4, pady=(14, 4))

        lecturer_assignments = get_lecturer_course_assignments()
        lecturer_assignment_map = {
            f"{name} ({username}) -> {code} {title}": (lecturer_id, course_id)
            for lecturer_id, course_id, name, username, code, title in lecturer_assignments
        }
        lecturer_assignment_var, lecturer_assignment_menu = self.option_menu(
            self.assignment_frame,
            lecturer_assignment_map,
            "(no lecturer assignments)"
        )
        lecturer_assignment_menu.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=4)

        def unassign_lecturer():
            selected = lecturer_assignment_var.get()
            if selected not in lecturer_assignment_map:
                messagebox.showwarning("No Assignment", "There is no lecturer-course assignment to remove.")
                return
            if not messagebox.askyesno("Confirm Unassign", f"Remove this assignment?\n\n{selected}"):
                return
            lecturer_id, course_id = lecturer_assignment_map[selected]
            try:
                unassign_lecturer_course(lecturer_id, course_id)
            except Exception as e:
                messagebox.showerror("Error", f"Could not unassign lecturer: {e}")
                return
            messagebox.showinfo("Success", "Lecturer unassigned from course")
            self.refresh_dynamic_sections()

        unassign_lecturer_button = button(
            self.assignment_frame,
            "Unassign Lecturer",
            unassign_lecturer,
            variant="warning"
        )
        if not lecturer_assignment_map:
            unassign_lecturer_button.configure(state="disabled")
        unassign_lecturer_button.grid(row=3, column=2, padx=4, pady=4)

    def option_menu(self, parent, item_map, empty_label):
        """Create an OptionMenu and disable it when no real options exist."""
        var = tk.StringVar()
        keys = list(item_map.keys()) or [empty_label]
        var.set(keys[0])
        menu = tk.OptionMenu(parent, var, *keys)
        if not item_map:
            menu.configure(state="disabled")
        return var, menu

    def delete_student_section(self, parent):
        """Allow the HOD/admin to delete a student from the system."""
        self.delete_student_frame = tk.LabelFrame(
            parent,
            text="Delete Student",
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        self.delete_student_frame.pack(fill="x", pady=10)

        students = get_all_students()
        student_map = {f"{student[1]} - {student[2]} ({student[3]})": student[0] for student in students}

        tk.Label(
            self.delete_student_frame,
            text="Student:",
            bg=COLORS["panel_bg"],
            fg=COLORS["text"]
        ).grid(row=0, column=0, sticky="w", padx=4)
        student_var, student_menu = self.option_menu(self.delete_student_frame, student_map, "(no students)")
        student_menu.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.delete_student_frame.columnconfigure(0, weight=1)

        def delete_selected_student():
            selected = student_var.get()
            if selected not in student_map:
                messagebox.showwarning("No Student", "There is no student to delete.")
                return
            confirmed = messagebox.askyesno(
                "Confirm Delete",
                f"Delete {selected} and their attendance records?"
            )
            if not confirmed:
                return
            try:
                delete_student(student_map[selected])
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete student: {e}")
                return
            messagebox.showinfo("Success", "Student deleted")
            self.refresh_dynamic_sections()

        delete_button = button(
            self.delete_student_frame,
            "Delete Student",
            delete_selected_student,
            variant="danger"
        )
        if not student_map:
            delete_button.configure(state="disabled")
        delete_button.grid(row=1, column=1, padx=4, pady=4)

    def delete_lecturer_section(self, parent):
        """Allow the HOD/admin to delete a lecturer from the system."""
        self.delete_lecturer_frame = tk.LabelFrame(
            parent,
            text="Delete Lecturer",
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        self.delete_lecturer_frame.pack(fill="x", pady=10)

        lecturers = get_all_lecturers()
        lecturer_map = {f"{lecturer[1]} ({lecturer[2]})": lecturer[0] for lecturer in lecturers}

        tk.Label(
            self.delete_lecturer_frame,
            text="Lecturer:",
            bg=COLORS["panel_bg"],
            fg=COLORS["text"]
        ).grid(row=0, column=0, sticky="w", padx=4)
        lecturer_var, lecturer_menu = self.option_menu(self.delete_lecturer_frame, lecturer_map, "(no lecturers)")
        lecturer_menu.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.delete_lecturer_frame.columnconfigure(0, weight=1)

        def delete_selected_lecturer():
            selected = lecturer_var.get()
            if selected not in lecturer_map:
                messagebox.showwarning("No Lecturer", "There is no lecturer to delete.")
                return
            confirmed = messagebox.askyesno(
                "Confirm Delete",
                f"Delete {selected} and their course assignments?"
            )
            if not confirmed:
                return
            try:
                delete_lecturer(lecturer_map[selected])
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete lecturer: {e}")
                return
            messagebox.showinfo("Success", "Lecturer deleted")
            self.refresh_dynamic_sections()

        delete_button = button(
            self.delete_lecturer_frame,
            "Delete Lecturer",
            delete_selected_lecturer,
            variant="danger"
        )
        if not lecturer_map:
            delete_button.configure(state="disabled")
        delete_button.grid(row=1, column=1, padx=4, pady=4)

    def registered_section(self, parent):
        """Show current registered students and lecturers."""
        self.registered_frame = tk.LabelFrame(
            parent,
            text="Registered Users",
            padx=12,
            pady=12,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            highlightbackground=COLORS["panel_border"]
        )
        self.registered_frame.pack(fill="both", pady=10, expand=True)

        students = get_all_students()
        lecturers = get_all_lecturers()

        student_box = tk.Text(self.registered_frame, height=10, width=55, state="normal")
        student_box.insert("1.0", "Registered Students:\n")
        student_box.insert("2.0", "ID | Matric | Name | Level\n")
        student_box.insert("3.0", "" + "-" * 62 + "\n")
        for student in students:
            student_box.insert("end", f"{student[0]} | {student[1]} | {student[2]} | {student[3]}\n")
        student_box.configure(state="disabled")
        student_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

        lecturer_box = tk.Text(self.registered_frame, height=10, width=40, state="normal")
        lecturer_box.insert("1.0", "Registered Lecturers:\n")
        lecturer_box.insert("2.0", "ID | Name | Username\n")
        lecturer_box.insert("3.0", "" + "-" * 45 + "\n")
        for lecturer in lecturers:
            lecturer_box.insert("end", f"{lecturer[0]} | {lecturer[1]} | {lecturer[2]}\n")
        lecturer_box.configure(state="disabled")
        lecturer_box.pack(side="right", fill="both", expand=True, padx=(6, 0))

    def refresh_dynamic_sections(self):
        """Refresh admin sections that depend on students, lecturers, and courses."""
        if self.assignment_frame:
            self.assignment_frame.destroy()
            self.assignment_frame = None
        if self.delete_student_frame:
            self.delete_student_frame.destroy()
            self.delete_student_frame = None
        if self.delete_lecturer_frame:
            self.delete_lecturer_frame.destroy()
            self.delete_lecturer_frame = None
        if self.registered_frame:
            self.registered_frame.destroy()
            self.registered_frame = None
        self.assignment_section(self.body)
        self.delete_student_section(self.body)
        self.delete_lecturer_section(self.body)
        self.registered_section(self.body)
