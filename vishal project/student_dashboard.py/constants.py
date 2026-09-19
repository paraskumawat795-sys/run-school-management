"""
constants.py
------------
Application-wide constants: grade scale, thresholds, and defaults.
All other modules import from here so that configuration changes
need to be made in exactly one place.
"""

# ---------------------------------------------------------------------------
# Grade scale: list of (minimum_percentage, grade_label) in DESCENDING order.
# The first threshold whose value is <= the student's percentage wins.
# ---------------------------------------------------------------------------
GRADE_SCALE: list[tuple[float, str]] = [
    (90.0, "A+"),
    (80.0, "A"),
    (70.0, "B"),
    (60.0, "C"),
    (50.0, "D"),
    (0.0,  "F"),
]

# ---------------------------------------------------------------------------
# Performance thresholds
# ---------------------------------------------------------------------------
LOW_ATTENDANCE_THRESHOLD: float = 75.0   # attendance % below this is flagged
LOW_MARKS_THRESHOLD: float = 50.0        # overall % below this is low-performance

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_MAX_MARKS: float = 100.0         # default max marks when user leaves field blank
DATA_FILE: str = "student_dashboard/students.json"   # persistence file path
