"""Edit Student page — pre-populated form for updating student records."""

from __future__ import annotations

import streamlit as st

from core.data_manager import load_all_students_as_objects, update_student
from core.models import Student, Subject
from core.validator import validate_attendance, validate_marks, validate_name, validate_subject_name


def render() -> None:
    """Render the Edit Student page."""
    st.header("✏️ Edit Student")

    students = load_all_students_as_objects()
    if not students:
        st.info("No students found. Add a student first.")
        return

    # ── Student selector ───────────────────────────────────────────────────
    options = {f"{s.name} ({s.student_id})": s.student_id for s in students}
    selected_label = st.selectbox(
        "Select a student to edit",
        options=list(options.keys()),
        key="edit_selector",
    )
    student_id = options[selected_label]

    # Look up the selected student
    student_map = {s.student_id: s for s in students}
    student = student_map[student_id]

    # ── Subject row count for this student ─────────────────────────────────
    row_key = f"edit_rows_{student_id}"
    if row_key not in st.session_state:
        st.session_state[row_key] = max(len(student.subjects), 1)

    st.divider()

    # ── Student info (ID is read-only) ─────────────────────────────────────
    st.write(f"**Student ID:** `{student.student_id}` *(cannot be changed)*")

    name = st.text_input(
        "Student Name *",
        value=student.name,
        key=f"edit_name_{student_id}",
    )
    attendance = st.number_input(
        "Attendance Percentage *",
        min_value=0.0,
        max_value=100.0,
        value=float(student.attendance),
        step=0.5,
        format="%.1f",
        key=f"edit_att_{student_id}",
    )

    # ── Subject rows ───────────────────────────────────────────────────────
    st.subheader("📚 Subjects")

    num_rows = st.session_state[row_key]
    subject_rows: list[dict] = []

    for i in range(num_rows):
        existing = student.subjects[i] if i < len(student.subjects) else None
        cols = st.columns([3, 2, 2])
        with cols[0]:
            sname = st.text_input(
                f"Subject Name {i + 1}",
                value=existing.subject_name if existing else "",
                key=f"edit_sname_{student_id}_{i}",
            )
        with cols[1]:
            obtained = st.number_input(
                f"Marks Obtained {i + 1}",
                min_value=0.0,
                max_value=9999.0,
                value=float(existing.marks_obtained) if existing else 0.0,
                step=0.5,
                format="%.1f",
                key=f"edit_obt_{student_id}_{i}",
            )
        with cols[2]:
            maximum = st.number_input(
                f"Max Marks {i + 1}",
                min_value=1.0,
                max_value=9999.0,
                value=float(existing.max_marks) if existing else 100.0,
                step=1.0,
                format="%.1f",
                key=f"edit_max_{student_id}_{i}",
            )
        subject_rows.append(
            {"subject_name": sname, "marks_obtained": obtained, "max_marks": maximum}
        )

    # ── Add / Remove subject row controls ─────────────────────────────────
    btn_col1, btn_col2 = st.columns([1, 5])
    with btn_col1:
        if st.button("＋ Add Subject", key=f"edit_add_subj_{student_id}"):
            st.session_state[row_key] += 1
            st.rerun()
    with btn_col2:
        if num_rows > 1:
            if st.button("－ Remove Last Subject", key=f"edit_rm_subj_{student_id}"):
                st.session_state[row_key] -= 1
                st.rerun()

    st.divider()

    # ── Update button ──────────────────────────────────────────────────────
    if st.button("💾 Update Student", type="primary", key=f"update_btn_{student_id}"):
        errors: list[str] = []

        name_err = validate_name(name)
        if name_err:
            errors.append(name_err)

        att_err = validate_attendance(attendance)
        if att_err:
            errors.append(att_err)

        filled_subjects = [s for s in subject_rows if s["subject_name"].strip()]
        if not filled_subjects:
            errors.append("Please add at least one subject with a name.")

        seen: list[str] = []
        for i, subj in enumerate(filled_subjects, start=1):
            sn = str(subj["subject_name"]).strip()
            sn_err = validate_subject_name(sn, seen)
            if sn_err:
                errors.append(f"Subject {i}: {sn_err}")
            else:
                seen.append(sn)
            mk_err = validate_marks(subj["marks_obtained"], subj["max_marks"])
            if mk_err:
                errors.append(f"Subject {i} ({sn}): {mk_err}")

        if errors:
            for err in errors:
                st.error(err)
        else:
            new_subjects = [
                Subject(
                    subject_name=s["subject_name"].strip(),
                    marks_obtained=float(s["marks_obtained"]),
                    max_marks=float(s["max_marks"]),
                )
                for s in filled_subjects
            ]
            updated = Student(
                student_id=student.student_id,
                name=name.strip(),
                attendance=float(attendance),
                subjects=new_subjects,
            )
            result = update_student(student.student_id, updated)
            if result:
                st.success(f"✅ Student **{name.strip()}** updated successfully!")
                # Clear row count so it refreshes from the new data next visit
                del st.session_state[row_key]
                st.rerun()
            else:
                st.error("Update failed — student not found.")
