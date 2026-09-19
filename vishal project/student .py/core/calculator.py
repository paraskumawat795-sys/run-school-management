"""Pure business logic: marks calculation, grading, and class statistics."""

from __future__ import annotations

from typing import Any

from core.models import Student, Subject

# ── Configurable thresholds ────────────────────────────────────────────────────
LOW_ATTENDANCE_THRESHOLD: float = 75.0
LOW_PERFORMANCE_THRESHOLD: float = 50.0
DEFAULT_MAX_MARKS: float = 100.0

# ── Grade scale (min_percentage, grade_label) — evaluated top-down ─────────────
GRADE_SCALE: list[tuple[float, str]] = [
    (90.0, "A+"),
    (80.0, "A"),
    (70.0, "B"),
    (60.0, "C"),
    (50.0, "D"),
    (0.0,  "F"),
]


# ── Individual student calculations ───────────────────────────────────────────

def calculate_total_marks(subjects: list[Subject]) -> tuple[float, float]:
    """Return (total_obtained, total_max) across all subjects.

    Returns (0.0, 0.0) when the subject list is empty.
    """
    if not subjects:
        return 0.0, 0.0
    total_obtained = sum(s.marks_obtained for s in subjects)
    total_max = sum(s.max_marks for s in subjects)
    return round(total_obtained, 2), round(total_max, 2)


def calculate_percentage(obtained: float, max_marks: float) -> float:
    """Return the percentage as a float rounded to 2 decimal places.

    Returns 0.0 if max_marks is 0 to avoid ZeroDivisionError.
    """
    if max_marks == 0:
        return 0.0
    return round((obtained / max_marks) * 100, 2)


def assign_grade(percentage: float) -> str:
    """Return a letter grade string for the given percentage.

    Uses the module-level GRADE_SCALE list evaluated from highest to lowest.
    Returns 'N/A' when percentage is negative (no subjects case).
    """
    if percentage < 0:
        return "N/A"
    for min_pct, grade in GRADE_SCALE:
        if percentage >= min_pct:
            return grade
    return "F"


def get_performance_summary(student: Student) -> dict[str, Any]:
    """Return a dict of all computed performance fields for a student.

    Keys: student_id, name, attendance, subjects_count,
          total_obtained, total_max, percentage, grade,
          is_low_attendance, is_low_performance.
    """
    total_obtained, total_max = calculate_total_marks(student.subjects)

    if student.subjects:
        percentage = calculate_percentage(total_obtained, total_max)
        grade = assign_grade(percentage)
    else:
        percentage = 0.0
        grade = "N/A"

    return {
        "student_id": student.student_id,
        "name": student.name,
        "attendance": student.attendance,
        "subjects_count": len(student.subjects),
        "total_obtained": total_obtained,
        "total_max": total_max,
        "percentage": percentage,
        "grade": grade,
        "is_low_attendance": is_low_attendance(student),
        "is_low_performance": is_low_performance(student),
    }


def is_low_attendance(student: Student) -> bool:
    """Return True if the student's attendance is below LOW_ATTENDANCE_THRESHOLD."""
    return student.attendance < LOW_ATTENDANCE_THRESHOLD


def is_low_performance(student: Student) -> bool:
    """Return True if the student's overall percentage is below LOW_PERFORMANCE_THRESHOLD."""
    total_obtained, total_max = calculate_total_marks(student.subjects)
    if not student.subjects:
        return False
    pct = calculate_percentage(total_obtained, total_max)
    return pct < LOW_PERFORMANCE_THRESHOLD


# ── Class-level statistics ─────────────────────────────────────────────────────

def get_class_statistics(students: list[Student]) -> dict[str, Any]:
    """Return aggregate statistics for an entire class.

    Returns a dict with keys:
        total_students, average_percentage, highest_percentage,
        lowest_percentage, average_attendance,
        below_50_count, below_75_attendance_count,
        grade_distribution, subject_averages,
        top_scorer_name, lowest_scorer_name.
    """
    if not students:
        return {
            "total_students": 0,
            "average_percentage": 0.0,
            "highest_percentage": 0.0,
            "lowest_percentage": 0.0,
            "average_attendance": 0.0,
            "below_50_count": 0,
            "below_75_attendance_count": 0,
            "grade_distribution": {},
            "subject_averages": {},
            "top_scorer_name": "N/A",
            "lowest_scorer_name": "N/A",
        }

    summaries = [get_performance_summary(s) for s in students]
    percentages = [s["percentage"] for s in summaries]
    attendances = [s["attendance"] for s in summaries]

    avg_pct = round(sum(percentages) / len(percentages), 2)
    highest_pct = round(max(percentages), 2)
    lowest_pct = round(min(percentages), 2)
    avg_att = round(sum(attendances) / len(attendances), 2)

    below_50 = sum(1 for p in percentages if p < LOW_PERFORMANCE_THRESHOLD)
    below_75_att = sum(1 for a in attendances if a < LOW_ATTENDANCE_THRESHOLD)

    # Grade distribution
    grade_dist: dict[str, int] = {}
    for s in summaries:
        g = s["grade"]
        grade_dist[g] = grade_dist.get(g, 0) + 1

    # Subject-wise class averages: subject_name → average percentage across students who have it
    subject_totals: dict[str, list[float]] = {}
    for student in students:
        for subj in student.subjects:
            pct = subj.subject_percentage()
            subject_totals.setdefault(subj.subject_name, []).append(pct)
    subject_averages = {
        name: round(sum(values) / len(values), 2)
        for name, values in subject_totals.items()
    }

    # Top and lowest scorers
    max_idx = percentages.index(max(percentages))
    min_idx = percentages.index(min(percentages))

    return {
        "total_students": len(students),
        "average_percentage": avg_pct,
        "highest_percentage": highest_pct,
        "lowest_percentage": lowest_pct,
        "average_attendance": avg_att,
        "below_50_count": below_50,
        "below_75_attendance_count": below_75_att,
        "grade_distribution": grade_dist,
        "subject_averages": subject_averages,
        "top_scorer_name": summaries[max_idx]["name"],
        "lowest_scorer_name": summaries[min_idx]["name"],
    }
