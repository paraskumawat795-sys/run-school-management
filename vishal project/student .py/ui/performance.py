"""Student Performance page — detailed view for a single student."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from core.calculator import get_performance_summary
from core.data_manager import load_all_students_as_objects


def render() -> None:
    """Render the individual Student Performance page."""
    st.header("🎯 Student Performance")

    students = load_all_students_as_objects()
    if not students:
        st.info("No students found. Add a student first.")
        return

    # ── Student selector ───────────────────────────────────────────────────
    options = {f"{s.name} ({s.student_id})": s.student_id for s in students}
    selected_label = st.selectbox(
        "Select a student",
        options=list(options.keys()),
        key="perf_selector",
    )
    student_id = options[selected_label]
    student_map = {s.student_id: s for s in students}
    student = student_map[student_id]
    summary = get_performance_summary(student)

    st.divider()

    # ── Student info banner ────────────────────────────────────────────────
    st.subheader(f"👤 {student.name}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Student ID", student.student_id)
    col2.metric("Overall %", f"{summary['percentage']}%")
    col3.metric("Grade", summary["grade"])
    col4.metric("Attendance", f"{student.attendance}%")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Obtained", f"{summary['total_obtained']}")
    col6.metric("Total Max", f"{summary['total_max']}")
    col7.metric("Subjects", summary["subjects_count"])

    # Performance and attendance status badges
    perf_status = "⚠️ Low Performance" if summary["is_low_performance"] else "✅ Good Performance"
    att_status = "⚠️ Low Attendance" if summary["is_low_attendance"] else "✅ Good Attendance"
    col8.metric("Status", perf_status.split(" ", 1)[0])

    # Colour-coded status
    status_col1, status_col2 = st.columns(2)
    if summary["is_low_performance"]:
        status_col1.error(perf_status)
    else:
        status_col1.success(perf_status)

    if summary["is_low_attendance"]:
        status_col2.error(att_status)
    else:
        status_col2.success(att_status)

    st.divider()

    # ── Subject-wise breakdown ─────────────────────────────────────────────
    st.subheader("📚 Subject-wise Marks")

    if not student.subjects:
        st.info("No subjects recorded for this student.")
        return

    subj_data = [
        {
            "Subject": s.subject_name,
            "Obtained": s.marks_obtained,
            "Max Marks": s.max_marks,
            "Percentage": s.subject_percentage(),
            "Grade": _quick_grade(s.subject_percentage()),
        }
        for s in student.subjects
    ]
    df = pd.DataFrame(subj_data)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Percentage": st.column_config.ProgressColumn(
                "Percentage",
                format="%.2f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

    # ── Subject-wise bar chart ─────────────────────────────────────────────
    st.subheader("📊 Subject Performance Chart")
    subj_names = [s.subject_name for s in student.subjects]
    subj_pcts = [s.subject_percentage() for s in student.subjects]

    fig, ax = plt.subplots(figsize=(max(5, len(subj_names) * 1.2), 4))
    bar_colors = ["#e74c3c" if p < 50 else "#3498db" for p in subj_pcts]
    bars = ax.bar(subj_names, subj_pcts, color=bar_colors, edgecolor="white", linewidth=0.5)
    ax.axhline(y=50, color="#e74c3c", linestyle="--", linewidth=1, label="Pass threshold (50%)")
    ax.set_xlabel("Subject")
    ax.set_ylabel("Percentage (%)")
    ax.set_title(f"Subject-wise Performance — {student.name}")
    ax.set_ylim(0, 115)
    ax.legend(fontsize=8)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    for bar, pct in zip(bars, subj_pcts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{pct}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _quick_grade(pct: float) -> str:
    """Return a grade label for a subject percentage (reuses the same scale)."""
    from core.calculator import assign_grade
    return assign_grade(pct)
