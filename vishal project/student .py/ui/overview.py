"""Dashboard Overview page — high-level summary of the class."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.calculator import get_class_statistics, get_performance_summary
from core.data_manager import load_all_students_as_objects


def render() -> None:
    """Render the Dashboard Overview page."""
    st.header("🏠 Dashboard Overview")
    st.write("A quick snapshot of the entire class performance.")

    students = load_all_students_as_objects()

    if not students:
        st.info(
            "👋 Welcome! No student data yet. "
            "Use **Add Student** in the sidebar to get started."
        )
        return

    stats = get_class_statistics(students)

    # ── Row 1: Core class metrics ──────────────────────────────────────────
    st.subheader("📊 Class Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", stats["total_students"])
    c2.metric("Average %", f"{stats['average_percentage']}%")
    c3.metric("Highest %", f"{stats['highest_percentage']}%")
    c4.metric("Lowest %", f"{stats['lowest_percentage']}%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Average Attendance", f"{stats['average_attendance']}%")
    c6.metric("Top Scorer", stats["top_scorer_name"])
    c7.metric("Below 50% (Performance)", stats["below_50_count"])
    c8.metric("Below 75% (Attendance)", stats["below_75_attendance_count"])

    st.divider()

    # ── Grade distribution summary ─────────────────────────────────────────
    st.subheader("🎓 Grade Distribution")
    grade_order = ["A+", "A", "B", "C", "D", "F", "N/A"]
    grade_dist = stats["grade_distribution"]

    if grade_dist:
        grade_cols = st.columns(len(grade_dist))
        grade_color = {
            "A+": "🟢", "A": "🟢", "B": "🔵",
            "C": "🟡", "D": "🟠", "F": "🔴", "N/A": "⚪",
        }
        for col, grade in zip(grade_cols, [g for g in grade_order if g in grade_dist]):
            count = grade_dist[grade]
            col.metric(f"{grade_color.get(grade, '')} Grade {grade}", count)

    st.divider()

    # ── Recent students table ──────────────────────────────────────────────
    st.subheader("👥 All Students — Quick View")
    summaries = [get_performance_summary(s) for s in students]
    rows = [
        {
            "ID": s["student_id"],
            "Name": s["name"],
            "Percentage": s["percentage"],
            "Grade": s["grade"],
            "Attendance %": s["attendance"],
            "Status": (
                "⚠️ Low Marks"
                if s["is_low_performance"]
                else ("⚠️ Low Att." if s["is_low_attendance"] else "✅ OK")
            ),
        }
        for s in summaries
    ]
    df = pd.DataFrame(rows)
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

    # ── Alert section ──────────────────────────────────────────────────────
    low_marks_students = [s for s in students if get_performance_summary(s)["is_low_performance"]]
    low_att_students = [s for s in students if s.attendance < 75.0]

    if low_marks_students or low_att_students:
        st.divider()
        st.subheader("⚠️ Students Needing Attention")

        if low_marks_students:
            names = ", ".join(s.name for s in low_marks_students)
            st.error(f"**Low Performance (< 50%):** {names}")

        if low_att_students:
            names_att = ", ".join(s.name for s in low_att_students)
            st.warning(f"**Low Attendance (< 75%):** {names_att}")
