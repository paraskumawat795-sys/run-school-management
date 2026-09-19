"""
grade_calculator.py
-------------------
Stateless, pure-function calculation layer.
No I/O, no Streamlit imports — fully unit-testable in isolation.
"""

from constants import GRADE_SCALE


class GradeCalculator:
    """Pure calculation helpers for student performance metrics."""

    @staticmethod
    def calculate_totals(subjects: list[dict]) -> tuple[float, float]:
        """
        Sum marks_obtained and max_marks across all subjects.

        Parameters
        ----------
        subjects : list of dicts, each with keys
                   'marks_obtained' (float) and 'max_marks' (float)

        Returns
        -------
        (total_obtained, total_max) as a tuple of floats.
        Returns (0.0, 0.0) for an empty list.
        """
        total_obtained: float = 0.0
        total_max: float = 0.0
        for subj in subjects:
            total_obtained += float(subj.get("marks_obtained", 0))
            total_max += float(subj.get("max_marks", 0))
        return total_obtained, total_max

    @staticmethod
    def calculate_percentage(obtained: float, maximum: float) -> float:
        """
        Compute percentage = (obtained / maximum) * 100.

        Returns 0.0 safely when maximum is 0 (no division by zero).
        """
        if maximum == 0:
            return 0.0
        return round((obtained / maximum) * 100, 2)

    @staticmethod
    def calculate_grade(percentage: float) -> str:
        """
        Map a percentage value to a letter grade using GRADE_SCALE.

        GRADE_SCALE is checked in descending order; the first entry
        whose threshold is <= percentage produces the grade label.

        Returns 'F' for any percentage below 50 (or 0).
        """
        for threshold, label in GRADE_SCALE:
            if percentage >= threshold:
                return label
        return "F"
