"""Student Records page — view all students with filtering."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.calculator import get_performance_summary
from core.data_manager import load_all_students_as_objects
from core.models import Student


def _build_summary_df(students: list[Student]) -> pd.DataFrame:
    """Build a display DataFrame from student summaries."""
    rows = []
    for student in students:
        s = get_performance_summary(student)
        rows.append(
            {
                "ID": s["student_id"],
                "Name": s["name"],
                "Subjects": s["subjects_count"],
                "Obtained": s["total_obtained"],
                "Max Marks": s["total_max"],
                "Percentage": s["percentage"],
                "Grade": s["grade"],
                "Attendance %": s["attendance"],
                "⚠ Low Marks": "Yes" if s["is_low_performance"] else "",
                "⚠ Low Att.": "Yes" if s["is_low_attendance"] else "",
            }
        )
    return pd.DataFrame(rows)


def render() -> None:
    """Render the Student Records page with filters."""
    st.header("📋 Student Records")

    students = load_all_students_as_objects()

    if not students:
        st.info("No students found. Use **Add Student** to add your first record.")
        return

    # ── Filter controls ────────────────────────────────────────────────────
    st.subheader("🔍 Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        # Collect all unique subject names
        all_subjects = sorted(
            {s.subject_name for student in students for s in student.subjects}
        )
        subject_filter = st.selectbox(
            "Filter by Subject",
            options=["All"] + all_subjects,
            key="vw_subject_filter",
        )

    with filter_col2:
        low_marks_filter = st.checkbox("Show only Low Marks (< 50%)", key="vw_low_marks")

    with filter_col3:
        low_att_filter = st.checkbox("Show only Low Attendance (< 75%)", key="vw_low_att")

    grade_options = ["All", "A+", "A", "B", "C", "D", "F", "N/A"]
    grade_filter = st.selectbox("Filter by Grade", options=grade_options, key="vw_grade")

    # ── Apply filters ──────────────────────────────────────────────────────
    filtered = students

    if subject_filter != "All":
        filtered = [
            s for s in filtered
            if any(sub.subject_name == subject_filter for sub in s.subjects)
        ]

    if low_marks_filter:
        filtered = [
            s for s in filtered
            if get_performance_summary(s)["is_low_performance"]
        ]

    if low_att_filter:
        filtered = [s for s in filtered if s.attendance < 75.0]

    if grade_filter != "All":
        filtered = [
            s for s in filtered
            if get_performance_summary(s)["grade"] == grade_filter
        ]

    st.caption(f"Showing **{len(filtered)}** of **{len(students)}** students")

    if not filtered:
        st.warning("No students match the selected filters.")
        return

    # ── Summary table ──────────────────────────────────────────────────────
    df = _build_summary_df(filtered)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Percentage": st.column_config.ProgressColumn(
                "Percentage",
                format="%.2f%%",
                min_value=0,
                max_value=100,
            ),
            "Attendance %": st.column_config.ProgressColumn(
                "Attendance %",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

    # ── Individual student detail expanders ────────────────────────────────
    st.subheader("📖 Student Details")
    for student in filtered:
        summary = get_performance_summary(student)
        label = (
            f"{student.name} ({student.student_id}) — "
            f"{summary['percentage']}% | Grade: {summary['grade']}"
        )
        with st.expander(label):
            info_col, marks_col = st.columns(2)
            with info_col:
                st.write(f"**Name:** {student.name}")
                st.write(f"**ID:** {student.student_id}")
                st.write(f"**Attendance:** {student.attendance}%")
                att_status = "⚠️ Low" if summary["is_low_attendance"] else "✅ OK"
                st.write(f"**Attendance Status:** {att_status}")

            with marks_col:
                st.write(f"**Total Obtained:** {summary['total_obtained']} / {summary['total_max']}")
                st.write(f"**Overall Percentage:** {summary['percentage']}%")
                st.write(f"**Grade:** {summary['grade']}")
                perf_status = "⚠️ Low Performance" if summary["is_low_performance"] else "✅ Good"
                st.write(f"**Performance Status:** {perf_status}")

            if student.subjects:
                st.write("**Subject-wise Marks:**")
                subj_data = [
                    {
                        "Subject": s.subject_name,
                        "Obtained": s.marks_obtained,
                        "Max": s.max_marks,
                        "Percentage": f"{s.subject_percentage()}%",
                    }
                    for s in student.subjects
                ]
                st.dataframe(pd.DataFrame(subj_data), hide_index=True, use_container_width=True)
            else:
                st.write("*No subjects recorded.*")
