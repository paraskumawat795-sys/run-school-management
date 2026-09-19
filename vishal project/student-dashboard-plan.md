# Student Performance Dashboard — Implementation Plan

## Top-Level Overview

**Goal:** Build a beginner-friendly, single-user Student Performance Dashboard using Python, OOP, Streamlit, and local JSON storage. The app lets a teacher add/edit/delete students, record subject-wise marks and attendance, auto-calculate grades, and view class-level statistics and charts.

**Scope:**
- 6 Python source files + 1 test file
- Single-page Streamlit app with 4 tabs
- Local `students.json` for persistence
- No authentication, no database, no external APIs

**Approach:**
- Strict separation: business logic lives in pure Python classes; Streamlit only handles display and user input
- Data is loaded once at startup into `st.session_state`, mutated in memory, and written back to disk on every change
- All computed fields (total, percentage, grade) are derived on the fly — never stored

**Technology:**
- Python 3.10+
- Streamlit
- Matplotlib (charts)
- pytest (unit tests)
- JSON file storage

**Grade Scale:**
- A+ = 90–100%
- A  = 80–89%
- B  = 70–79%
- C  = 60–69%
- D  = 50–59%
- F  = below 50%

**Thresholds:**
- Low attendance: < 75%
- Low performance: overall percentage < 50%
- Default max marks per subject: 100

---

## Project Folder Structure

```
student_dashboard/
├── app.py                  # Streamlit entry point — UI only
├── student_manager.py      # StudentManager class — CRUD + filtering
├── grade_calculator.py     # GradeCalculator class — pure calculation logic
├── file_handler.py         # FileHandler class — JSON load/save
├── validator.py            # Validator class — input validation
├── constants.py            # Thresholds, grade scale, defaults
├── tests/
│   └── test_grade_calculator.py   # pytest unit tests
└── students.json           # Auto-created on first run
```

---

## Data Model

### `students.json` structure

```
[
  {
    "student_id": "S001",
    "name": "Alice Smith",
    "attendance": 85.0,
    "subjects": [
      { "subject_name": "Mathematics", "marks_obtained": 88, "max_marks": 100 },
      { "subject_name": "Science",     "marks_obtained": 72, "max_marks": 100 }
    ]
  }
]
```

### Derived fields (never stored, always computed)
| Field | Formula |
|---|---|
| `total_obtained` | sum of marks_obtained across subjects |
| `total_max` | sum of max_marks across subjects |
| `overall_percentage` | (total_obtained / total_max) × 100 |
| `grade` | lookup from grade scale |
| `is_low_attendance` | attendance < LOW_ATTENDANCE_THRESHOLD |
| `is_low_performer` | overall_percentage < LOW_MARKS_THRESHOLD |

---

## Classes and Responsibilities

| Class | File | Responsibility |
|---|---|---|
| `GradeCalculator` | `grade_calculator.py` | Stateless pure functions: totals, percentage, grade |
| `Validator` | `validator.py` | Validates all user inputs, returns (bool, message) |
| `FileHandler` | `file_handler.py` | Reads and writes `students.json`; handles missing/corrupt file |
| `StudentManager` | `student_manager.py` | In-memory CRUD, filtering, statistics; uses GradeCalculator |
| _(functions)_ | `app.py` | Streamlit tab renderers; no logic, only UI |

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffold and Constants

**Status:** [ ] pending

**Intent:**
Create the project folder, empty placeholder files, and the `constants.py` module. This establishes the foundation every other sub-task builds on.

**Expected Outcomes:**
- Folder `student_dashboard/` exists with all 6 source files and `tests/` directory
- `constants.py` defines: grade scale dict, LOW_ATTENDANCE_THRESHOLD = 75.0, LOW_MARKS_THRESHOLD = 50.0, DEFAULT_MAX_MARKS = 100, DATA_FILE = "students.json"
- All other files are empty stubs (just a module docstring)

**Todo List:**
- [ ] Create `student_dashboard/` directory
- [ ] Create `constants.py` with all threshold values, grade scale, and defaults
- [ ] Create empty stub files: `grade_calculator.py`, `validator.py`, `file_handler.py`, `student_manager.py`, `app.py`
- [ ] Create `tests/` subdirectory with empty `test_grade_calculator.py`
- [ ] Create empty `students.json` containing `[]`

