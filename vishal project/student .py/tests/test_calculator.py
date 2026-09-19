"""Unit tests for core/calculator.py."""

from __future__ import annotations

import pytest

from core.calculator import (
    LOW_ATTENDANCE_THRESHOLD,
    LOW_PERFORMANCE_THRESHOLD,
    assign_grade,
    calculate_percentage,
    calculate_total_marks,
    get_class_statistics,
    get_performance_summary,
    is_low_attendance,
    is_low_performance,
)
from core.models import Student, Subject


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_student(
    student_id: str = "S001",
    name: str = "Alice",
    attendance: float = 80.0,
    subjects: list[Subject] | None = None,
) -> Student:
    if subjects is None:
        subjects = [
            Subject("Math", 80, 100),
            Subject("Science", 70, 100),
            Subject("English", 90, 100),
        ]
    return Student(student_id=student_id, name=name, attendance=attendance, subjects=subjects)


# ── calculate_total_marks ─────────────────────────────────────────────────────

class TestCalculateTotalMarks:
    def test_single_subject(self):
        subjects = [Subject("Math", 75, 100)]
        obtained, maximum = calculate_total_marks(subjects)
        assert obtained == 75.0
        assert maximum == 100.0

    def test_multiple_subjects(self):
        subjects = [Subject("Math", 80, 100), Subject("Science", 60, 100)]
        obtained, maximum = calculate_total_marks(subjects)
        assert obtained == 140.0
        assert maximum == 200.0

    def test_empty_subjects(self):
        obtained, maximum = calculate_total_marks([])
        assert obtained == 0.0
        assert maximum == 0.0

    def test_varying_max_marks(self):
        subjects = [Subject("Math", 45, 50), Subject("Science", 30, 50)]
        obtained, maximum = calculate_total_marks(subjects)
        assert obtained == 75.0
        assert maximum == 100.0

    def test_decimal_marks(self):
        subjects = [Subject("Math", 18.5, 20), Subject("Science", 14.5, 20)]
        obtained, maximum = calculate_total_marks(subjects)
        assert obtained == 33.0
        assert maximum == 40.0


# ── calculate_percentage ──────────────────────────────────────────────────────

class TestCalculatePercentage:
    def test_normal(self):
        assert calculate_percentage(80, 100) == 80.0

    def test_full_marks(self):
        assert calculate_percentage(100, 100) == 100.0

    def test_zero_obtained(self):
        assert calculate_percentage(0, 100) == 0.0

    def test_zero_max_marks(self):
        assert calculate_percentage(50, 0) == 0.0

    def test_partial_marks(self):
        assert calculate_percentage(75, 150) == 50.0

    def test_rounding(self):
        result = calculate_percentage(1, 3)
        assert result == 33.33


# ── assign_grade ──────────────────────────────────────────────────────────────

class TestAssignGrade:
    @pytest.mark.parametrize("pct,expected", [
        (100, "A+"),
        (90, "A+"),
        (89, "A"),
        (80, "A"),
        (79, "B"),
        (70, "B"),
        (69, "C"),
        (60, "C"),
        (59, "D"),
        (50, "D"),
        (49, "F"),
        (0,  "F"),
    ])
    def test_grade_boundaries(self, pct: float, expected: str):
        assert assign_grade(pct) == expected

    def test_negative_percentage_returns_na(self):
        assert assign_grade(-1) == "N/A"


# ── get_performance_summary ───────────────────────────────────────────────────

class TestGetPerformanceSummary:
    def test_all_fields_present(self):
        student = make_student()
        summary = get_performance_summary(student)
        expected_keys = {
            "student_id", "name", "attendance", "subjects_count",
            "total_obtained", "total_max", "percentage", "grade",
            "is_low_attendance", "is_low_performance",
        }
        assert expected_keys == set(summary.keys())

    def test_correct_values(self):
        student = make_student(attendance=80.0)
        summary = get_performance_summary(student)
        assert summary["total_obtained"] == 240.0
        assert summary["total_max"] == 300.0
        assert summary["percentage"] == 80.0
        assert summary["grade"] == "A"
        assert summary["is_low_attendance"] is False
        assert summary["is_low_performance"] is False

    def test_no_subjects_gives_na_grade(self):
        student = make_student(subjects=[])
        summary = get_performance_summary(student)
        assert summary["grade"] == "N/A"
        assert summary["percentage"] == 0.0
        assert summary["subjects_count"] == 0


# ── is_low_attendance ─────────────────────────────────────────────────────────

class TestIsLowAttendance:
    def test_below_threshold_is_true(self):
        student = make_student(attendance=74.9)
        assert is_low_attendance(student) is True

    def test_at_threshold_is_false(self):
        student = make_student(attendance=75.0)
        assert is_low_attendance(student) is False

    def test_above_threshold_is_false(self):
        student = make_student(attendance=90.0)
        assert is_low_attendance(student) is False

    def test_zero_attendance_is_true(self):
        student = make_student(attendance=0.0)
        assert is_low_attendance(student) is True


# ── is_low_performance ────────────────────────────────────────────────────────

class TestIsLowPerformance:
    def test_below_threshold_is_true(self):
        subjects = [Subject("Math", 40, 100)]
        student = make_student(subjects=subjects)
        assert is_low_performance(student) is True

    def test_at_threshold_is_false(self):
        subjects = [Subject("Math", 50, 100)]
        student = make_student(subjects=subjects)
        assert is_low_performance(student) is False

    def test_above_threshold_is_false(self):
        student = make_student()  # 80% average
        assert is_low_performance(student) is False

    def test_no_subjects_is_false(self):
        student = make_student(subjects=[])
        assert is_low_performance(student) is False


# ── get_class_statistics ──────────────────────────────────────────────────────

class TestGetClassStatistics:
    def test_empty_list_returns_zeros(self):
        stats = get_class_statistics([])
        assert stats["total_students"] == 0
        assert stats["average_percentage"] == 0.0

    def test_single_student(self):
        student = make_student(attendance=80.0)
        stats = get_class_statistics([student])
        assert stats["total_students"] == 1
        assert stats["average_percentage"] == 80.0
        assert stats["top_scorer_name"] == "Alice"
        assert stats["lowest_scorer_name"] == "Alice"

    def test_multiple_students(self):
        s1 = make_student("S001", "Alice", 80.0, [Subject("Math", 90, 100)])
        s2 = make_student("S002", "Bob", 60.0, [Subject("Math", 40, 100)])
        stats = get_class_statistics([s1, s2])
        assert stats["total_students"] == 2
        assert stats["average_percentage"] == 65.0
        assert stats["top_scorer_name"] == "Alice"
        assert stats["lowest_scorer_name"] == "Bob"
        assert stats["below_50_count"] == 1
        assert stats["below_75_attendance_count"] == 1

    def test_grade_distribution(self):
        s1 = make_student("S001", "Alice", 80, [Subject("Math", 95, 100)])
        s2 = make_student("S002", "Bob", 70, [Subject("Math", 45, 100)])
        stats = get_class_statistics([s1, s2])
        assert stats["grade_distribution"].get("A+") == 1
        assert stats["grade_distribution"].get("F") == 1

    def test_subject_averages(self):
        s1 = make_student("S001", "Alice", 80, [Subject("Math", 80, 100)])
        s2 = make_student("S002", "Bob", 70, [Subject("Math", 60, 100)])
        stats = get_class_statistics([s1, s2])
        assert stats["subject_averages"]["Math"] == 70.0
