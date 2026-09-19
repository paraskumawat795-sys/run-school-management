"""
tests/test_student_dashboard.py
--------------------------------
Comprehensive pytest unit tests for the Student Performance Dashboard.

Covers:
- GradeCalculator  (totals, percentage, grade)
- Validator        (ID, name, marks, attendance, subject name)
- FileHandler      (load/save roundtrip, missing file, corrupt file)
- StudentManager   (add, edit, delete, filter, statistics)
- Integration      (full workflow: add → enrich → query → persist)
"""

import sys
import os
import json
import tempfile
import shutil

# Allow imports from parent (student_dashboard/) directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from grade_calculator import GradeCalculator
from validator import Validator
from file_handler import FileHandler
from student_manager import StudentManager
from constants import LOW_ATTENDANCE_THRESHOLD, LOW_MARKS_THRESHOLD


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture()
def tmp_data_dir(tmp_path):
    """Return a temporary directory; clean up after the test."""
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture()
def tmp_json(tmp_data_dir):
    """Return a path to a temporary students.json file."""
    return str(tmp_data_dir / "students.json")


@pytest.fixture()
def sample_subjects():
    return [
        {"subject_name": "Mathematics", "marks_obtained": 80, "max_marks": 100},
        {"subject_name": "Science",     "marks_obtained": 70, "max_marks": 100},
        {"subject_name": "English",     "marks_obtained": 60, "max_marks": 100},
    ]


@pytest.fixture()
def sample_student(sample_subjects):
    return {
        "student_id": "S001",
        "name": "Alice Smith",
        "attendance": 85.0,
        "subjects": sample_subjects,
    }


@pytest.fixture()
def manager_with_one(sample_student, tmp_json):
    """StudentManager pre-loaded with one student."""
    mgr = StudentManager([sample_student], tmp_json)
    return mgr


@pytest.fixture()
def manager_empty(tmp_json):
    """Empty StudentManager."""
    return StudentManager([], tmp_json)


# ===========================================================================
# GradeCalculator Tests
# ===========================================================================

class TestGradeCalculatorTotals:
    def test_multiple_subjects(self, sample_subjects):
        obt, mx = GradeCalculator.calculate_totals(sample_subjects)
        assert obt == 210.0
        assert mx == 300.0

    def test_single_subject(self):
        subjects = [{"subject_name": "Math", "marks_obtained": 55, "max_marks": 100}]
        obt, mx = GradeCalculator.calculate_totals(subjects)
        assert obt == 55.0
        assert mx == 100.0

    def test_empty_list(self):
        obt, mx = GradeCalculator.calculate_totals([])
        assert obt == 0.0
        assert mx == 0.0

    def test_variable_max(self):
        subjects = [
            {"subject_name": "A", "marks_obtained": 40, "max_marks": 50},
            {"subject_name": "B", "marks_obtained": 30, "max_marks": 50},
        ]
        obt, mx = GradeCalculator.calculate_totals(subjects)
        assert obt == 70.0
        assert mx == 100.0

    def test_zero_marks(self):
        subjects = [{"subject_name": "X", "marks_obtained": 0, "max_marks": 100}]
        obt, mx = GradeCalculator.calculate_totals(subjects)
        assert obt == 0.0


class TestGradeCalculatorPercentage:
    def test_normal(self):
        assert GradeCalculator.calculate_percentage(80, 100) == 80.0

    def test_zero_max_no_crash(self):
        assert GradeCalculator.calculate_percentage(0, 0) == 0.0

    def test_nonzero_obtained_zero_max(self):
        assert GradeCalculator.calculate_percentage(50, 0) == 0.0

    def test_full_marks(self):
        assert GradeCalculator.calculate_percentage(100, 100) == 100.0

    def test_fractional(self):
        result = GradeCalculator.calculate_percentage(1, 3)
        assert result == round(100 / 3, 2)

    def test_variable_max(self):
        assert GradeCalculator.calculate_percentage(35, 50) == 70.0


class TestGradeCalculatorGrade:
    @pytest.mark.parametrize("pct,expected", [
        (100, "A+"), (90, "A+"), (95, "A+"),
        (89.9, "A"),  (85, "A"),  (80, "A"),
        (79, "B"),    (75, "B"),  (70, "B"),
        (69, "C"),    (65, "C"),  (60, "C"),
        (59, "D"),    (55, "D"),  (50, "D"),
        (49, "F"),    (0, "F"),   (25, "F"),
    ])
    def test_grade_boundaries(self, pct, expected):
        assert GradeCalculator.calculate_grade(pct) == expected