**Relevant Context:**
- Grade scale: A+=90, A=80, B=70, C=60, D=50, F=0
- Thresholds and defaults are consumed by every other module — define them here first

---

### Sub-Task 2 — GradeCalculator Class

**Status:** [ ] pending

**Intent:**
Implement the stateless calculation layer. This class has no dependencies on other project modules and can be fully unit-tested in isolation.

**Expected Outcomes:**
- `GradeCalculator` class with three static/class methods
- `calculate_totals(subjects)` returns `(total_obtained, total_max)` as a tuple of floats
- `calculate_percentage(obtained, maximum)` returns float; returns 0.0 if maximum is 0
- `calculate_grade(percentage)` returns a grade string (A+/A/B/C/D/F) using the grade scale from `constants.py`
- All methods are pure functions (no side effects, no I/O)

**Todo List:**
- [ ] Define `GradeCalculator` class in `grade_calculator.py`
- [ ] Implement `calculate_totals(subjects: list[dict]) -> tuple[float, float]`
- [ ] Implement `calculate_percentage(obtained: float, maximum: float) -> float`
- [ ] Implement `calculate_grade(percentage: float) -> str`
- [ ] Import grade scale from `constants.py`

**Relevant Context:**
- `subjects` is a list of dicts: `[{"subject_name": ..., "marks_obtained": ..., "max_marks": ...}]`
- Grade scale is defined in `constants.py` as a sorted list of (threshold, label) pairs
- Used by `StudentManager` to compute derived fields for display

---

### Sub-Task 3 — Unit Tests for GradeCalculator

**Status:** [ ] pending

**Intent:**
Write pytest tests covering all grade calculator logic — including boundary values and edge cases — before any UI work begins.

**Expected Outcomes:**
- `tests/test_grade_calculator.py` contains tests for all three methods
- All tests pass with `pytest tests/`
- Edge cases covered: 0 marks, 100%, grade boundaries, empty subject list, max_marks = 0

**Todo List:**
- [ ] Test `calculate_totals` with multiple subjects, single subject, and empty list
- [ ] Test `calculate_percentage` with normal values, 0/0, and 100/100
- [ ] Test `calculate_grade` for each grade boundary: 90, 80, 70, 60, 50, and below 50
- [ ] Test `calculate_grade` with exactly 89.9 (should be A, not A+)
- [ ] Run `pytest tests/` and confirm all pass

**Relevant Context:**
- Only tests `GradeCalculator` — no file I/O, no Streamlit in these tests
- Boundary values: 90=A+, 89=A, 80=A, 79=B, etc.

---

### Sub-Task 4 — Validator Class

**Status:** [ ] pending

**Intent:**
Implement all input validation logic as a single `Validator` class with static methods. Each method returns a tuple `(is_valid: bool, message: str)` so the UI can display the error without knowing validation internals.

**Expected Outcomes:**
- `Validator` class with 4 static methods
- `validate_student_id(sid, existing_ids)` — non-empty, alphanumeric+hyphen/underscore, unique
- `validate_name(name)` — non-empty, letters and spaces only, max 50 chars
- `validate_marks(obtained, maximum)` — both numeric, obtained >= 0, maximum > 0, obtained <= maximum
- `validate_attendance(value)` — numeric, 0 <= value <= 100
- Each returns `(True, "")` on success or `(False, "error message")` on failure

**Todo List:**
- [ ] Define `Validator` class in `validator.py`
- [ ] Implement `validate_student_id(sid: str, existing_ids: list[str]) -> tuple[bool, str]`
- [ ] Implement `validate_name(name: str) -> tuple[bool, str]`
- [ ] Implement `validate_marks(obtained: float, maximum: float) -> tuple[bool, str]`
- [ ] Implement `validate_attendance(value: float) -> tuple[bool, str]`
- [ ] Strip whitespace from string inputs before validating

**Relevant Context:**
- Validation runs in `app.py` before any data is passed to `StudentManager`
- The `(bool, message)` return pattern lets Streamlit call `st.error(message)` directly
- Student ID uniqueness check requires passing in the current list of IDs

