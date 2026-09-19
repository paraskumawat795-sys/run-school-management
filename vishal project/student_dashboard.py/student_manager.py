"""
student_manager.py
------------------
Core CRUD and query layer.

StudentManager holds the in-memory student list, performs all mutations,
delegates calculations to GradeCalculator, and delegates persistence to
FileHandler.

Raw dicts stored in self._students are NEVER modified directly — mutations
always rebuild the list so that session_state copies stay consistent.
"""

from copy import deepcopy
from grade_calculator import GradeCalculator
from file_handler import FileHandler
from constants import (
    DATA_FILE,
    LOW_ATTENDANCE_THRESHOLD,
    LOW_MARKS_THRESHOLD,
)


class StudentManager:
    """Manages the in-memory student list with full CRUD and query support."""

    def __init__(self, students: list[dict], filepath: str = DATA_FILE) -> None:
        """
        Parameters
        ----------
        students : list of raw student dicts (as loaded from JSON)
        filepath : path to the JSON persistence file
        """
        self._students: list[dict] = deepcopy(students)
        self._filepath: str = filepath

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enrich(self, student: dict) -> dict:
        """
        Return a COPY of *student* with computed fields added:
          - total_obtained  (float)
          - total_max       (float)
          - overall_percentage (float)
          - grade           (str)
          - is_low_attendance (bool)
          - is_low_performer  (bool)
        """
        s = deepcopy(student)
        subjects = s.get("subjects", [])
        obtained, maximum = GradeCalculator.calculate_totals(subjects)
        pct = GradeCalculator.calculate_percentage(obtained, maximum)
        s["total_obtained"] = obtained
        s["total_max"] = maximum
        s["overall_percentage"] = pct
        s["grade"] = GradeCalculator.calculate_grade(pct)
        s["is_low_attendance"] = float(s.get("attendance", 0)) < LOW_ATTENDANCE_THRESHOLD
        s["is_low_performer"] = pct < LOW_MARKS_THRESHOLD
        return s

    def _save(self) -> None:
        """Persist the current in-memory list to disk."""
        FileHandler.save(self._students, self._filepath)

    def _index_of(self, student_id: str) -> int | None:
        """Return the list index of a student by ID (case-insensitive), or None."""
        sid_upper = student_id.strip().upper()
        for i, s in enumerate(self._students):
            if s.get("student_id", "").upper() == sid_upper:
                return i
        return None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_student(
        self,
        student_id: str,
        name: str,
        attendance: float,
        subjects: list[dict],
    ) -> None:
        """
        Append a new student record and save.

        Caller is responsible for validating inputs before calling this method.
        """
        record: dict = {
            "student_id": student_id.strip(),
            "name": name.strip(),
            "attendance": float(attendance),
            "subjects": deepcopy(subjects),
        }
        self._students.append(record)
        self._save()

    def update_student(
        self,
        student_id: str,
        name: str,
        attendance: float,
        subjects: list[dict],
    ) -> bool:
        """
        Replace name, attendance, and subjects for an existing student.
        Returns True if found and updated, False if student_id not found.
        """
        idx = self._index_of(student_id)
        if idx is None:
            return False
        self._students[idx]["name"] = name.strip()
        self._students[idx]["attendance"] = float(attendance)
        self._students[idx]["subjects"] = deepcopy(subjects)
        self._save()
        return True

    def delete_student(self, student_id: str) -> bool:
        """
        Remove a student by ID.
        Returns True if removed, False if not found.
        """
        idx = self._index_of(student_id)
        if idx is None:
            return False
        self._students.pop(idx)
        self._save()
        return True

    # ------------------------------------------------------------------
    # Queries — all return enriched copies (never raw records)
    # ------------------------------------------------------------------

    def get_all_students(self) -> list[dict]:
        """Return all students enriched with computed performance fields."""
        return [self._enrich(s) for s in self._students]

    def get_student_by_id(self, student_id: str) -> dict | None:
        """Return one enriched student dict, or None if not found."""
        idx = self._index_of(student_id)
        if idx is None:
            return None
        return self._enrich(self._students[idx])

    def get_all_ids(self) -> list[str]:
        """Return a plain list of all student IDs (not enriched)."""
        return [s["student_id"] for s in self._students]

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def filter_by_grade(self, grade: str) -> list[dict]:
        """Return enriched students whose computed grade matches *grade*."""
        return [s for s in self.get_all_students() if s["grade"] == grade]

    def filter_by_subject(self, subject_name: str) -> list[dict]:
        """
        Return enriched students who have a subject matching *subject_name*
        (case-insensitive).
        """
        target = subject_name.strip().lower()
        result = []
        for s in self.get_all_students():
            names = [subj["subject_name"].lower() for subj in s.get("subjects", [])]
            if target in names:
                result.append(s)
        return result

    def get_low_attendance(self) -> list[dict]:
        """Return enriched students with attendance below the threshold."""
        return [s for s in self.get_all_students() if s["is_low_attendance"]]

    def get_low_performers(self) -> list[dict]:
        """Return enriched students with overall percentage below the threshold."""
        return [s for s in self.get_all_students() if s["is_low_performer"]]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> dict:
        """
        Return a summary dict for the whole class:
          class_avg        (float)  — mean of all overall percentages
          highest_pct      (float)  — highest overall percentage
          lowest_pct       (float)  — lowest overall percentage
          top_student      (str)    — name of top performer
          bottom_student   (str)    — name of lowest performer
          avg_attendance   (float)  — mean attendance
          pass_count       (int)    — students with grade != 'F'
          fail_count       (int)    — students with grade == 'F'
          low_attendance_count (int)
          low_performer_count  (int)
          total_students   (int)
        """
        students = self.get_all_students()
        total = len(students)

        if total == 0:
            return {
                "class_avg": 0.0,
                "highest_pct": 0.0,
                "lowest_pct": 0.0,
                "top_student": "—",
                "bottom_student": "—",
                "avg_attendance": 0.0,
                "pass_count": 0,
                "fail_count": 0,
                "low_attendance_count": 0,
                "low_performer_count": 0,
                "total_students": 0,
            }

        percentages = [s["overall_percentage"] for s in students]
        attendances = [s["attendance"] for s in students]

        class_avg = round(sum(percentages) / total, 2)
        highest_pct = max(percentages)
        lowest_pct = min(percentages)
        avg_attendance = round(sum(attendances) / total, 2)

        top_student = max(students, key=lambda s: s["overall_percentage"])["name"]
        bottom_student = min(students, key=lambda s: s["overall_percentage"])["name"]

        pass_count = sum(1 for s in students if s["grade"] != "F")
        fail_count = total - pass_count
        low_att_count = sum(1 for s in students if s["is_low_attendance"])
        low_perf_count = sum(1 for s in students if s["is_low_performer"])

        return {
            "class_avg": class_avg,
            "highest_pct": highest_pct,
            "lowest_pct": lowest_pct,
            "top_student": top_student,
            "bottom_student": bottom_student,
            "avg_attendance": avg_attendance,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "low_attendance_count": low_att_count,
            "low_performer_count": low_perf_count,
            "total_students": total,
        }
