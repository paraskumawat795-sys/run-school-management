"""Student Performance Dashboard — Streamlit application entry point."""

from __future__ import annotations

import sys
import os

# Ensure the project root is on the Python path so `core` and `ui` imports resolve
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from ui import add_student, delete_student, edit_student, overview, performance, statistics, view_students

# ── Page configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
PAGES = {
    "🏠 Dashboard Overview": overview,
    "➕ Add Student": add_student,
    "📋 Student Records": view_students,
    "🎯 Student Performance": performance,
    "📊 Analytics & Charts": statistics,
    "✏️ Edit Student": edit_student,
    "🗑️ Delete Student": delete_student,
}

with st.sidebar:
    st.title("🎓 Student Dashboard")
    st.caption("Student Performance Tracker")
    st.divider()
    selected_page = st.radio(
        "Navigation",
        options=list(PAGES.keys()),
        key="nav_page",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("📁 Data saved locally to `data/students.json`")

# ── Render selected page ───────────────────────────────────────────────────────
try:
    PAGES[selected_page].render()
except Exception as exc:
    st.error(f"⚠️ An unexpected error occurred on this page: {exc}")
    st.exception(exc)