---

### Sub-Task 5 — FileHandler Class

**Status:** [ ] pending

**Intent:**
Implement a `FileHandler` class that abstracts all disk I/O. It handles the cases of a missing file (first run) and a malformed file (corrupted JSON) without crashing.

**Expected Outcomes:**
- `FileHandler` class with two static methods
- `load(filepath)` — returns `list[dict]`; returns `[]` if file does not exist; returns `[]` and logs a warning if JSON is malformed
- `save(filepath, data)` — writes the list to JSON with indentation; raises `IOError` only for genuine write failures
- `students.json` is created automatically on first save if it does not exist

**Todo List:**
- [ ] Define `FileHandler` class in `file_handler.py`
- [ ] Implement `load(filepath: str) -> list[dict]`
- [ ] Handle `FileNotFoundError` by returning `[]`
- [ ] Handle `json.JSONDecodeError` by returning `[]`
- [ ] Implement `save(filepath: str, data: list[dict]) -> None`
- [ ] Use `json.dump` with `indent=2` for human-readable output

**Relevant Context:**
- `DATA_FILE` path constant is defined in `constants.py`
- Called once at startup by `app.py` to populate `st.session_state`
- Called after every mutation in `StudentManager`

---

### Sub-Task 6 — StudentManager Class

**Status:** [ ] pending

**Intent:**
Implement the core CRUD and query logic. `StudentManager` holds the in-memory student list, performs all mutations, delegates calculations to `GradeCalculator`, and delegates persistence to `FileHandler`.

**Expected Outcomes:**
- `StudentManager` class initialized with a list of student dicts and a filepath
- `add_student(student_id, name, attendance, subjects)` — validates uniqueness, appends, saves
- `update_student(student_id, name, attendance, subjects)` — finds by ID, updates fields, saves
- `delete_student(student_id)` — removes by ID, saves
- `get_all_students()` — returns all students, each enriched with derived fields
- `get_student_by_id(student_id)` — returns one student dict enriched with derived fields, or `None`
- `filter_by_grade(grade)` — returns students whose computed grade matches
- `filter_by_subject(subject_name)` — returns students who have that subject (case-insensitive)
- `get_low_attendance()` — returns students where attendance < LOW_ATTENDANCE_THRESHOLD
- `get_low_performers()` — returns students where percentage < LOW_MARKS_THRESHOLD
- `get_statistics()` — returns dict: class average %, top student, lowest student, pass count, fail count

**Todo List:**
- [ ] Define `StudentManager` class in `student_manager.py`
- [ ] Implement `__init__(self, students: list[dict], filepath: str)`
- [ ] Implement `_enrich(student)` — private method that adds derived fields to a student dict copy
- [ ] Implement `add_student(...)` using `_enrich` and `FileHandler.save`
- [ ] Implement `update_student(student_id, ...)` — replace record in-place, save
- [ ] Implement `delete_student(student_id)` — remove from list, save
- [ ] Implement `get_all_students()` — returns enriched copies
- [ ] Implement `get_student_by_id(student_id)` — returns enriched copy or None
- [ ] Implement `filter_by_grade(grade: str)` 
- [ ] Implement `filter_by_subject(subject_name: str)` — case-insensitive match
- [ ] Implement `get_low_attendance()`
- [ ] Implement `get_low_performers()`
- [ ] Implement `get_statistics()` — returns class-level summary dict

**Relevant Context:**
- `_enrich` must call `GradeCalculator.calculate_totals`, `calculate_percentage`, `calculate_grade`
- `_enrich` adds: `total_obtained`, `total_max`, `overall_percentage`, `grade`, `is_low_attendance`, `is_low_performer`
- `StudentManager` never modifies the raw dicts — always works on copies to avoid mutation bugs
- `get_statistics` needs: class average, top performer name, bottom performer name, pass count (grade != F), fail count

---

### Sub-Task 7 — Streamlit UI: App Shell and Tab Layout

**Status:** [ ] pending

**Intent:**
Build the top-level `app.py` shell: page config, session state initialization, tab scaffold, and the shared data-loading pattern. No business logic — just wiring.

