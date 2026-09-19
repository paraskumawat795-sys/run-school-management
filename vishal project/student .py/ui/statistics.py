"""Analytics / Charts page — class-level statistics and visualisations."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from core.calculator import get_class_statistics, get_performance_summary
from core.data_manager import load_all_students_as_objects


def render() -> None:
    """Render the Analytics page with charts and class statistics."""
    st.header("📊 Analytics & Charts")

    students = load_all_students_as_objects()
    if not students:
        st.info("No student data available. Add students to see analytics.")
        return

    stats = get_class_statistics(students)

    # ── Key metrics row ────────────────────────────────────────────────────
    st.subheader("📈 Class Overview")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", stats["total_students"])
    m2.metric("Class Average %", f"{stats['average_percentage']}%")
    m3.metric("Highest %", f"{stats['highest_percentage']}%")
    m4.metric("Lowest %", f"{stats['lowest_percentage']}%")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Avg Attendance", f"{stats['average_attendance']}%")
    m6.metric("Below 50% (Marks)", stats["below_50_count"])
    m7.metric("Below 75% (Att.)", stats["below_75_attendance_count"])
    m8.metric("Top Scorer", stats["top_scorer_name"])

    st.divider()

    # ── Chart 1: Student percentage comparison (bar chart) ─────────────────
    st.subheader("📉 Student Percentage Comparison")
    summaries = [get_performance_summary(s) for s in students]
    names = [s["name"] for s in summaries]
    percentages = [s["percentage"] for s in summaries]

    fig1, ax1 = plt.subplots(figsize=(max(6, len(names) * 0.8), 4))
    colors = ["#e74c3c" if p < 50 else "#3498db" for p in percentages]
    bars = ax1.bar(names, percentages, color=colors, edgecolor="white", linewidth=0.5)
    ax1.axhline(y=50, color="#e74c3c", linestyle="--", linewidth=1, label="Low performance (50%)")
    ax1.set_xlabel("Student")
    ax1.set_ylabel("Percentage (%)")
    ax1.set_title("Overall Percentage by Student")
    ax1.set_ylim(0, 110)
    ax1.legend(fontsize=8)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    for bar, pct in zip(bars, percentages):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{pct}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

    # ── Chart 2: Attendance comparison (bar chart) ──────────────────────────
    st.subheader("🗓️ Attendance Comparison")
    attendances = [s.attendance for s in students]

    fig2, ax2 = plt.subplots(figsize=(max(6, len(names) * 0.8), 4))
    att_colors = ["#e74c3c" if a < 75 else "#2ecc71" for a in attendances]
    bars2 = ax2.bar(names, attendances, color=att_colors, edgecolor="white", linewidth=0.5)
    ax2.axhline(y=75, color="#e74c3c", linestyle="--", linewidth=1, label="Low attendance (75%)")
    ax2.set_xlabel("Student")
    ax2.set_ylabel("Attendance (%)")
    ax2.set_title("Attendance Percentage by Student")
    ax2.set_ylim(0, 115)
    ax2.legend(fontsize=8)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    for bar, att in zip(bars2, attendances):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{att}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # ── Chart 3: Grade distribution (pie chart) ────────────────────────────
    st.subheader("🎓 Grade Distribution")
    grade_dist = stats["grade_distribution"]

    if grade_dist:
        grade_order = ["A+", "A", "B", "C", "D", "F", "N/A"]
        grade_colors = {
            "A+": "#27ae60", "A": "#2ecc71", "B": "#3498db",
            "C": "#f39c12", "D": "#e67e22", "F": "#e74c3c", "N/A": "#95a5a6",
        }
        labels = [g for g in grade_order if g in grade_dist]
        sizes = [grade_dist[g] for g in labels]
        pie_colors = [grade_colors.get(g, "#bdc3c7") for g in labels]

        fig3, ax3 = plt.subplots(figsize=(5, 5))
        wedges, texts, autotexts = ax3.pie(
            sizes,
            labels=labels,
            colors=pie_colors,
            autopct="%1.0f%%",
            startangle=90,
            pctdistance=0.8,
        )
        for t in autotexts:
            t.set_fontsize(9)
        ax3.set_title("Grade Distribution")
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    # ── Chart 4: Subject-wise average marks (bar chart) ────────────────────
    st.subheader("📚 Subject-wise Class Average")
    subject_avgs = stats["subject_averages"]

    if subject_avgs:
        subj_names = list(subject_avgs.keys())
        subj_avgs = list(subject_avgs.values())

        fig4, ax4 = plt.subplots(figsize=(max(5, len(subj_names) * 1.2), 4))
        ax4.bar(subj_names, subj_avgs, color="#9b59b6", edgecolor="white", linewidth=0.5)
        ax4.set_xlabel("Subject")
        ax4.set_ylabel("Average % Score")
        ax4.set_title("Class Average Score per Subject (%)")
        ax4.set_ylim(0, 115)
        for j, (sname, avg) in enumerate(zip(subj_names, subj_avgs)):
            ax4.text(j, avg + 1.5, f"{avg}%", ha="center", va="bottom", fontsize=8)
        plt.xticks(rotation=30, ha="right", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close(fig4)
    else:
        st.info("No subject data available for subject-wise chart.")

    # ── Low performance table ──────────────────────────────────────────────
    st.divider()
    st.subheader("⚠️ Students Needing Attention")

    low_marks = [s for s in students if get_performance_summary(s)["is_low_performance"]]
    low_att = [s for s in students if s.attendance < 75.0]

    tab_marks, tab_att = st.tabs(["Low Marks (< 50%)", "Low Attendance (< 75%)"])

    with tab_marks:
        if low_marks:
            rows = [
                {
                    "ID": s.student_id,
                    "Name": s.name,
                    "Percentage": get_performance_summary(s)["percentage"],
                    "Grade": get_performance_summary(s)["grade"],
                }
                for s in low_marks
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.success("No students with low marks. 🎉")

    with tab_att:
        if low_att:
            rows_att = [
                {"ID": s.student_id, "Name": s.name, "Attendance %": s.attendance}
                for s in low_att
            ]
            st.dataframe(pd.DataFrame(rows_att), hide_index=True, use_container_width=True)
        else:
            st.success("All students have satisfactory attendance. 🎉")
