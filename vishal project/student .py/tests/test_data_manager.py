"""Unit tests for core/data_manager.py and core/models.py."""

from __future__ import annotations

import json
import os
import pytest

from core.models import Student, Subject


# ── Subject model ──────────────────────────────────────────────────────────────

class TestSubjectModel:
    def test_creation(self):
        s = Subject("Math", 80, 100)
        assert s.subject_name == "Math"
        assert s.marks_obtained == 80
        assert s.max_marks == 100

    def test_default_max_marks(self):
        s = Subject("Math", 80)
        assert s.max_marks == 100.0

    def test_subject_percentage_normal(self):
        s = Subject("Math", 75, 100)
        assert s.subject_percentage() == 75.0

    def test_subject_percentage_zero_max(self):
        s = Subject("Math", 50, 0)
        assert s.subject_percentage() == 0.0

    def test_to_dict(self):
        s = Subject("Math", 80, 100)
        d = s.to_dict()
        assert d == {"subject_name": "Math", "marks_obtained": 80, "max_marks": 100}

    def test_from_dict(self):
        d = {"subject_name": "Math", "marks_obtained": 80, "max_marks": 100}
        s = Subject.from_dict(d)
        assert s.subject_name == "Math"
        assert s.marks_obtained == 80.0
        assert s.max_marks == 100.0

    def test_roundtrip(self):
        original = Subject("Science", 65.5, 80)
        restored = Subject.from_dict(original.to_dict())
        assert original == restored


# ── Student model ──────────────────────────────────────────────────────────────

class TestStudentModel:
    def _make_student(self) -> Student:
        return Student(
            student_id="S001",
            name="Alice",
            attendance=80.0,
            subjects=[Subject("Math", 80, 100)],
        )

    def test_creation(self):
        s = self._make_student()
        assert s.student_id == "S001"
        assert s.name == "Alice"
        assert s.attendance == 80.0
        assert len(s.subjects) == 1

    def test_default_empty_subjects(self):
        s = Student("S001", "Alice", 80.0)
        assert s.subjects == []

    def test_add_subject(self):
        s = Student("S001", "Alice", 80.0)
        s.add_subject(Subject("Math", 80, 100))
        assert len(s.subjects) == 1

    def test_remove_subject_existing(self):
        s = self._make_student()
        result = s.remove_subject("Math")
        assert result is True
        assert len(s.subjects) == 0

    def test_remove_subject_nonexistent(self):
        s = self._make_student()
        result = s.remove_subject("Physics")
        assert result is False
        assert len(s.subjects) == 1

    def test_get_subject_names(self):
        s = self._make_student()
        s.add_subject(Subject("Science", 70, 100))
        assert s.get_subject_names() == ["Math", "Science"]

    def test_to_dict(self):
        s = self._make_student()
        d = s.to_dict()
        assert d["student_id"] == "S001"
        assert d["name"] == "Alice"
        assert d["attendance"] == 80.0
        assert len(d["subjects"]) == 1

    def test_from_dict(self):
        d = {
            "student_id": "S001",
            "name": "Alice",
            "attendance": 80.0,
            "subjects": [{"subject_name": "Math", "marks_obtained": 80, "max_marks": 100}],
        }
        s = Student.from_dict(d)
        assert s.student_id == "S001"
        assert len(s.subjects) == 1

    def test_roundtrip(self):
        original = self._make_student()
        restored = Student.from_dict(original.to_dict())
        assert original.student_id == restored.student_id
        assert original.name == restored.name
        assert original.attendance == restored.attendance

    def test_equality_by_id(self):
        s1 = Student("S001", "Alice", 80.0)
        s2 = Student("S001", "Bob", 70.0)
        assert s1 == s2

    def test_inequality(self):
        s1 = Student("S001", "Alice", 80.0)
        s2 = Student("S002", "Alice", 80.0)
        assert s1 != s2


# ── data_manager ───────────────────────────────────────────────────────────────

@pytest.fixture
def patch_data_file(tmp_path, monkeypatch):
    """Redirect data_manager to use a temporary file for each test."""
    import core.data_manager as dm
    tmp_file = str(tmp_path / "students.json")
    monkeypatch.setattr(dm, "DATA_FILE", tmp_file)
    monkeypatch.setattr(dm, "_DATA_DIR", str(tmp_path))
    return tmp_file


def _make_student(sid: str = "S001", name: str = "Alice", att: float = 80.0) -> Student:
    return Student(
        student_id=sid,
        name=name,
        attendance=att,
        subjects=[Subject("Math", 80, 100)],
    )


class TestDataManager:
    def test_load_students_missing_file_returns_empty(self, patch_data_file):
        from core.data_manager import load_students
        assert load_students() == []

    def test_save_and_load_roundtrip(self, patch_data_file):
        from core.data_manager import add_student, load_students
        student = _make_student()
        add_student(student)
        records = load_students()
        assert len(records) == 1
        assert records[0]["student_id"] == "S001"

    def test_add_student(self, patch_data_file):
        from core.data_manager import add_student, load_students
        add_student(_make_student("S001", "Alice"))
        add_student(_make_student("S002", "Bob"))
        assert len(load_students()) == 2

    def test_add_duplicate_raises_value_error(self, patch_data_file):
        from core.data_manager import add_student
        add_student(_make_student())
        with pytest.raises(ValueError):
            add_student(_make_student())

    def test_get_student_by_id_found(self, patch_data_file):
        from core.data_manager import add_student, get_student_by_id
        add_student(_make_student("S001", "Alice"))
        record = get_student_by_id("S001")
        assert record is not None
        assert record["name"] == "Alice"

    def test_get_student_by_id_not_found(self, patch_data_file):
        from core.data_manager import get_student_by_id
        assert get_student_by_id("NONE") is None

    def test_update_student(self, patch_data_file):
        from core.data_manager import add_student, get_student_by_id, update_student
        add_student(_make_student("S001", "Alice"))
        updated = Student("S001", "Alice Updated", 90.0, [Subject("Math", 95, 100)])
        result = update_student("S001", updated)
        assert result is True
        record = get_student_by_id("S001")
        assert record["name"] == "Alice Updated"
        assert record["attendance"] == 90.0

    def test_update_nonexistent_returns_false(self, patch_data_file):
        from core.data_manager import update_student
        result = update_student("NONE", _make_student())
        assert result is False

    def test_delete_student(self, patch_data_file):
        from core.data_manager import add_student, delete_student, load_students
        add_student(_make_student("S001"))
        result = delete_student("S001")
        assert result is True
        assert load_students() == []

    def test_delete_nonexistent_returns_false(self, patch_data_file):
        from core.data_manager import delete_student
        result = delete_student("NONE")
        assert result is False

    def test_student_id_exists_true(self, patch_data_file):
        from core.data_manager import add_student, student_id_exists
        add_student(_make_student())
        assert student_id_exists("S001") is True

    def test_student_id_exists_false(self, patch_data_file):
        from core.data_manager import student_id_exists
        assert student_id_exists("NONE") is False

    def test_load_malformed_json_returns_empty(self, patch_data_file):
        from core.data_manager import load_students
        with open(patch_data_file, "w") as f:
            f.write("this is not json {{{")
        assert load_students() == []

    def test_load_all_students_as_objects(self, patch_data_file):
        from core.data_manager import add_student, load_all_students_as_objects
        add_student(_make_student("S001", "Alice"))
        students = load_all_students_as_objects()
        assert len(students) == 1
        assert isinstance(students[0], Student)
        assert students[0].student_id == "S001"
