"""Data models for the Student Performance Dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Subject:
    """Represents a single subject with marks obtained and maximum marks."""

    subject_name: str
    marks_obtained: float
    max_marks: float = 100.0

    def subject_percentage(self) -> float:
        """Return the percentage for this subject. Returns 0.0 if max_marks is 0."""
        if self.max_marks == 0:
            return 0.0
        return round((self.marks_obtained / self.max_marks) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        """Serialize Subject to a plain dictionary for JSON storage."""
        return {
            "subject_name": self.subject_name,
            "marks_obtained": self.marks_obtained,
            "max_marks": self.max_marks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subject":
        """Deserialize a Subject from a plain dictionary."""
        return cls(
            subject_name=str(data["subject_name"]),
            marks_obtained=float(data["marks_obtained"]),
            max_marks=float(data["max_marks"]),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Subject):
            return False
        return (
            self.subject_name == other.subject_name
            and self.marks_obtained == other.marks_obtained
            and self.max_marks == other.max_marks
        )


@dataclass
class Student:
    """Represents a student with personal info, attendance and subject records."""

    student_id: str
    name: str
    attendance: float
    subjects: list[Subject] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize Student to a plain dictionary for JSON storage."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "attendance": self.attendance,
            "subjects": [s.to_dict() for s in self.subjects],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Student":
        """Deserialize a Student from a plain dictionary."""
        subjects = [Subject.from_dict(s) for s in data.get("subjects", [])]
        return cls(
            student_id=str(data["student_id"]),
            name=str(data["name"]),
            attendance=float(data["attendance"]),
            subjects=subjects,
        )

    def add_subject(self, subject: Subject) -> None:
        """Append a subject to this student's subject list."""
        self.subjects.append(subject)

    def remove_subject(self, subject_name: str) -> bool:
        """Remove a subject by name. Returns True if removed, False if not found."""
        original_len = len(self.subjects)
        self.subjects = [s for s in self.subjects if s.subject_name != subject_name]
        return len(self.subjects) < original_len

    def get_subject_names(self) -> list[str]:
        """Return a list of all subject names for this student."""
        return [s.subject_name for s in self.subjects]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Student):
            return False
        return self.student_id == other.student_id