**Expected Outcomes:**
- `app.py` runs with `streamlit run app.py` without errors
- Page title is "Student Performance Dashboard"
- Four tabs render: ➕ Add Student | 📋 All Students | ✏️ Edit / Delete | 📊 Statistics
- On first load, `FileHandler.load` is called and data is stored in `st.session_state.students`
- `StudentManager` is instantiated from `st.session_state.students` at the top of each render cycle
- Each tab renders a placeholder heading for now

**Todo List:**
- [ ] Set `st.set_page_config(page_title=..., layout="wide")`
- [ ] Load data into `st.session_state.students` on first run using `FileHandler.load`
- [ ] Instantiate `StudentManager` from session state at top of app body
- [ ] Create four tabs with `st.tabs([...])`
- [ ] Route each tab to a dedicated render function: `render_add_tab`, `render_students_tab`, `render_edit_tab`, `render_stats_tab`
- [ ] Each render function is a stub returning `st.info("Coming soon")`

**Relevant Context:**
- Session state pattern: `if "students" not in st.session_state: st.session_state.students = FileHandler.load(...)`
- `StudentManager` is stateless from Streamlit's point of view — instantiated fresh each render from session state
- Tab functions are defined in `app.py` itself (no separate UI modules needed at this scale)

---

### Sub-Task 8 — Streamlit UI: Add Student Tab

**Status:** [ ] pending

**Intent:**
Implement the ➕ Add Student tab. The user fills in name, ID, attendance, and one or more subjects with marks, then submits. Validation errors are shown inline. On success, data is written to disk and the UI resets.

**Expected Outcomes:**
- Form with: Student ID (text), Name (text), Attendance % (number slider 0–100)
- Dynamic subject section: user can add up to N subjects with subject name, marks obtained, max marks
- "Add Another Subject" button adds a new subject row (uses `st.session_state` to track subject count)
- On submit: all fields are validated using `Validator`; errors shown with `st.error`
- On valid submit: `StudentManager.add_student` is called; `st.success` shown; form resets
- `st.session_state.students` is updated after add

**Todo List:**
- [ ] Implement `render_add_tab(manager: StudentManager)` in `app.py`
- [ ] Add text inputs for student ID and name
- [ ] Add number input for attendance (0.0–100.0, default 100.0)
- [ ] Add session state counter for number of subject rows (`st.session_state.subject_count`)
- [ ] Render N subject rows: each has subject_name text input, marks_obtained number input, max_marks number input (default 100)
- [ ] Add "➕ Add Subject" button that increments subject count
- [ ] Add "Save Student" submit button
- [ ] On submit: collect all inputs, run validation, show errors or call `add_student`, reset subject count

**Relevant Context:**
- Subject rows are keyed by index, e.g., `subject_name_0`, `subject_name_1`
- Validation order: ID → name → attendance → each subject's marks
- After a successful save, reset `st.session_state.subject_count = 1` and call `st.rerun()`

---

### Sub-Task 9 — Streamlit UI: All Students Tab

**Status:** [ ] pending

**Intent:**
Implement the 📋 All Students tab. Shows a filterable table of all students with their computed grade, percentage, and attendance. Highlights low-attendance and low-performing students.

**Expected Outcomes:**
- Filter controls: dropdown for grade (All/A+/A/B/C/D/F), text input for subject name filter
- Table rendered with `st.dataframe` showing: ID, Name, Attendance, Total Obtained, Total Max, Percentage, Grade
- Low-attendance rows visually flagged (warning icon in name or separate indicator column)
- Low-performer rows visually flagged
- "⚠️ Low Attendance Students" expander section below table listing students below 75%
- "⚠️ Low Performers" expander section listing students below 50%
- "No students found" message when list is empty

**Todo List:**
- [ ] Implement `render_students_tab(manager: StudentManager)` in `app.py`
- [ ] Add grade dropdown filter using `st.selectbox`
- [ ] Add subject filter text input using `st.text_input`
- [ ] Apply filters to get student list from manager
- [ ] Build a display DataFrame from enriched student list (flatten subjects for display)
- [ ] Render with `st.dataframe`
- [ ] Add ⚠️ expander for low attendance using `manager.get_low_attendance()`
- [ ] Add ⚠️ expander for low performers using `manager.get_low_performers()`

