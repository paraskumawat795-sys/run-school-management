"""Add Student page — Streamlit UI."""

from __future__ import annotations

import streamlit as st

from core.data_manager import add_student, load_students
from core.models import Student, Subject
from core.validator import validate_student_record


def render() -> None:
    """Render the Add Student form."""
    st.header("➕ Add Student")
    st.write("Fill in the student details and add at least one subject.")

    # ── Initialise subject rows in session state ───────────────────────────
    if "add_subject_rows" not in st.session_state:
        st.session_state["add_subject_rows"] = 1

    # ── Student info ───────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input(
            "Student ID / Roll Number *",
            placeholder="e.g. S001",
            key="add_sid",
        )
    with col2:
        name = st.text_input(
            "Student Name *",
            placeholder="e.g. Alice Johnson",
            key="add_name",
        )

    attendance = st.number_input(
        "Attendance Percentage *",
        min_value=0.0,
        max_value=100.0,
        value=75.0,
        step=0.5,
        format="%.1f",
        key="add_attendance",
    )

    # ── Subject rows ───────────────────────────────────────────────────────
    st.subheader("📚 Subjects")

    subject_rows: list[dict] = []
    for i in range(st.session_state["add_subject_rows"]):
        cols = st.columns([3, 2, 2])
        with cols[0]:
            sname = st.text_input(
                f"Subject Name {i + 1}",
                placeholder="e.g. Mathematics",
                key=f"add_sname_{i}",
            )
        with cols[1]:
            obtained = st.number_input(
                f"Marks Obtained {i + 1}",
                min_value=0.0,
                max_value=9999.0,
                value=0.0,
                step=0.5,
                format="%.1f",
                key=f"add_obtained_{i}",
            )
        with cols[2]:
            maximum = st.number_input(
                f"Max Marks {i + 1}",
                min_value=1.0,
                max_value=9999.0,
                value=100.0,
                step=1.0,
                format="%.1f",
                key=f"add_max_{i}",
            )
        subject_rows.append(
            {"subject_name": sname, "marks_obtained": obtained, "max_marks": maximum}
        )

    # ── Add / Remove subject row controls ─────────────────────────────────
    btn_col1, btn_col2 = st.columns([1, 5])
    with btn_col1:
        if st.button("＋ Add Subject", key="add_more_subj"):
            st.session_state["add_subject_rows"] += 1
            st.rerun()
    with btn_col2:
        if st.session_state["add_subject_rows"] > 1:
            if st.button("－ Remove Last Subject", key="remove_subj"):
                st.session_state["add_subject_rows"] -= 1
                st.rerun()

    st.divider()

    # ── Save button ────────────────────────────────────────────────────────
    if st.button("💾 Save Student", type="primary", key="save_student_btn"):
        existing_ids = [s["student_id"] for s in load_students()]

        # Only pass non-empty subject rows to the validator
        filled_subjects = [s for s in subject_rows if s["subject_name"].strip()]

        errors = validate_student_record(
            student_id=student_id,
            name=name,
            attendance=attendance,
            subjects=filled_subjects if filled_subjects else subject_rows,
            existing_ids=existing_ids,
        )

        if not filled_subjects:
            errors.append("Please add at least one subject with a name.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            subjects = [
                Subject(
                    subject_name=s["subject_name"].strip(),
                    marks_obtained=float(s["marks_obtained"]),
                    max_marks=float(s["max_marks"]),
                )
                for s in filled_subjects
            ]
            student = Student(
                student_id=student_id.strip(),
                name=name.strip(),
                attendance=float(attendance),
                subjects=subjects,
            )
            try:
                add_student(student)
                st.success(f"✅ Student **{name.strip()}** (ID: {student_id.strip()}) added successfully!")
                # Reset form state
                st.session_state["add_subject_rows"] = 1
                for key in list(st.session_state.keys()):
                    if key.startswith("add_"):
                        del st.session_state[key]
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected error while saving: {exc}")