# ===========================================================================
# Validator Tests
# ===========================================================================

class TestValidatorStudentId:
    def test_valid_id(self):
        ok, msg = Validator.validate_student_id("S001", [])
        assert ok is True
        assert msg == ""

    def test_empty_id(self):
        ok, msg = Validator.validate_student_id("", [])
        assert ok is False
        assert "empty" in msg.lower()

    def test_whitespace_only(self):
        ok, msg = Validator.validate_student_id("   ", [])
        assert ok is False

    def test_duplicate_id(self):
        ok, msg = Validator.validate_student_id("S001", ["S001"])
        assert ok is False
        assert "already exists" in msg.lower()

    def test_duplicate_id_case_insensitive(self):
        ok, msg = Validator.validate_student_id("s001", ["S001"])
        assert ok is False

    def test_invalid_characters(self):
        ok, msg = Validator.validate_student_id("S 001", [])
        assert ok is False

    def test_hyphen_and_underscore_allowed(self):
        ok, _ = Validator.validate_student_id("STU-001_A", [])
        assert ok is True


class TestValidatorName:
    def test_valid_name(self):
        ok, msg = Validator.validate_name("Alice Smith")
        assert ok is True

    def test_empty_name(self):
        ok, msg = Validator.validate_name("")
        assert ok is False
        assert "empty" in msg.lower()

    def test_whitespace_only(self):
        ok, msg = Validator.validate_name("   ")
        assert ok is False

    def test_too_long(self):
        ok, msg = Validator.validate_name("A" * 51)
        assert ok is False
        assert "50" in msg

    def test_exactly_50_chars(self):
        ok, _ = Validator.validate_name("A" * 50)
        assert ok is True

    def test_numbers_not_allowed(self):
        ok, msg = Validator.validate_name("Alice123")
        assert ok is False

    def test_apostrophe_allowed(self):
        ok, _ = Validator.validate_name("O'Brien")
        assert ok is True

    def test_hyphen_allowed(self):
        ok, _ = Validator.validate_name("Mary-Jane")
        assert ok is True


class TestValidatorMarks:
    def test_valid_marks(self):
        ok, msg = Validator.validate_marks(80, 100)
        assert ok is True

    def test_zero_marks_obtained(self):
        ok, _ = Validator.validate_marks(0, 100)
        assert ok is True

    def test_full_marks(self):
        ok, _ = Validator.validate_marks(100, 100)
        assert ok is True

    def test_obtained_exceeds_max(self):
        ok, msg = Validator.validate_marks(110, 100)
        assert ok is False
        assert "exceed" in msg.lower() or "cannot" in msg.lower()

    def test_negative_obtained(self):
        ok, msg = Validator.validate_marks(-5, 100)
        assert ok is False
        assert "negative" in msg.lower()

    def test_zero_max(self):
        ok, msg = Validator.validate_marks(50, 0)
        assert ok is False
        assert "greater than 0" in msg.lower()

    def test_non_numeric_obtained(self):
        ok, msg = Validator.validate_marks("abc", 100)
        assert ok is False

    def test_non_numeric_max(self):
        ok, msg = Validator.validate_marks(50, "xyz")
        assert ok is False

    def test_float_marks(self):
        ok, _ = Validator.validate_marks(87.5, 100)
        assert ok is True


class TestValidatorAttendance:
    def test_valid_attendance(self):
        ok, _ = Validator.validate_attendance(85.0)
        assert ok is True

    def test_zero_attendance(self):
        ok, _ = Validator.validate_attendance(0)
        assert ok is True

    def test_100_attendance(self):
        ok, _ = Validator.validate_attendance(100)
        assert ok is True

    def test_above_100(self):
        ok, msg = Validator.validate_attendance(101)
        assert ok is False

    def test_negative(self):
        ok, msg = Validator.validate_attendance(-1)
        assert ok is False

    def test_non_numeric(self):
        ok, msg = Validator.validate_attendance("high")
        assert ok is False


