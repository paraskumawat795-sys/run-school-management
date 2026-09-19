"""Unit tests for core/validator.py."""

from __future__ import annotations

import pytest

from core.validator import (
    validate_attendance,
    validate_marks,
    validate_name,
    validate_student_id,
    validate_student_record,
    validate_subject_name,
)


# ── validate_student_id ───────────────────────────────────────────────────────

class TestValidateStudentId:
    def test_empty_string_returns_error(self):
        assert validate_student_id("", []) is not None

    def test_whitespace_only_returns_error(self):
        assert validate_student_id("   ", []) is not None

    def test_duplicate_returns_error(self):
        assert validate_student_id("S001", ["S001", "S002"]) is not None

    def test_duplicate_case_insensitive(self):
        assert validate_student_id("s001", ["S001"]) is not None

    def test_unique_id_returns_none(self):
        assert validate_student_id("S003", ["S001", "S002"]) is None

    def test_empty_existing_list_returns_none(self):
        assert validate_student_id("S001", []) is None


# ── validate_name ─────────────────────────────────────────────────────────────

class TestValidateName:
    def test_empty_string_returns_error(self):
        assert validate_name("") is not None

    def test_whitespace_only_returns_error(self):
        assert validate_name("   ") is not None

    def test_valid_name_returns_none(self):
        assert validate_name("Alice Johnson") is None

    def test_name_over_100_chars_returns_error(self):
        long_name = "A" * 101
        assert validate_name(long_name) is not None

    def test_name_exactly_100_chars_returns_none(self):
        name_100 = "A" * 100
        assert validate_name(name_100) is None


# ── validate_attendance ───────────────────────────────────────────────────────

class TestValidateAttendance:
    def test_below_zero_returns_error(self):
        assert validate_attendance(-1) is not None

    def test_above_100_returns_error(self):
        assert validate_attendance(101) is not None

    def test_zero_is_valid(self):
        assert validate_attendance(0) is None

    def test_100_is_valid(self):
        assert validate_attendance(100) is None

    def test_75_is_valid(self):
        assert validate_attendance(75) is None

    def test_non_numeric_returns_error(self):
        assert validate_attendance("abc") is not None

    def test_float_string_is_valid(self):
        assert validate_attendance("82.5") is None


# ── validate_subject_name ─────────────────────────────────────────────────────

class TestValidateSubjectName:
    def test_empty_returns_error(self):
        assert validate_subject_name("", []) is not None

    def test_whitespace_only_returns_error(self):
        assert validate_subject_name("   ", []) is not None

    def test_duplicate_returns_error(self):
        assert validate_subject_name("Math", ["Math", "Science"]) is not None

    def test_duplicate_case_insensitive(self):
        assert validate_subject_name("math", ["Math"]) is not None

    def test_unique_subject_returns_none(self):
        assert validate_subject_name("English", ["Math", "Science"]) is None

    def test_first_subject_returns_none(self):
        assert validate_subject_name("Math", []) is None


# ── validate_marks ────────────────────────────────────────────────────────────

class TestValidateMarks:
    def test_obtained_exceeds_max_returns_error(self):
        assert validate_marks(110, 100) is not None

    def test_negative_obtained_returns_error(self):
        assert validate_marks(-5, 100) is not None

    def test_zero_max_returns_error(self):
        assert validate_marks(0, 0) is not None

    def test_negative_max_returns_error(self):
        assert validate_marks(50, -10) is not None

    def test_valid_marks_returns_none(self):
        assert validate_marks(75, 100) is None

    def test_zero_obtained_is_valid(self):
        assert validate_marks(0, 100) is None

    def test_obtained_equals_max_is_valid(self):
        assert validate_marks(100, 100) is None

    def test_non_numeric_obtained_returns_error(self):
        assert validate_marks("abc", 100) is not None

    def test_non_numeric_max_returns_error(self):
        assert validate_marks(50, "xyz") is not None

    def test_decimal_marks_valid(self):
        assert validate_marks(18.5, 20) is None


# ── validate_student_record ───────────────────────────────────────────────────

class TestValidateStudentRecord:
    def _valid_subjects(self) -> list[dict]:
        return [
            {"subject_name": "Math", "marks_obtained": 80, "max_marks": 100},
            {"subject_name": "Science", "marks_obtained": 70, "max_marks": 100},
        ]

    def test_valid_record_returns_empty_list(self):
        errors = validate_student_record("S001", "Alice", 80, self._valid_subjects(), [])
        assert errors == []

    def test_duplicate_id_caught(self):
        errors = validate_student_record("S001", "Alice", 80, self._valid_subjects(), ["S001"])
        assert any("already exists" in e for e in errors)

    def test_empty_name_caught(self):
        errors = validate_student_record("S001", "", 80, self._valid_subjects(), [])
        assert any("name" in e.lower() for e in errors)

    def test_invalid_attendance_caught(self):
        errors = validate_student_record("S001", "Alice", 110, self._valid_subjects(), [])
        assert any("attendance" in e.lower() for e in errors)

    def test_invalid_marks_caught(self):
        subjects = [{"subject_name": "Math", "marks_obtained": 120, "max_marks": 100}]
        errors = validate_student_record("S001", "Alice", 80, subjects, [])
        assert any("Math" in e or "exceed" in e.lower() for e in errors)

    def test_duplicate_subject_caught(self):
        subjects = [
            {"subject_name": "Math", "marks_obtained": 80, "max_marks": 100},
            {"subject_name": "Math", "marks_obtained": 70, "max_marks": 100},
        ]
        errors = validate_student_record("S001", "Alice", 80, subjects, [])
        assert any("already added" in e for e in errors)

    def test_empty_subject_name_caught(self):
        subjects = [{"subject_name": "", "marks_obtained": 80, "max_marks": 100}]
        errors = validate_student_record("S001", "Alice", 80, subjects, [])
        assert any("empty" in e.lower() for e in errors)

    def test_multiple_errors_all_returned(self):
        errors = validate_student_record("", "", 200, [], [])
        # ID error + name error + attendance error
        assert len(errors) >= 3
