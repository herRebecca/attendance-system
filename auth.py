from db import (
    validate_lecturer,
    validate_admin
)


# ─────────────────────────────
# LOGIN FUNCTION
# ─────────────────────────────
def login_user(username, password):
    """Authenticate a lecturer or admin user."""

    # Lecturers log in with a username and password.
    lecturer = validate_lecturer(username, password)
    if lecturer:
        return ("lecturer", lecturer)

    # Admins also use username and password.
    admin = validate_admin(username, password)
    if admin:
        return ("admin", admin)

    return None