class TestValidatorSubjectName:
    def test_valid(self):
        ok, _ = Validator.validate_subject_name("Mathematics")
        assert ok is True

    def test_empty(self):
        ok, msg = Validator.validate_subject_name("")
        assert ok is False
        assert "empty" in msg.lower()

    def test_duplicate(self):
        ok, msg = Validator.validate_subject_name("Math", ["Math"])
        assert ok is False

    def test_duplicate_case_insensitive(self):
        ok, msg = Validator.validate_subject_name("math", ["Math"])
        assert ok is False

    def test_too_long(self):
        ok, _ = Validator.validate_subject_name("A" * 51)
        assert ok is False

    def test_no_existing_names(self):
        ok, _ = Validator.validate_subject_name("Physics", None)
        assert ok is True


# ===========================================================================
# FileHandler Tests
# ===========================================================================

class TestFileHandler:
    def test_load_missing_file_returns_empty(self, tmp_json):
        result = FileHandler.load(tmp_json)
        assert result == []

    def test_save_and_load_roundtrip(self, tmp_json, sample_student):
        FileHandler.save([sample_student], tmp_json)
        loaded = FileHandler.load(tmp_json)
        assert len(loaded) == 1
        assert loaded[0]["student_id"] == "S001"

    def test_corrupt_json_returns_empty(self, tmp_json):
        with open(tmp_json, "w") as f:
            f.write("{not valid json}")
        result = FileHandler.load(tmp_json)
        assert result == []

    def test_non_array_json_returns_empty(self, tmp_json):
        with open(tmp_json, "w") as f:
            json.dump({"key": "value"}, f)
        result = FileHandler.load(tmp_json)
        assert result == []

    def test_save_creates_file(self, tmp_json):
        FileHandler.save([], tmp_json)
        assert os.path.exists(tmp_json)

    def test_save_multiple_students(self, tmp_json, sample_student):
        student2 = {**sample_student, "student_id": "S002", "name": "Bob Jones"}
        FileHandler.save([sample_student, student2], tmp_json)
        loaded = FileHandler.load(tmp_json)
        assert len(loaded) == 2

    def test_load_empty_array(self, tmp_json):
        FileHandler.save([], tmp_json)
        result = FileHandler.load(tmp_json)
        assert result == []


# ===========================================================================
# StudentManager Tests
# ===========================================================================

class TestStudentManagerAdd:
    def test_add_student(self, manager_empty, sample_subjects, tmp_json):
        manager_empty.add_student("S001", "Alice", 90.0, sample_subjects)
        students = manager_empty.get_all_students()
        assert len(students) == 1
        assert students[0]["student_id"] == "S001"
        assert students[0]["name"] == "Alice"

    def test_add_persists_to_file(self, manager_empty, sample_subjects, tmp_json):
        manager_empty.add_student("S001", "Alice", 90.0, sample_subjects)
        loaded = FileHandler.load(tmp_json)
        assert len(loaded) == 1

    def test_add_multiple_students(self, manager_empty, sample_subjects, tmp_json):
        manager_empty.add_student("S001", "Alice", 90.0, sample_subjects)
        manager_empty.add_student("S002", "Bob", 80.0, sample_subjects)
        assert len(manager_empty.get_all_students()) == 2

    def test_add_enriches_record(self, manager_empty, sample_subjects):
        manager_empty.add_student("S001", "Alice", 90.0, sample_subjects)
        s = manager_empty.get_all_students()[0]
        assert "overall_percentage" in s
        assert "grade" in s
        assert "is_low_attendance" in s
        assert "is_low_performer" in s


class TestStudentManagerUpdate:
    def test_update_name(self, manager_with_one):
        ok = manager_with_one.update_student("S001", "Alice Johnson", 85.0,
                                              manager_with_one.get_student_by_id("S001")["subjects"])
        assert ok is True
        assert manager_with_one.get_student_by_id("S001")["name"] == "Alice Johnson"

    def test_update_attendance(self, manager_with_one):
        subjs = manager_with_one.get_student_by_id("S001")["subjects"]
        manager_with_one.update_student("S001", "Alice Smith", 60.0, subjs)
        assert manager_with_one.get_student_by_id("S001")["attendance"] == 60.0

    def test_update_nonexistent_returns_false(self, manager_with_one):
        ok = manager_with_one.update_student("XXXX", "Nobody", 100.0, [])
        assert ok is False

    def test_update_persists(self, manager_with_one, tmp_json):
        subjs = manager_with_one.get_student_by_id("S001")["subjects"]
        manager_with_one.update_student("S001", "Updated Name", 85.0, subjs)
        loaded = FileHandler.load(tmp_json)
        assert loaded[0]["name"] == "Updated Name"


