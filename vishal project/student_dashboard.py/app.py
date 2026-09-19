"""
app.py
------
Streamlit entry point — UI layer only.
All business logic lives in student_manager.py, grade_calculator.py,
validator.py, file_handler.py, and constants.py.

Run:
    streamlit run student_dashboard/app.py
"""

import sys
import os

# Allow imports from the student_dashboard package directory
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for Streamlit

from student_manager import StudentManager
from file_handler import FileHandler
from validator import Validator
from constants import DATA_FILE, DEFAULT_MAX_MARKS, LOW_ATTENDANCE_THRESHOLD, LOW_MARKS_THRESHOLD

# ---------------------------------------------------------------------------
# Page config — must be the very first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "students" not in st.session_state:
    st.session_state.students = FileHandler.load(DATA_FILE)

# Instantiate manager fresh on every render from session state
manager = StudentManager(st.session_state.students, DATA_FILE)


# ---------------------------------------------------------------------------
# Helper — sync session state after any mutation
# ---------------------------------------------------------------------------
def _sync() -> None:
    """Pull the updated list back into session state and rerun."""
    st.session_state.students = FileHandler.load(DATA_FILE)
    st.rerun()


# ===========================================================================
# TAB 1 — Dashboard Overview
# ===========================================================================
def render_overview_tab(mgr: StudentManager) -> None:
    st.header("📊 Dashboard Overview")

    stats = mgr.get_statistics()

    if stats["total_students"] == 0:
        st.info("No students yet. Add students using the **Add Student** tab.")
        return

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", stats["total_students"])
    col2.metric("Class Average %", f"{stats['class_avg']:.1f}%")
    col3.metric("Highest %", f"{stats['highest_pct']:.1f}%")
    col4.metric("Lowest %", f"{stats['lowest_pct']:.1f}%")

    col5, col6, col7 = st.columns(3)
    col5.metric("Avg Attendance", f"{stats['avg_attendance']:.1f}%")
    col6.metric(f"Below {int(LOW_MARKS_THRESHOLD)}% (Low Performers)", stats["low_performer_count"])
    col7.metric(f"Below {int(LOW_ATTENDANCE_THRESHOLD)}% Attendance", stats["low_attendance_count"])

    st.divider()

    # Quick summary table
    st.subheader("All Students at a Glance")
    all_students = mgr.get_all_students()

    rows = []
    for s in all_students:
        rows.append({
            "ID": s["student_id"],
            "Name": s["name"],
            "Subjects": len(s.get("subjects", [])),
            "Total Obtained": s["total_obtained"],
            "Total Max": s["total_max"],
            "Percentage": f"{s['overall_percentage']:.1f}%",
            "Grade": s["grade"],
            "Attendance": f"{s['attendance']:.1f}%",
            "⚠ Low Att.": "Yes" if s["is_low_attendance"] else "",
            "⚠ Low Marks": "Yes" if s["is_low_performer"] else "",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Alerts
    low_att = mgr.get_low_attendance()
    low_perf = mgr.get_low_performers()

    if low_att:
        with st.expander(f"⚠️ Students with Low Attendance (< {int(LOW_ATTENDANCE_THRESHOLD)}%)", expanded=False):
            for s in low_att:
                st.warning(f"**{s['name']}** (ID: {s['student_id']}) — Attendance: {s['attendance']:.1f}%")

    if low_perf:
        with st.expander(f"⚠️ Low Performing Students (< {int(LOW_MARKS_THRESHOLD)}%)", expanded=False):
            for s in low_perf:
                st.error(f"**{s['name']}** (ID: {s['student_id']}) — {s['overall_percentage']:.1f}% — Grade: {s['grade']}")


# ===========================================================================
# TAB 2 — Add Student
# ===========================================================================
def render_add_tab(mgr: StudentManager) -> None:
    st.header("➕ Add Student")

    with st.form("add_student_form", clear_on_submit=True):
        st.subheader("Student Information")
        col1, col2 = st.columns(2)
        student_id = col1.text_input("Student ID / Roll Number *", placeholder="e.g. S001")
        name = col2.text_input("Full Name *", placeholder="e.g. Alice Smith")
        attendance = st.number_input(
            "Attendance Percentage *",
            min_value=0.0, max_value=100.0, value=100.0, step=0.5,
            help="Enter overall attendance as a percentage (0–100).",
        )

        st.subheader("Subjects & Marks")
        st.caption("Enter at least one subject. Leave subject name blank to skip that row.")

        # Fixed number of subject rows in the form (dynamic add handled outside form via session_state)
        num_subjects = st.session_state.get("num_subjects_add", 3)

        subject_data: list[dict] = []
        for i in range(num_subjects):
            c1, c2, c3 = st.columns([3, 2, 2])
            sname = c1.text_input(f"Subject {i+1} Name", key=f"add_sname_{i}", placeholder="e.g. Mathematics")
            obtained = c2.number_input(
                f"Marks Obtained", key=f"add_obtained_{i}",
                min_value=0.0, value=0.0, step=1.0,
            )
            max_m = c3.number_input(
                f"Max Marks", key=f"add_max_{i}",
                min_value=1.0, value=DEFAULT_MAX_MARKS, step=1.0,
            )
            if sname.strip():
                subject_data.append({
                    "subject_name": sname.strip(),
                    "marks_obtained": obtained,
                    "max_marks": max_m,
                })

        submitted = st.form_submit_button("💾 Save Student", use_container_width=True)

    # "Add more rows" button lives outside the form
    col_btn, _ = st.columns([1, 3])
    if col_btn.button("➕ Add Subject Row"):
        st.session_state["num_subjects_add"] = st.session_state.get("num_subjects_add", 3) + 1
        st.rerun()

    if submitted:
        errors: list[str] = []

        # Validate ID
        ok, msg = Validator.validate_student_id(student_id, mgr.get_all_ids())
        if not ok:
            errors.append(msg)

        # Validate name
        ok, msg = Validator.validate_name(name)
        if not ok:
            errors.append(msg)

        # Validate attendance
        ok, msg = Validator.validate_attendance(attendance)
        if not ok:
            errors.append(msg)

        # Validate subjects
        if not subject_data:
            errors.append("Please enter at least one subject with a name.")

        seen_subjects: list[str] = []
        for subj in subject_data:
            ok, msg = Validator.validate_subject_name(subj["subject_name"], seen_subjects)
            if not ok:
                errors.append(msg)
            else:
                seen_subjects.append(subj["subject_name"])
            ok, msg = Validator.validate_marks(subj["marks_obtained"], subj["max_marks"])
            if not ok:
                errors.append(f"[{subj['subject_name']}] {msg}")

        if errors:
            for e in errors:
                st.error(e)
        else:
            mgr.add_student(student_id, name, attendance, subject_data)
            st.session_state["num_subjects_add"] = 3
            st.success(f"✅ Student **{name}** (ID: {student_id}) added successfully!")
            _sync()


# ===========================================================================
# TAB 3 — Student Records
# ===========================================================================
def render_records_tab(mgr: StudentManager) -> None:
    st.header("📋 Student Records")

    all_students = mgr.get_all_students()

    if not all_students:
        st.info("No student records yet. Add students from the **Add Student** tab.")
        return

    # Filters
    with st.expander("🔍 Filters", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        grade_filter = fc1.selectbox(
            "Filter by Grade",
            options=["All", "A+", "A", "B", "C", "D", "F"],
            key="filter_grade",
        )
        subject_filter = fc2.text_input("Filter by Subject Name", key="filter_subject", placeholder="e.g. Mathematics")
        perf_filter = fc3.selectbox(
            "Performance Status",
            options=["All", "Low Performers", "Low Attendance"],
            key="filter_perf",
        )

    # Apply filters
    filtered = all_students
    if grade_filter != "All":
        filtered = [s for s in filtered if s["grade"] == grade_filter]
    if subject_filter.strip():
        target = subject_filter.strip().lower()
        filtered = [
            s for s in filtered
            if any(subj["subject_name"].lower() == target for subj in s.get("subjects", []))
        ]
    if perf_filter == "Low Performers":
        filtered = [s for s in filtered if s["is_low_performer"]]
    elif perf_filter == "Low Attendance":
        filtered = [s for s in filtered if s["is_low_attendance"]]

    st.caption(f"Showing **{len(filtered)}** of **{len(all_students)}** students.")

    if not filtered:
        st.warning("No students match the selected filters.")
        return

    # Table
    rows = []
    for s in filtered:
        rows.append({
            "ID": s["student_id"],
            "Name": s["name"],
            "Subjects": len(s.get("subjects", [])),
            "Total Obtained": s["total_obtained"],
            "Total Max": s["total_max"],
            "Percentage": f"{s['overall_percentage']:.1f}%",
            "Grade": s["grade"],
            "Attendance": f"{s['attendance']:.1f}%",
            "Low Att.": "⚠️" if s["is_low_attendance"] else "✅",
            "Low Marks": "⚠️" if s["is_low_performer"] else "✅",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Expandable subject detail per student
    st.divider()
    st.subheader("Subject-wise Detail")
    for s in filtered:
        with st.expander(f"📖 {s['name']} ({s['student_id']})"):
            subj_rows = []
            for subj in s.get("subjects", []):
                subj_pct = (subj["marks_obtained"] / subj["max_marks"] * 100) if subj["max_marks"] > 0 else 0.0
                subj_rows.append({
                    "Subject": subj["subject_name"],
                    "Obtained": subj["marks_obtained"],
                    "Max": subj["max_marks"],
                    "Percentage": f"{subj_pct:.1f}%",
                })
            st.dataframe(subj_rows, use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 4 — Student Performance (individual view)
# ===========================================================================
def render_performance_tab(mgr: StudentManager) -> None:
    st.header("🎯 Student Performance")

    all_students = mgr.get_all_students()

    if not all_students:
        st.info("No student records yet.")
        return

    options = {f"{s['student_id']} — {s['name']}": s["student_id"] for s in all_students}
    selected_label = st.selectbox("Select a Student", list(options.keys()), key="perf_select")
    selected_id = options[selected_label]
    s = mgr.get_student_by_id(selected_id)

    if s is None:
        st.error("Student not found.")
        return

    st.divider()

    # Student info cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Student ID", s["student_id"])
    col2.metric("Name", s["name"])
    col3.metric("Grade", s["grade"])
    col4.metric("Attendance", f"{s['attendance']:.1f}%")

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Obtained", f"{s['total_obtained']:.0f}")
    col6.metric("Total Max", f"{s['total_max']:.0f}")
    col7.metric("Overall Percentage", f"{s['overall_percentage']:.1f}%")

    # Performance status badges
    status_col1, status_col2 = st.columns(2)
    if s["is_low_attendance"]:
        status_col1.warning(f"⚠️ Low Attendance (< {int(LOW_ATTENDANCE_THRESHOLD)}%)")
    else:
        status_col1.success(f"✅ Attendance OK (≥ {int(LOW_ATTENDANCE_THRESHOLD)}%)")

    if s["is_low_performer"]:
        status_col2.error(f"⚠️ Low Performer (< {int(LOW_MARKS_THRESHOLD)}%)")
    else:
        status_col2.success(f"✅ Performing Well (≥ {int(LOW_MARKS_THRESHOLD)}%)")

    st.divider()

    # Subject-wise marks table + bar chart
    subjects = s.get("subjects", [])
    if subjects:
        st.subheader("Subject-wise Marks")

        subj_rows = []
        for subj in subjects:
            subj_pct = (subj["marks_obtained"] / subj["max_marks"] * 100) if subj["max_marks"] > 0 else 0.0
            subj_rows.append({
                "Subject": subj["subject_name"],
                "Obtained": subj["marks_obtained"],
                "Max": subj["max_marks"],
                "Percentage": f"{subj_pct:.1f}%",
                "Grade": GradeCalculator_for_display(subj_pct),
            })
        st.dataframe(subj_rows, use_container_width=True, hide_index=True)

        # Bar chart: marks obtained vs max marks per subject
        fig, ax = plt.subplots(figsize=(8, 4))
        subject_names = [subj["subject_name"] for subj in subjects]
        obtained_vals = [subj["marks_obtained"] for subj in subjects]
        max_vals = [subj["max_marks"] for subj in subjects]

        x = range(len(subject_names))
        width = 0.35
        bars1 = ax.bar([xi - width/2 for xi in x], obtained_vals, width, label="Obtained", color="#4A90D9")
        bars2 = ax.bar([xi + width/2 for xi in x], max_vals, width, label="Max Marks", color="#E8E8E8", edgecolor="#999")

        ax.set_xlabel("Subject")
        ax.set_ylabel("Marks")
        ax.set_title(f"Subject-wise Marks — {s['name']}")
        ax.set_xticks(list(x))
        ax.set_xticklabels(subject_names, rotation=15, ha="right")
        ax.legend()
        ax.set_ylim(0, max(max_vals) * 1.15)

        # Value labels on bars
        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{bar.get_height():.0f}", ha="center", va="bottom", fontsize=9)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No subjects recorded for this student.")


def GradeCalculator_for_display(pct: float) -> str:
    """Thin wrapper so the performance tab can call grade logic inline."""
    from grade_calculator import GradeCalculator
    return GradeCalculator.calculate_grade(pct)


# ===========================================================================
# TAB 5 — Edit / Delete
# ===========================================================================
def render_edit_tab(mgr: StudentManager) -> None:
    st.header("✏️ Edit / Delete Student")

    all_students = mgr.get_all_students()

    if not all_students:
        st.info("No student records to edit. Add students first.")
        return

    options = {f"{s['student_id']} — {s['name']}": s["student_id"] for s in all_students}
    selected_label = st.selectbox("Select Student to Edit", list(options.keys()), key="edit_select")
    selected_id = options[selected_label]
    current = mgr.get_student_by_id(selected_id)

    if current is None:
        st.error("Student not found.")
        return

    st.divider()
    st.subheader(f"Editing: {current['name']} (ID: {current['student_id']})")
    st.caption("Student ID cannot be changed — it is the unique identifier.")

    with st.form("edit_student_form"):
        col1, col2 = st.columns(2)
        col1.text_input("Student ID (read-only)", value=current["student_id"], disabled=True)
        new_name = col2.text_input("Full Name *", value=current["name"])
        new_attendance = st.number_input(
            "Attendance Percentage *",
            min_value=0.0, max_value=100.0,
            value=float(current["attendance"]), step=0.5,
        )

        st.subheader("Subjects & Marks")
        existing_subjects = current.get("subjects", [])
        num_rows = st.session_state.get(f"num_subjects_edit_{selected_id}", len(existing_subjects) or 1)

        new_subjects: list[dict] = []
        for i in range(num_rows):
            pre = existing_subjects[i] if i < len(existing_subjects) else {}
            c1, c2, c3 = st.columns([3, 2, 2])
            sname = c1.text_input(
                f"Subject {i+1}", key=f"edit_sname_{i}",
                value=pre.get("subject_name", ""),
            )
            obtained = c2.number_input(
                "Obtained", key=f"edit_obt_{i}",
                min_value=0.0,
                value=float(pre.get("marks_obtained", 0)),
                step=1.0,
            )
            max_m = c3.number_input(
                "Max", key=f"edit_max_{i}",
                min_value=1.0,
                value=float(pre.get("max_marks", DEFAULT_MAX_MARKS)),
                step=1.0,
            )
            if sname.strip():
                new_subjects.append({
                    "subject_name": sname.strip(),
                    "marks_obtained": obtained,
                    "max_marks": max_m,
                })

        save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)

    # Add row button outside form
    if st.button("➕ Add Subject Row", key="edit_add_row"):
        st.session_state[f"num_subjects_edit_{selected_id}"] = num_rows + 1
        st.rerun()

    if save_btn:
        errors: list[str] = []

        ok, msg = Validator.validate_name(new_name)
        if not ok:
            errors.append(msg)

        ok, msg = Validator.validate_attendance(new_attendance)
        if not ok:
            errors.append(msg)

        if not new_subjects:
            errors.append("Please enter at least one subject.")

        seen_subjects: list[str] = []
        for subj in new_subjects:
            ok, msg = Validator.validate_subject_name(subj["subject_name"], seen_subjects)
            if not ok:
                errors.append(msg)
            else:
                seen_subjects.append(subj["subject_name"])
            ok, msg = Validator.validate_marks(subj["marks_obtained"], subj["max_marks"])
            if not ok:
                errors.append(f"[{subj['subject_name']}] {msg}")

        if errors:
            for e in errors:
                st.error(e)
        else:
            mgr.update_student(selected_id, new_name, new_attendance, new_subjects)
            st.success(f"✅ Student **{new_name}** updated successfully!")
            _sync()

    # ---- Delete section ----
    st.divider()
    st.subheader("🗑️ Delete Student")
    confirm_delete = st.checkbox(
        f"I confirm I want to permanently delete **{current['name']}** (ID: {current['student_id']})",
        key="confirm_delete",
    )
    if st.button("🗑️ Delete Student", disabled=not confirm_delete, type="primary"):
        mgr.delete_student(selected_id)
        st.success(f"🗑️ Student **{current['name']}** deleted.")
        _sync()


# ===========================================================================
# TAB 6 — Analytics / Charts
# ===========================================================================
def render_analytics_tab(mgr: StudentManager) -> None:
    st.header("📈 Analytics & Charts")

    all_students = mgr.get_all_students()

    if not all_students:
        st.info("Add students to see analytics.")
        return

    # ---- Chart 1: Student percentage comparison ----
    st.subheader("Student Percentage Comparison")
    names = [s["name"] for s in all_students]
    percentages = [s["overall_percentage"] for s in all_students]

    fig1, ax1 = plt.subplots(figsize=(max(6, len(names) * 0.8), 5))
    colors = ["#d9534f" if p < LOW_MARKS_THRESHOLD else "#5cb85c" for p in percentages]
    bars = ax1.bar(names, percentages, color=colors, edgecolor="white")
    ax1.axhline(LOW_MARKS_THRESHOLD, color="#d9534f", linestyle="--", linewidth=1.2, label=f"Low Performer Threshold ({int(LOW_MARKS_THRESHOLD)}%)")
    ax1.set_ylabel("Overall Percentage (%)")
    ax1.set_title("Overall Percentage — All Students")
    ax1.set_ylim(0, 110)
    ax1.legend()
    plt.xticks(rotation=20, ha="right")
    for bar in bars:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

    # ---- Chart 2: Attendance comparison ----
    st.subheader("Attendance Comparison")
    attendances = [s["attendance"] for s in all_students]

    fig2, ax2 = plt.subplots(figsize=(max(6, len(names) * 0.8), 5))
    att_colors = ["#d9534f" if a < LOW_ATTENDANCE_THRESHOLD else "#5bc0de" for a in attendances]
    bars2 = ax2.bar(names, attendances, color=att_colors, edgecolor="white")
    ax2.axhline(LOW_ATTENDANCE_THRESHOLD, color="#d9534f", linestyle="--", linewidth=1.2,
                label=f"Low Attendance Threshold ({int(LOW_ATTENDANCE_THRESHOLD)}%)")
    ax2.set_ylabel("Attendance (%)")
    ax2.set_title("Attendance — All Students")
    ax2.set_ylim(0, 110)
    ax2.legend()
    plt.xticks(rotation=20, ha="right")
    for bar in bars2:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # ---- Chart 3: Grade distribution ----
    st.subheader("Grade Distribution")
    grade_labels = ["A+", "A", "B", "C", "D", "F"]
    grade_counts = {g: 0 for g in grade_labels}
    for s in all_students:
        g = s["grade"]
        if g in grade_counts:
            grade_counts[g] += 1

    # Only show grades that have at least one student
    present_grades = [(g, grade_counts[g]) for g in grade_labels if grade_counts[g] > 0]

    if present_grades:
        g_labels, g_counts = zip(*present_grades)
        grade_colors = {
            "A+": "#2ecc71", "A": "#27ae60", "B": "#3498db",
            "C": "#f39c12", "D": "#e67e22", "F": "#e74c3c",
        }
        pie_colors = [grade_colors.get(g, "#95a5a6") for g in g_labels]

        col_pie, col_bar = st.columns(2)

        with col_pie:
            fig3, ax3 = plt.subplots(figsize=(5, 5))
            ax3.pie(
                g_counts, labels=g_labels, autopct="%1.0f%%",
                colors=pie_colors, startangle=140,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            )
            ax3.set_title("Grade Distribution (Pie)")
            st.pyplot(fig3)
            plt.close(fig3)

        with col_bar:
            fig4, ax4 = plt.subplots(figsize=(5, 5))
            ax4.bar(g_labels, g_counts, color=pie_colors, edgecolor="white")
            ax4.set_xlabel("Grade")
            ax4.set_ylabel("Number of Students")
            ax4.set_title("Grade Distribution (Bar)")
            for i, cnt in enumerate(g_counts):
                ax4.text(i, cnt + 0.1, str(cnt), ha="center", va="bottom", fontsize=10)
            plt.tight_layout()
            st.pyplot(fig4)
            plt.close(fig4)

    # ---- Chart 4: Subject-wise average marks ----
    st.subheader("Subject-wise Average Marks (Class)")

    subject_totals: dict[str, list[float]] = {}
    subject_max: dict[str, float] = {}

    for s in all_students:
        for subj in s.get("subjects", []):
            sn = subj["subject_name"]
            if sn not in subject_totals:
                subject_totals[sn] = []
                subject_max[sn] = subj["max_marks"]
            subject_totals[sn].append(subj["marks_obtained"])

    if subject_totals:
        subject_names_list = list(subject_totals.keys())
        avg_obtained = [sum(vals) / len(vals) for vals in subject_totals.values()]
        max_marks_list = [subject_max[sn] for sn in subject_names_list]

        fig5, ax5 = plt.subplots(figsize=(max(6, len(subject_names_list) * 1.2), 5))
        x = range(len(subject_names_list))
        width = 0.35
        ax5.bar([xi - width/2 for xi in x], avg_obtained, width, label="Avg Obtained", color="#4A90D9")
        ax5.bar([xi + width/2 for xi in x], max_marks_list, width, label="Max Marks", color="#E8E8E8", edgecolor="#999")
        ax5.set_xticks(list(x))
        ax5.set_xticklabels(subject_names_list, rotation=15, ha="right")
        ax5.set_ylabel("Marks")
        ax5.set_title("Subject-wise Average Marks Across All Students")
        ax5.legend()
        plt.tight_layout()
        st.pyplot(fig5)
        plt.close(fig5)
    else:
        st.info("No subject data available for chart.")


# ===========================================================================
# Main app — tab navigation
# ===========================================================================
def main() -> None:
    st.title("🎓 Student Performance Dashboard")
    st.caption("A beginner-friendly dashboard for tracking student marks, grades, and attendance.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "➕ Add Student",
        "📋 Student Records",
        "🎯 Performance",
        "📈 Analytics",
    ])

    with tab1:
        render_overview_tab(manager)
    with tab2:
        render_add_tab(manager)
    with tab3:
        render_records_tab(manager)
    with tab4:
        render_performance_tab(manager)
    with tab5:
        render_analytics_tab(manager)

    # Edit tab is hidden in a sidebar expander to keep main nav clean
    with st.sidebar:
        st.markdown("### 🎓 Student Dashboard")
        st.divider()
        st.markdown("**Navigation**")
        st.markdown("Use the tabs above to navigate sections.")
        st.divider()
        with st.expander("✏️ Edit / Delete a Student"):
            render_edit_tab(manager)


if __name__ == "__main__":
    main()