**Relevant Context:**
- `st.dataframe` accepts a list of dicts or a pandas DataFrame
- Subject-wise marks in the table can be omitted at this level; shown in detail view or edit tab
- Filtering is applied client-side from the in-memory list — no need to reload JSON

---

### Sub-Task 10 — Streamlit UI: Edit and Delete Tab

**Status:** [ ] pending

**Intent:**
Implement the ✏️ Edit / Delete tab. The user selects a student by ID, sees their current data pre-filled in a form, edits it, and saves — or deletes the student.

**Expected Outcomes:**
- Student selector dropdown (by ID + name)
- On student selected: form pre-filled with current name, attendance, subjects
- "Save Changes" button: validates and calls `manager.update_student`; shows success/error
- "Delete Student" button with a confirmation checkbox: calls `manager.delete_student`
- After any mutation, `st.session_state.students` is refreshed and `st.rerun()` is called
- "No students to edit" message if student list is empty

**Todo List:**
- [ ] Implement `render_edit_tab(manager: StudentManager)` in `app.py`
- [ ] Add `st.selectbox` with student ID + name pairs
- [ ] Load selected student's current data into form fields using pre-filled `value=` parameters
- [ ] Render editable subject rows (same pattern as Add tab, but pre-filled)
- [ ] Add "Save Changes" button with validation and `manager.update_student` call
- [ ] Add "Delete Student" button guarded by a `st.checkbox("Confirm deletion")` 
- [ ] After save or delete: update `st.session_state.students` and call `st.rerun()`

**Relevant Context:**
- Student ID is displayed but not editable (it is the primary key)
- Pre-filling uses the selected student's `subjects` list length to set subject count
- After deletion, the selector should no longer show the deleted student — `st.rerun()` handles this

---

### Sub-Task 11 — Streamlit UI: Statistics and Charts Tab

**Status:** [ ] pending

**Intent:**
Implement the 📊 Statistics tab. Shows class-level KPIs, a bar chart of average marks per subject, and a grade distribution chart.

**Expected Outcomes:**
- KPI row using `st.metric`: Class Average %, Top Performer, Pass Count, Fail Count
- Bar chart: average marks per subject across all students (Matplotlib or `st.bar_chart`)
- Pie or bar chart: grade distribution (how many A+, A, B, C, D, F)
- "Not enough data to display statistics" message if fewer than 1 student exists

**Todo List:**
- [ ] Implement `render_stats_tab(manager: StudentManager)` in `app.py`
- [ ] Call `manager.get_statistics()` to get summary dict
- [ ] Render 4 `st.metric` cards in a `st.columns(4)` row
- [ ] Compute per-subject averages by iterating all students' subjects
- [ ] Render bar chart for subject averages using `st.bar_chart` or `matplotlib`
- [ ] Count grade distribution across all enriched students
- [ ] Render grade distribution chart using `st.bar_chart` or `matplotlib`
- [ ] Wrap charts in a try/except and show a message if data is insufficient

**Relevant Context:**
- `get_statistics()` returns: `class_avg`, `top_student`, `bottom_student`, `pass_count`, `fail_count`
- Per-subject averages require iterating all students — compute in `render_stats_tab`, not in `StudentManager`
- Use `matplotlib.pyplot` and `st.pyplot(fig)` for richer chart control, or use `st.bar_chart` for simplicity

---

### Sub-Task 12 — Integration, Final Wiring, and Smoke Test

**Status:** [ ] pending

**Intent:**
Connect all modules, run the full app end-to-end, verify all features work together, and confirm pytest passes.

**Expected Outcomes:**
- `streamlit run app.py` launches without errors
- All 4 tabs are functional: add, view, edit/delete, stats
- Adding a student saves to `students.json` and immediately appears in the All Students tab
- Editing a student updates the file and the UI
- Deleting a student removes them from file and UI
- Low attendance and low performer alerts trigger correctly
- Charts display when at least one student exists
- `pytest tests/` passes all tests