class TestStudentManagerDelete:
    def test_delete_student(self, manager_with_one):
        ok = manager_with_one.delete_student("S001")
        assert ok is True
        assert manager_with_one.get_student_by_id("S001") is None

    def test_delete_nonexistent_returns_false(self, manager_with_one):
        ok = manager_with_one.delete_student("XXXX")
        assert ok is False

    def test_delete_persists(self, manager_with_one, tmp_json):
        manager_with_one.delete_student("S001")
        loaded = FileHandler.load(tmp_json)
        assert len(loaded) == 0

    def test_delete_removes_from_list(self, manager_with_one):
        manager_with_one.delete_student("S001")
        assert len(manager_with_one.get_all_students()) == 0


class TestStudentManagerEnrichment:
    def test_percentage_calculated(self, manager_with_one):
        # 80+70+60 = 210 / 300 = 70.0%
        s = manager_with_one.get_student_by_id("S001")
        assert s["overall_percentage"] == 70.0

    def test_grade_calculated(self, manager_with_one):
        s = manager_with_one.get_student_by_id("S001")
        assert s["grade"] == "B"

    def test_total_obtained(self, manager_with_one):
        s = manager_with_one.get_student_by_id("S001")
        assert s["total_obtained"] == 210.0

    def test_total_max(self, manager_with_one):
        s = manager_with_one.get_student_by_id("S001")
        assert s["total_max"] == 300.0

    def test_is_low_attendance_false_for_85(self, manager_with_one):
        s = manager_with_one.get_student_by_id("S001")
        assert s["is_low_attendance"] is False

    def test_is_low_performer_false_for_70_percent(self, manager_with_one):
        s = manager_with_one.get_student_by_id("S001")
        assert s["is_low_performer"] is False

    def test_low_attendance_flagged(self, tmp_json, sample_subjects):
        mgr = StudentManager([], tmp_json)
        mgr.add_student("S001", "Alice", LOW_ATTENDANCE_THRESHOLD - 1, sample_subjects)
        s = mgr.get_all_students()[0]
        assert s["is_low_attendance"] is True

    def test_low_performer_flagged(self, tmp_json):
        mgr = StudentManager([], tmp_json)
        low_subjects = [
            {"subject_name": "Math", "marks_obtained": 30, "max_marks": 100},
        ]
        mgr.add_student("S001", "Alice", 80.0, low_subjects)
        s = mgr.get_all_students()[0]
        assert s["is_low_performer"] is True

    def test_empty_subjects_percentage_is_zero(self, tmp_json):
        mgr = StudentManager([], tmp_json)
        mgr.add_student("S001", "Alice", 80.0, [])
        s = mgr.get_all_students()[0]
        assert s["overall_percentage"] == 0.0
        assert s["grade"] == "F"


class TestStudentManagerFilters:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_json):
        self.mgr = StudentManager([], tmp_json)
        # High performer, good attendance
        self.mgr.add_student("S001", "Alice", 90.0, [
            {"subject_name": "Math", "marks_obtained": 95, "max_marks": 100},
        ])
        # Low performer, low attendance
        self.mgr.add_student("S002", "Bob", 60.0, [
            {"subject_name": "Math", "marks_obtained": 40, "max_marks": 100},
        ])
        # Mid-range
        self.mgr.add_student("S003", "Carol", 80.0, [
            {"subject_name": "Science", "marks_obtained": 75, "max_marks": 100},
        ])

    def test_filter_by_grade(self):
        result = self.mgr.filter_by_grade("A+")
        assert len(result) == 1
        assert result[0]["student_id"] == "S001"

    def test_filter_by_subject_present(self):
        result = self.mgr.filter_by_subject("Math")
        assert len(result) == 2

    def test_filter_by_subject_case_insensitive(self):
        result = self.mgr.filter_by_subject("math")
        assert len(result) == 2

    def test_filter_by_subject_not_present(self):
        result = self.mgr.filter_by_subject("History")
        assert len(result) == 0

    def test_get_low_attendance(self):
        result = self.mgr.get_low_attendance()
        assert any(s["student_id"] == "S002" for s in result)

    def test_get_low_performers(self):
        result = self.mgr.get_low_performers()
        assert any(s["student_id"] == "S002" for s in result)

    def test_good_performer_not_in_low_list(self):
        result = self.mgr.get_low_performers()
        assert not any(s["student_id"] == "S001" for s in result)


