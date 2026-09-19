"""Input validation functions for the Student Performance Dashboard.

Every function returns None when the input is valid, or a non-empty
error string describing the problem.  No Streamlit imports here.
"""

from __future__ import annotations


def validate_student_id(student_id: str, existing_ids: list[str]) -> str | None:
    """Validate a student ID.

    Rules:
    - Must be non-empty after stripping whitespace.
    - Must not already exist in existing_ids (case-insensitive).
    """
    if not student_id or not student_id.strip():
        return "Student ID cannot be empty."
    if student_id.strip().lower() in [eid.lower() for eid in existing_ids]:
        return f"Student ID '{student_id.strip()}' already exists. Use a unique ID."
    return None


def validate_name(name: str) -> str | None:
    """Validate a student name.

    Rules:
    - Must be non-empty after stripping whitespace.
    - Maximum 100 characters.
    """
    if not name or not name.strip():
        return "Student name cannot be empty."
    if len(name.strip()) > 100:
        return "Student name must be 100 characters or fewer."
    return None


def validate_attendance(value: float | int | str) -> str | None:
    """Validate an attendance percentage.

    Rules:
    - Must be numeric.
    - Must be in the range 0 to 100 (inclusive).
    """
    try:
        att = float(value)
    except (ValueError, TypeError):
        return "Attendance must be a numeric value."
    if att < 0 or att > 100:
        return "Attendance must be between 0 and 100."
    return None


def validate_subject_name(name: str, existing_names: list[str]) -> str | None:
    """Validate a subject name within a student's subject list.

    Rules:
    - Must be non-empty after stripping whitespace.
    - Must not duplicate an existing subject name for the same student
      (case-insensitive comparison).
    """
    if not name or not name.strip():
        return "Subject name cannot be empty."
    if name.strip().lower() in [n.lower() for n in existing_names]:
        return f"Subject '{name.strip()}' is already added for this student."
    return None


def validate_marks(
    marks_obtained: float | int | str,
    max_marks: float | int | str,
) -> str | None:
    """Validate marks obtained against the maximum marks.

    Rules:
    - Both values must be numeric.
    - max_marks must be > 0.
    - marks_obtained must be >= 0.
    - marks_obtained must be <= max_marks.
    """
    try:
        obtained = float(marks_obtained)
    except (ValueError, TypeError):
        return "Marks obtained must be a numeric value."
    try:
        maximum = float(max_marks)
    except (ValueError, TypeError):
        return "Maximum marks must be a numeric value."
    if maximum <= 0:
        return "Maximum marks must be greater than 0."
    if obtained < 0:
        return "Marks obtained cannot be negative."
    if obtained > maximum:
        return f"Marks obtained ({obtained}) cannot exceed maximum marks ({maximum})."
    return None


def validate_student_record(
    student_id: str,
    name: str,
    attendance: float | int | str,
    subjects: list[dict[str, object]],
    existing_ids: list[str],
) -> list[str]:
    """Composite validator for a complete student record.

    Runs all individual validators and returns a list of error strings.
    An empty list means the record is fully valid.

    subjects is a list of dicts with keys: subject_name, marks_obtained, max_marks.
    """
    errors: list[str] = []

    id_err = validate_student_id(student_id, existing_ids)
    if id_err:
        errors.append(id_err)

    name_err = validate_name(name)
    if name_err:
        errors.append(name_err)

    att_err = validate_attendance(attendance)
    if att_err:
        errors.append(att_err)

    seen_names: list[str] = []
    for i, subj in enumerate(subjects, start=1):
        subj_name = str(subj.get("subject_name", ""))
        obtained = subj.get("marks_obtained", 0)
        maximum = subj.get("max_marks", 100)

        name_err = validate_subject_name(subj_name, seen_names)
        if name_err:
            errors.append(f"Subject {i}: {name_err}")
        else:
            seen_names.append(subj_name.strip())

        marks_err = validate_marks(obtained, maximum)
        if marks_err:
            errors.append(f"Subject {i} ({subj_name}): {marks_err}")

    return errors
