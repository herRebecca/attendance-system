import sqlite3
from contextlib import closing

DB = "attendance.db"


def get_connection():
    """Open the SQLite database and enforce foreign keys."""
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_one(query, params=()):
    """Run a SELECT query and return one row."""
    with closing(get_connection()) as conn:
        return conn.execute(query, params).fetchone()


def fetch_all(query, params=()):
    """Run a SELECT query and return all rows."""
    with closing(get_connection()) as conn:
        return conn.execute(query, params).fetchall()


def execute_write(query, params=()):
    """Run a write query and return the last inserted row id."""
    with closing(get_connection()) as conn:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid


def init_db():
    """Create the attendance database tables if they do not already exist."""
    conn = get_connection()
    cur = conn.cursor()

    # Create all core tables for students, lecturers, admins, courses and attendance.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        matric_number TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password TEXT NOT NULL,
        department TEXT DEFAULT 'Computer Science',
        level TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS lecturers (
        lecturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_title TEXT NOT NULL,
        level TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        UNIQUE(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS lecturer_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lecturer_id INTEGER,
        course_id INTEGER,
        UNIQUE(lecturer_id, course_id),
        FOREIGN KEY(lecturer_id) REFERENCES lecturers(lecturer_id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance_sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        lecturer_id INTEGER,
        attendance_date TEXT,
        FOREIGN KEY(course_id) REFERENCES courses(course_id),
        FOREIGN KEY(lecturer_id) REFERENCES lecturers(lecturer_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        student_id INTEGER,
        status TEXT CHECK(status IN ('Present','Absent')),
        UNIQUE(session_id, student_id),
        FOREIGN KEY(session_id) REFERENCES attendance_sessions(session_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)

    conn.commit()
    _seed_default_data(conn)
    conn.close()


def _seed_default_data(conn):
    """Seed at least one default admin and lecturer for first-time setup."""
    cur = conn.cursor()

    admin_count = cur.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
    if admin_count == 0:
        cur.execute(
            "INSERT INTO admins(username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    lecturer_count = cur.execute("SELECT COUNT(*) FROM lecturers").fetchone()[0]
    if lecturer_count == 0:
        cur.execute(
            "INSERT INTO lecturers(full_name, username, password) VALUES (?, ?, ?)",
            ("Default Lecturer", "lecturer", "lec123")
        )

    conn.commit()


def add_student(matric, name, password, level):
    """Add a new student to the database."""
    execute_write(
        "INSERT INTO students (matric_number, full_name, password, level) VALUES (?, ?, ?, ?)",
        (matric, name, password, level)
    )


def validate_student(matric, password):
    """Return the student row if credentials are valid."""
    return fetch_one(
        "SELECT * FROM students WHERE matric_number = ? AND password = ?",
        (matric, password)
    )


def get_student_courses(student_id):
    """Return the courses a student is assigned to."""
    return fetch_all(
        """
        SELECT c.course_id, c.course_code, c.course_title
        FROM courses c
        JOIN student_courses sc ON c.course_id = sc.course_id
        WHERE sc.student_id = ?
        """,
        (student_id,)
    )


def get_student_attendance(student_id, course_id):
    """Return attendance records and percentage for a student in one course."""
    rows = fetch_all(
        """
        SELECT s.attendance_date, ar.status
        FROM attendance_records ar
        JOIN attendance_sessions s ON ar.session_id = s.session_id
        WHERE ar.student_id = ? AND s.course_id = ?
        ORDER BY s.attendance_date
        """,
        (student_id, course_id)
    )

    total = len(rows)
    present = sum(1 for _, status in rows if status == "Present")
    percentage = round((present / total) * 100, 2) if total else 0

    return {
        "records": rows,
        "percentage": percentage
    }


def validate_lecturer(username, password):
    """Return the lecturer row if credentials are valid."""
    return fetch_one(
        "SELECT * FROM lecturers WHERE username = ? AND password = ?",
        (username, password)
    )


def get_lecturer_courses(lecturer_id):
    """Return all courses assigned to a lecturer."""
    return fetch_all(
        """
        SELECT c.course_id, c.course_code, c.course_title
        FROM courses c
        JOIN lecturer_courses lc ON c.course_id = lc.course_id
        WHERE lc.lecturer_id = ?
        """,
        (lecturer_id,)
    )


def get_course_attendance(course_id):
    """Return attendance statistics for each student in a course."""
    rows = fetch_all(
        """
        SELECT s.full_name, s.matric_number,
            SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) AS absent,
            COUNT(ar.id) AS total
        FROM students s
        JOIN student_courses sc ON s.student_id = sc.student_id
        LEFT JOIN attendance_sessions sess ON sess.course_id = sc.course_id
        LEFT JOIN attendance_records ar
            ON ar.session_id = sess.session_id
            AND ar.student_id = s.student_id
        WHERE sc.course_id = ?
        GROUP BY s.student_id, s.full_name, s.matric_number
        ORDER BY s.full_name
        """,
        (course_id,)
    )

    results = []
    for full_name, matric_number, present, absent, total in rows:
        present = present or 0
        absent = absent or 0
        total = total or 0
        percentage = round((present / total) * 100, 2) if total else 0
        results.append((full_name, matric_number, present, absent, total, percentage))

    return results


def get_course_sessions(course_id):
    """Return all attendance sessions for a course, sorted by date."""
    return fetch_all(
        """
        SELECT session_id, attendance_date
        FROM attendance_sessions
        WHERE course_id = ?
        ORDER BY attendance_date
        """,
        (course_id,)
    )


def get_session_attendance(session_id):
    """Return attendance details for a single session."""
    return fetch_all(
        """
        SELECT s.student_id, s.full_name, s.matric_number, ar.status
        FROM attendance_records ar
        JOIN students s ON ar.student_id = s.student_id
        WHERE ar.session_id = ?
        ORDER BY s.full_name
        """,
        (session_id,)
    )


def create_session(course_id, lecturer_id, date):
    """Create a new attendance session for a given lecturer and course."""
    return execute_write(
        "INSERT INTO attendance_sessions(course_id, lecturer_id, attendance_date) VALUES (?, ?, ?)",
        (course_id, lecturer_id, date)
    )


def get_students_for_course(course_id):
    """Return every student assigned to a given course."""
    return fetch_all(
        """
        SELECT s.student_id, s.full_name, s.matric_number
        FROM students s
        JOIN student_courses sc ON s.student_id = sc.student_id
        WHERE sc.course_id = ?
        """,
        (course_id,)
    )


def save_attendance_batch(session_id, attendance_rows):
    """Save attendance rows for a session in one transaction."""
    rows = [(session_id, student_id, status) for student_id, status in attendance_rows]
    with closing(get_connection()) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO attendance_records(session_id, student_id, status) VALUES (?, ?, ?)",
            rows
        )
        conn.commit()


def add_course(code, title, level):
    """Add a new course to the database."""
    execute_write(
        "INSERT INTO courses(course_code, course_title, level) VALUES (?, ?, ?)",
        (code, title, level)
    )


def add_lecturer(full_name, username, password):
    """Add a new lecturer to the database."""
    execute_write(
        "INSERT INTO lecturers(full_name, username, password) VALUES (?, ?, ?)",
        (full_name, username, password)
    )


def assign_student_course(student_id, course_id):
    """Assign a student to a course."""
    execute_write(
        "INSERT OR IGNORE INTO student_courses(student_id, course_id) VALUES (?, ?)",
        (student_id, course_id)
    )


def assign_lecturer_course(lecturer_id, course_id):
    """Assign a lecturer to a course."""
    execute_write(
        "INSERT OR IGNORE INTO lecturer_courses(lecturer_id, course_id) VALUES (?, ?)",
        (lecturer_id, course_id)
    )


def unassign_student_course(student_id, course_id):
    """Remove a student from a course."""
    execute_write(
        "DELETE FROM student_courses WHERE student_id = ? AND course_id = ?",
        (student_id, course_id)
    )


def unassign_lecturer_course(lecturer_id, course_id):
    """Remove a lecturer from a course."""
    execute_write(
        "DELETE FROM lecturer_courses WHERE lecturer_id = ? AND course_id = ?",
        (lecturer_id, course_id)
    )


def get_student_course_assignments():
    """Return all student-course assignments for admin management."""
    return fetch_all(
        """
        SELECT s.student_id, c.course_id, s.matric_number, s.full_name, c.course_code, c.course_title
        FROM student_courses sc
        JOIN students s ON s.student_id = sc.student_id
        JOIN courses c ON c.course_id = sc.course_id
        ORDER BY s.full_name, c.course_code
        """
    )


def get_lecturer_course_assignments():
    """Return all lecturer-course assignments for admin management."""
    return fetch_all(
        """
        SELECT l.lecturer_id, c.course_id, l.full_name, l.username, c.course_code, c.course_title
        FROM lecturer_courses lc
        JOIN lecturers l ON l.lecturer_id = lc.lecturer_id
        JOIN courses c ON c.course_id = lc.course_id
        ORDER BY l.full_name, c.course_code
        """
    )


def delete_student(student_id):
    """Delete a student and their related attendance/course records."""
    with closing(get_connection()) as conn:
        conn.execute(
            """
            DELETE FROM attendance_records
            WHERE student_id = ?
            """,
            (student_id,)
        )
        conn.execute("DELETE FROM student_courses WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()


def delete_lecturer(lecturer_id):
    """Delete a lecturer and records tied to attendance sessions they created."""
    with closing(get_connection()) as conn:
        session_ids = [
            row[0]
            for row in conn.execute(
                "SELECT session_id FROM attendance_sessions WHERE lecturer_id = ?",
                (lecturer_id,)
            ).fetchall()
        ]
        if session_ids:
            placeholders = ", ".join("?" for _ in session_ids)
            conn.execute(
                f"DELETE FROM attendance_records WHERE session_id IN ({placeholders})",
                session_ids
            )
        conn.execute("DELETE FROM attendance_sessions WHERE lecturer_id = ?", (lecturer_id,))
        conn.execute("DELETE FROM lecturer_courses WHERE lecturer_id = ?", (lecturer_id,))
        conn.execute("DELETE FROM lecturers WHERE lecturer_id = ?", (lecturer_id,))
        conn.commit()


def validate_admin(username, password):
    """Return the admin row if credentials are valid."""
    return fetch_one(
        "SELECT * FROM admins WHERE username = ? AND password = ?",
        (username, password)
    )


def get_all_students():
    """Return every student registered in the system."""
    return fetch_all(
        """
        SELECT student_id, matric_number, full_name, level
        FROM students
        ORDER BY full_name
        """
    )


def get_all_courses():
    """Return every course registered in the system."""
    return fetch_all(
        """
        SELECT course_id, course_code, course_title, level
        FROM courses
        ORDER BY course_code
        """
    )


def get_all_lecturers():
    """Return every lecturer registered in the system."""
    return fetch_all(
        """
        SELECT lecturer_id, full_name, username
        FROM lecturers
        ORDER BY full_name
        """
    )