class TestStudentManagerStatistics:
    def test_empty_statistics(self, manager_empty):
        stats = manager_empty.get_statistics()
        assert stats["total_students"] == 0
        assert stats["class_avg"] == 0.0

    def test_statistics_fields_present(self, manager_with_one):
        stats = manager_with_one.get_statistics()
        for key in ["class_avg", "highest_pct", "lowest_pct", "top_student",
                    "bottom_student", "avg_attendance", "pass_count", "fail_count",
                    "low_attendance_count", "low_performer_count", "total_students"]:
            assert key in stats

    def test_statistics_single_student(self, manager_with_one):
        stats = manager_with_one.get_statistics()
        assert stats["total_students"] == 1
        assert stats["class_avg"] == 70.0
        assert stats["pass_count"] == 1
        assert stats["fail_count"] == 0

    def test_pass_fail_counts(self, tmp_json):
        mgr = StudentManager([], tmp_json)
        mgr.add_student("S001", "Alice", 80.0, [
            {"subject_name": "Math", "marks_obtained": 80, "max_marks": 100},
        ])
        mgr.add_student("S002", "Bob", 80.0, [
            {"subject_name": "Math", "marks_obtained": 30, "max_marks": 100},
        ])
        stats = mgr.get_statistics()
        assert stats["pass_count"] == 1
        assert stats["fail_count"] == 1


# ===========================================================================
# Integration Tests
# ===========================================================================

class TestIntegration:
    def test_full_add_edit_delete_flow(self, tmp_json):
        """Add a student, verify it's saved, edit it, verify edit, delete it."""
        subjects = [{"subject_name": "Math", "marks_obtained": 75, "max_marks": 100}]

        mgr = StudentManager([], tmp_json)
        mgr.add_student("S001", "Test Student", 80.0, subjects)

        # Reload from file to verify persistence
        mgr2 = StudentManager(FileHandler.load(tmp_json), tmp_json)
        assert mgr2.get_student_by_id("S001") is not None
        assert mgr2.get_student_by_id("S001")["name"] == "Test Student"

        # Edit
        mgr2.update_student("S001", "Updated Name", 90.0, subjects)
        mgr3 = StudentManager(FileHandler.load(tmp_json), tmp_json)
        assert mgr3.get_student_by_id("S001")["name"] == "Updated Name"
        assert mgr3.get_student_by_id("S001")["attendance"] == 90.0

        # Delete
        mgr3.delete_student("S001")
        mgr4 = StudentManager(FileHandler.load(tmp_json), tmp_json)
        assert mgr4.get_student_by_id("S001") is None

    def test_grade_changes_when_marks_updated(self, tmp_json):
        subjects_low = [{"subject_name": "Math", "marks_obtained": 30, "max_marks": 100}]
        subjects_high = [{"subject_name": "Math", "marks_obtained": 92, "max_marks": 100}]

        mgr = StudentManager([], tmp_json)
        mgr.add_student("S001", "Alice", 80.0, subjects_low)
        assert mgr.get_student_by_id("S001")["grade"] == "F"

        mgr.update_student("S001", "Alice", 80.0, subjects_high)
        assert mgr.get_student_by_id("S001")["grade"] == "A+"

    def test_session_state_pattern(self, tmp_json):
        """Simulate the app.py session state pattern: load → mutate → reload."""
        subjects = [{"subject_name": "Math", "marks_obtained": 60, "max_marks": 100}]

        # First "session"
        session_students = FileHandler.load(tmp_json)
        mgr = StudentManager(session_students, tmp_json)
        mgr.add_student("S001", "Alice", 80.0, subjects)

        # Simulate st.session_state refresh after save
        session_students = FileHandler.load(tmp_json)
        mgr2 = StudentManager(session_students, tmp_json)
        assert len(mgr2.get_all_students()) == 1
