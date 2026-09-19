"""JSON-based persistence layer for the Student Performance Dashboard.

All public functions accept and return plain Python dicts so the persistence
layer remains fully decoupled from the model layer.  Callers in the UI and
core layers convert between Student objects and dicts as needed.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from core.models import Student

# Path to the data file — relative to the project root
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(_DATA_DIR, "students.json")


def _ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""
    os.makedirs(_DATA_DIR, exist_ok=True)


def load_students() -> list[dict[str, Any]]:
    """Read all student records from the JSON file.

    Returns an empty list if the file does not exist or is malformed.
    """
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_students(students: list[dict[str, Any]]) -> None:
    """Atomically write the full student list to the JSON file.

    Uses a temporary file + rename to prevent data loss on crash.
    """
    _ensure_data_dir()
    tmp_fd, tmp_path = tempfile.mkstemp(dir=_DATA_DIR, suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(students, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, DATA_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def add_student(student: Student) -> None:
    """Append a new student record and persist it.

    Raises ValueError if a student with the same ID already exists.
    """
    students = load_students()
    if any(s["student_id"] == student.student_id for s in students):
        raise ValueError(f"Student ID '{student.student_id}' already exists.")
    students.append(student.to_dict())
    save_students(students)


def get_student_by_id(student_id: str) -> dict[str, Any] | None:
    """Return the student dict matching student_id, or None if not found."""
    for student in load_students():
        if student["student_id"] == student_id:
            return student
    return None


def update_student(student_id: str, updated_student: Student) -> bool:
    """Replace the student record identified by student_id with updated_student.

    Returns True if the record was found and updated, False otherwise.
    """
    students = load_students()
    for i, s in enumerate(students):
        if s["student_id"] == student_id:
            students[i] = updated_student.to_dict()
            save_students(students)
            return True
    return False


def delete_student(student_id: str) -> bool:
    """Remove the student with the given student_id.

    Returns True if a record was removed, False if not found.
    """
    students = load_students()
    filtered = [s for s in students if s["student_id"] != student_id]
    if len(filtered) == len(students):
        return False
    save_students(filtered)
    return True


def student_id_exists(student_id: str) -> bool:
    """Return True if a student with the given ID already exists."""
    return any(s["student_id"] == student_id for s in load_students())


def load_all_students_as_objects() -> list[Student]:
    """Load all persisted students and return them as Student objects."""
    return [Student.from_dict(s) for s in load_students()]
