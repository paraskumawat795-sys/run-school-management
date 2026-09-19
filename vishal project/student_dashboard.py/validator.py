"""
validator.py
------------
All input validation logic in one place.
Every method returns (is_valid: bool, message: str).
  - (True, "")               — input is valid
  - (False, "error message") — input is invalid, message explains why

No I/O, no Streamlit imports — pure validation logic only.
"""

import re
from constants import DEFAULT_MAX_MARKS


class Validator:
    """Static validation methods for every user-supplied field."""

    # ------------------------------------------------------------------
    # Student ID
    # ------------------------------------------------------------------

    @staticmethod
    def validate_student_id(
        sid: str,
        existing_ids: list[str],
    ) -> tuple[bool, str]:
        """
        Student ID rules:
        - Non-empty after stripping whitespace
        - Only letters, digits, hyphens, and underscores
        - Must be unique in existing_ids (case-insensitive)
        """
        sid = sid.strip()
        if not sid:
            return False, "Student ID cannot be empty."
        if not re.match(r"^[A-Za-z0-9_\-]+$", sid):
            return False, "Student ID may only contain letters, digits, hyphens (-), and underscores (_)."
        if sid.upper() in [e.upper() for e in existing_ids]:
            return False, f"Student ID '{sid}' already exists. Please use a unique ID."
        return True, ""

    # ------------------------------------------------------------------
    # Student name
    # ------------------------------------------------------------------

    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        """
        Name rules:
        - Non-empty after stripping
        - Letters, spaces, hyphens, and apostrophes only (to support names like O'Brien)
        - Max 50 characters
        """
        name = name.strip()
        if not name:
            return False, "Student name cannot be empty."
        if len(name) > 50:
            return False, "Student name must be 50 characters or fewer."
        if not re.match(r"^[A-Za-z\s\-']+$", name):
            return False, "Student name may only contain letters, spaces, hyphens, and apostrophes."
        return True, ""

    # ------------------------------------------------------------------
    # Marks
    # ------------------------------------------------------------------

    @staticmethod
    def validate_marks(
        obtained: float | int | str,
        maximum: float | int | str,
    ) -> tuple[bool, str]:
        """
        Marks rules:
        - Both values must be numeric
        - maximum > 0 (cannot be zero — would cause division by zero)
        - obtained >= 0
        - obtained <= maximum
        """
        # Coerce to float
        try:
            obtained = float(obtained)
        except (TypeError, ValueError):
            return False, "Marks obtained must be a number."
        try:
            maximum = float(maximum)
        except (TypeError, ValueError):
            return False, f"Maximum marks must be a number (default is {DEFAULT_MAX_MARKS})."

        if maximum <= 0:
            return False, "Maximum marks must be greater than 0."
        if obtained < 0:
            return False, "Marks obtained cannot be negative."
        if obtained > maximum:
            return False, f"Marks obtained ({obtained}) cannot exceed maximum marks ({maximum})."
        return True, ""

    # ------------------------------------------------------------------
    # Attendance
    # ------------------------------------------------------------------

    @staticmethod
    def validate_attendance(value: float | int | str) -> tuple[bool, str]:
        """
        Attendance rules:
        - Must be numeric
        - 0.0 <= value <= 100.0
        """
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False, "Attendance must be a number between 0 and 100."
        if value < 0 or value > 100:
            return False, "Attendance must be between 0 and 100."
        return True, ""

    # ------------------------------------------------------------------
    # Subject name
    # ------------------------------------------------------------------

    @staticmethod
    def validate_subject_name(
        name: str,
        existing_names: list[str] | None = None,
    ) -> tuple[bool, str]:
        """
        Subject name rules:
        - Non-empty after stripping
        - Max 50 characters
        - No duplicate subject names within the same student (case-insensitive)
        """
        name = name.strip()
        if not name:
            return False, "Subject name cannot be empty."
        if len(name) > 50:
            return False, "Subject name must be 50 characters or fewer."
        if existing_names is not None:
            if name.lower() in [n.lower() for n in existing_names]:
                return False, f"Subject '{name}' is already added for this student."
        return True, ""
