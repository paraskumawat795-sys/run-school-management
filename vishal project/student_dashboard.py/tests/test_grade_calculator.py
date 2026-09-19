"""
tests/test_grade_calculator.py
-------------------------------
Comprehensive pytest unit tests for GradeCalculator.
Tests cover normal cases, boundary values, and edge cases.
"""

import sys
import os

# Ensure the student_dashboard package is on sys.path when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from grade_calculator import GradeCalculator


# ---------------------------------------------------------------------------
# calculate_totals
# ---------------------------------------------------------------------------

class TestCalculateTotals:
    def test_multiple_subjects(self):
        subjects = [
            {"subject_name": "Math",    "marks_obtained": 80, "max_marks": 100},
            {"subject_name": "Science", "marks_obtained": 70, "max_marks": 100},
            {"subject_name": "English", "marks_obtained": 90, "max_marks": 100},
        ]
        obtained, maximum = GradeCalculator.calculate_totals(subjects)
        assert obtained == 240.0
        assert maximum == 300.0

    def test_single_subject(self):
        subjects = [{"subject_name": "Math", "marks_obtained": 55, "max_marks": 100}]
        obtained, maximum = GradeCalculator.calculate_totals(subjects)
        assert obtained == 55.0
        assert maximum == 100.0

    def test_empty_list(self):
        obtained, maximum = GradeCalculator.calculate_totals([])
        assert obtained == 0.0
        assert maximum == 0.0

    def test_variable_max_marks(self):
        subjects = [
            {"subject_name": "Math",    "marks_obtained": 40, "max_marks": 50},
            {"subject_name": "Science", "marks_obtained": 30, "max_marks": 50},
        ]
        obtained, maximum = GradeCalculator.calculate_totals(subjects)
        assert obtained == 70.0
        assert maximum == 100.0

    def test_zero_marks_obtained(self):
        subjects = [{"subject_name": "Math", "marks_obtained": 0, "max_marks": 100}]
        obtained, maximum = GradeCalculator.calculate_totals(subjects)
        assert obtained == 0.0
        assert maximum == 100.0

    def test_full_marks(self):
        subjects = [
            {"subject_name": "Math",    "marks_obtained": 100, "max_marks": 100},
            {"subject_name": "Science", "marks_obtained": 100, "max_marks": 100},
        ]
        obtained, maximum = GradeCalculator.calculate_totals(subjects)
        assert obtained == 200.0
        assert maximum == 200.0


# ---------------------------------------------------------------------------
# calculate_percentage
# ---------------------------------------------------------------------------

class TestCalculatePercentage:
    def test_normal_calculation(self):
        assert GradeCalculator.calculate_percentage(80, 100) == 80.0

    def test_full_marks(self):
        assert GradeCalculator.calculate_percentage(100, 100) == 100.0

    def test_zero_obtained(self):
        assert GradeCalculator.calculate_percentage(0, 100) == 0.0

    def test_zero_maximum_no_crash(self):
        # Should return 0.0, not raise ZeroDivisionError
        assert GradeCalculator.calculate_percentage(0, 0) == 0.0

    def test_zero_maximum_nonzero_obtained(self):
        assert GradeCalculator.calculate_percentage(50, 0) == 0.0

    def test_fractional_result(self):
        result = GradeCalculator.calculate_percentage(1, 3)
        assert result == round((1 / 3) * 100, 2)

    def test_variable_max(self):
        # 35 out of 50 = 70%
        assert GradeCalculator.calculate_percentage(35, 50) == 70.0


# ---------------------------------------------------------------------------
# calculate_grade
# ---------------------------------------------------------------------------

class TestCalculateGrade:
    # Normal grades
    def test_grade_a_plus(self):
        assert GradeCalculator.calculate_grade(95) == "A+"

    def test_grade_a(self):
        assert GradeCalculator.calculate_grade(85) == "A"

    def test_grade_b(self):
        assert GradeCalculator.calculate_grade(75) == "B"

    def test_grade_c(self):
        assert GradeCalculator.calculate_grade(65) == "C"

    def test_grade_d(self):
        assert GradeCalculator.calculate_grade(55) == "D"

    def test_grade_f(self):
        assert GradeCalculator.calculate_grade(45) == "F"

    # Exact boundary values
    def test_boundary_90_is_a_plus(self):
        assert GradeCalculator.calculate_grade(90) == "A+"

    def test_boundary_89_is_a(self):
        assert GradeCalculator.calculate_grade(89) == "A"

    def test_boundary_80_is_a(self):
        assert GradeCalculator.calculate_grade(80) == "A"

    def test_boundary_79_is_b(self):
        assert GradeCalculator.calculate_grade(79) == "B"

    def test_boundary_70_is_b(self):
        assert GradeCalculator.calculate_grade(70) == "B"

    def test_boundary_69_is_c(self):
        assert GradeCalculator.calculate_grade(69) == "C"

    def test_boundary_60_is_c(self):
        assert GradeCalculator.calculate_grade(60) == "C"

    def test_boundary_59_is_d(self):
        assert GradeCalculator.calculate_grade(59) == "D"

    def test_boundary_50_is_d(self):
        assert GradeCalculator.calculate_grade(50) == "D"

    def test_boundary_49_is_f(self):
        assert GradeCalculator.calculate_grade(49) == "F"

    def test_zero_percent_is_f(self):
        assert GradeCalculator.calculate_grade(0) == "F"

    def test_100_percent_is_a_plus(self):
        assert GradeCalculator.calculate_grade(100) == "A+"

    def test_89_point_9_is_a_not_a_plus(self):
        assert GradeCalculator.calculate_grade(89.9) == "A"