**Todo List:**
- [ ] Verify all imports are consistent across modules
- [ ] Add a `students.json` seed with 3–4 sample students for manual testing
- [ ] Run `streamlit run app.py` and walk through each tab manually
- [ ] Verify add → view → edit → delete flow end-to-end
- [ ] Verify statistics update after adding/deleting a student
- [ ] Run `pytest tests/` and confirm all tests pass
- [ ] Remove seed data, verify app handles empty `students.json` gracefully

**Relevant Context:**
- Common issues: circular imports (avoided by design), session state not updating (fixed by calling `st.rerun()` after mutations)
- The `_enrich` method in `StudentManager` is the most likely source of bugs — verify it handles 0 subjects gracefully

---

## Data Flow Diagram

```
User Input (Streamlit form)
        |
        v
   Validator.validate_*()
        |
   (valid) --> StudentManager.add/update/delete()
                    |
                    +--> GradeCalculator (derived fields)
                    |
                    +--> FileHandler.save() --> students.json
                    |
                    +--> st.session_state.students updated
                    |
                    v
             Streamlit re-renders from session state
```

---

## Validation Strategy

- All validation happens in `Validator` before any data reaches `StudentManager`
- The UI collects input, calls `Validator` methods, displays errors using `st.error()`, and only calls `StudentManager` if all validations pass
- `StudentManager` assumes inputs are already validated — it does not re-validate
- This keeps the business logic layer clean and the UI layer responsible for error messaging

---

## Exception Handling

| Scenario | Handling |
|---|---|
| `students.json` missing | `FileHandler.load` returns `[]` silently |
| `students.json` corrupt | `FileHandler.load` catches `JSONDecodeError`, returns `[]` |
| Duplicate student ID | Caught by `Validator.validate_student_id` before insert |
| `max_marks = 0` | Caught by `Validator.validate_marks`; `GradeCalculator` also returns 0.0 safely |
| No students in system | All tabs show graceful empty-state messages |
| Chart with no data | Wrapped in guard clause; shows info message instead of crashing |

---

## Unit Testing Strategy

File: `tests/test_grade_calculator.py`

Tests cover `GradeCalculator` only (pure functions, no I/O, no Streamlit):

| Test | What it checks |
|---|---|
| `test_calculate_totals_multiple` | Sum across multiple subjects |
| `test_calculate_totals_single` | Works with exactly one subject |
| `test_calculate_totals_empty` | Returns (0.0, 0.0) for empty list |
| `test_calculate_percentage_normal` | 80/100 = 80.0 |
| `test_calculate_percentage_zero_max` | 0/0 returns 0.0, no crash |
| `test_calculate_percentage_full` | 100/100 = 100.0 |
| `test_grade_a_plus` | 95% → A+ |
| `test_grade_a` | 85% → A |
| `test_grade_b` | 75% → B |
| `test_grade_c` | 65% → C |
| `test_grade_d` | 55% → D |
| `test_grade_f` | 45% → F |
| `test_grade_boundary_90` | Exactly 90% → A+ |
| `test_grade_boundary_89` | Exactly 89% → A |
| `test_grade_boundary_50` | Exactly 50% → D |
| `test_grade_boundary_49` | Exactly 49% → F |

---

## Implementation Sequence

The sub-tasks are designed to be implemented in order, each building on the previous:

1. **Sub-Task 1** — Project scaffold (no dependencies)
2. **Sub-Task 2** — GradeCalculator (depends on constants only)
3. **Sub-Task 3** — Unit tests (depends on GradeCalculator)
4. **Sub-Task 4** — Validator (depends on constants only)
5. **Sub-Task 5** — FileHandler (depends on constants only)
6. **Sub-Task 6** — StudentManager (depends on GradeCalculator + FileHandler)
7. **Sub-Task 7** — App shell (depends on FileHandler + StudentManager)
8. **Sub-Task 8** — Add Student tab (depends on app shell + Validator + StudentManager)
9. **Sub-Task 9** — All Students tab (depends on StudentManager)
10. **Sub-Task 10** — Edit/Delete tab (depends on StudentManager + Validator)
11. **Sub-Task 11** — Statistics tab (depends on StudentManager)
12. **Sub-Task 12** — Integration and smoke test (depends on all)
