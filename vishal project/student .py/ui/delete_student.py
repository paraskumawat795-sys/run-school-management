"""Delete Student page — select, preview, confirm and delete."""

from __future__ import annotations

import streamlit as st

from core.calculator import get_performance_summary
from core.data_manager import delete_student, load_all_students_as_objects


def render() -> None:
    """Render the Delete Student page."""
    st.header("🗑️ Delete Student")

    students = load_all_students_as_objects()
    if not students:
        st.info("No students found. Add a student first.")
        return

    st.warning(
        "⚠️ Deleting a student is **permanent** and cannot be undone. "
        "All subject data for the student will also be removed."
    )

    # ── Student selector ───────────────────────────────────────────────────
    options = {f"{s.name} ({s.student_id})": s.student_id for s in students}
    selected_label = st.selectbox(
        "Select the student to delete",
        options=list(options.keys()),
        key="del_selector",
    )
    student_id = options[selected_label]
    student_map = {s.student_id: s for s in students}
    student = student_map[student_id]

    # ── Student preview ────────────────────────────────────────────────────
    st.subheader("Student Preview")
    summary = get_performance_summary(student)

    col1, col2, col3 = st.columns(3)
    col1.metric("Name", student.name)
    col2.metric("Overall %", f"{summary['percentage']}%")
    col3.metric("Grade", summary["grade"])

    col4, col5, col6 = st.columns(3)
    col4.metric("Student ID", student.student_id)
    col5.metric("Attendance", f"{student.attendance}%")
    col6.metric("Subjects", summary["subjects_count"])

    # ── Confirmation ───────────────────────────────────────────────────────
    st.divider()
    confirmed = st.checkbox(
        f"I confirm I want to permanently delete **{student.name}** (ID: {student.student_id})",
        key="del_confirm",
    )

    if st.button(
        "🗑️ Delete Student",
        type="primary",
        disabled=not confirmed,
        key="del_btn",
    ):
        result = delete_student(student_id)
        if result:
            st.success(f"✅ Student **{student.name}** has been deleted.")
            # Clear the confirmation checkbox
            st.session_state["del_confirm"] = False
            st.rerun()
        else:
            st.error("Delete failed — student not found.")
