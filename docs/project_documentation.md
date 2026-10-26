# Student Performance Analysis Dashboard
## Technical Project Documentation

**Project Title:** Student Performance Analysis Dashboard Using Python  
**Technology Stack:** Python 3.11+, Streamlit, Pandas, NumPy, Plotly, pytest  
**Department:** Computer Science and Engineering  
**Academic Session:** 2025–2026  
**Document Type:** Technical Reference  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Module Reference](#2-module-reference)
3. [Data Flow](#3-data-flow)
4. [Data Schema](#4-data-schema)
5. [Analytics Pipeline](#5-analytics-pipeline)
6. [Visualisation Reference](#6-visualisation-reference)
7. [Insight Engine](#7-insight-engine)
8. [Testing Strategy](#8-testing-strategy)
9. [Configuration & Constants](#9-configuration--constants)
10. [Known Limitations & Edge Cases](#10-known-limitations--edge-cases)

---

## 1. Architecture Overview

The application follows a **layered architecture** with a clear separation between the UI layer, the business logic layer, and the data layer.

```
┌─────────────────────────────────────────────────────────┐
│                    app.py  (UI Layer)                   │
│         Streamlit — sidebar, tabs, KPI cards,           │
│         filter controls, download buttons               │
└────────────────────────┬────────────────────────────────┘
                         │ calls
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
┌──────────────┐ ┌──────────────────┐ ┌────────────────┐
│ data_loader  │ │  data_cleaning   │ │   analytics    │
│   .py        │ │      .py         │ │     .py        │
│              │ │                  │ │                │
│ Reads CSV /  │ │ Validates,       │ │ Stats, ranks,  │
│ Excel files. │ │ cleans, flags    │ │ filters,       │
│ Auto-detects │ │ students needing │ │ correlations,  │
│ columns.     │ │ support.         │ │ class compare. │
└──────────────┘ └──────────────────┘ └────────────────┘
         │               │                   │
         └───────────────┼───────────────────┘
                         │ feeds
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
┌──────────────────┐             ┌──────────────────────┐
│ visualizations   │             │      insights.py      │
│     .py          │             │                       │
│                  │             │ Rule-based textual    │
│ 8 Plotly charts  │             │ observations derived  │
│ returned as      │             │ from computed stats.  │
│ go.Figure objs   │             │                       │
└──────────────────┘             └──────────────────────┘
```

### Design Principles

| Principle | How It Is Applied |
|-----------|------------------|
| **Separation of concerns** | UI logic lives only in `app.py`; all calculations are in `src/` |
| **No side effects in library modules** | `src/` modules are pure functions — they accept DataFrames and return DataFrames or dicts |
| **Graceful degradation** | All chart functions return a placeholder figure if data is insufficient |
| **Explicit over implicit** | Missing values are never silently replaced; they are reported and excluded |
| **Testability** | All business logic modules have corresponding `tests/` files |

---

## 2. Module Reference

### 2.1 `app.py` — Main Streamlit Application

**Responsibility:** Orchestrate the entire user interface.

**Key sections:**

| Section | Purpose |
|---------|---------|
| Page config & CSS | Sets page title, icon, layout, and injects custom CSS |
| Sidebar — data source | Radio button: Sample Dataset / Upload CSV / Excel |
| Sidebar — column mapping | Expander allowing the user to identify which columns are Student ID, Name, Class, Attendance, Subjects |
| Sidebar — filters | Class filter, category filter, marks range slider, attendance slider, text search, reset button |
| KPI cards | Five metric cards rendered with `st.metric` |
| Tab: Overview | Marks histogram + pass/fail donut |
| Tab: Subjects | Subject bar chart + pass/fail grouped bar + statistics table |
| Tab: Students | Ranked student table with colour-coded pass/fail |
| Tab: Needs Support | Filtered list of flagged students |
| Tab: Attendance | Scatter plot + correlation coefficient |
| Tab: Insights | Algorithmically generated insight list |
| Tab: Data Quality | Missing value counts, duplicate summary, invalid mark counts |
| Tab: Export | Four CSV/Markdown download buttons |

**State management:** Streamlit's `st.session_state` is used to persist the loaded DataFrame and column mapping across reruns triggered by widget interactions.

---

### 2.2 `src/data_loader.py` — File Loading & Column Detection

**Public functions:**

```python
load_file(uploaded_file) -> pd.DataFrame
```
Accepts a `UploadedFile` object from `st.file_uploader`. Returns a raw DataFrame. Supports `.csv` and `.xlsx` / `.xls`.

```python
auto_detect_columns(df: pd.DataFrame) -> dict
```
Scans column names using keyword matching to suggest likely mappings for Student ID, Name, Class, and Attendance columns. Returns a dict of `{role: column_name_or_None}`.

**Column detection keywords:**

| Role | Keywords checked (case-insensitive) |
|------|-------------------------------------|
| Student ID | `id`, `roll`, `number`, `no`, `num` |
| Name | `name`, `student` |
| Class | `class`, `group`, `section`, `division`, `batch` |
| Attendance | `attend`, `presence`, `present` |

---

### 2.3 `src/data_cleaning.py` — Validation & Cleaning

**Public function:**

```python
clean_and_validate(
    df: pd.DataFrame,
    subject_cols: list[str],
    attendance_col: str | None,
    pass_mark: int,
    attendance_threshold: float,
    drop_incomplete: bool,
) -> tuple[pd.DataFrame, dict]
```

Returns `(cleaned_df, quality_report)`.

**Cleaning steps performed, in order:**

| Step | What Happens |
|------|--------------|
| 1. Empty check | Returns an error if the DataFrame has zero rows |
| 2. Duplicate removal | Exact duplicate rows are dropped |
| 3. Mark coercion | Non-numeric mark values are coerced to `NaN` using `pd.to_numeric(..., errors='coerce')` |
| 4. Range validation | Values outside `[0, 100]` are set to `NaN` |
| 5. Attendance validation | Values outside `[0, 100]` are set to `NaN` |
| 6. Drop incomplete (optional) | Rows with any `NaN` in subject columns are dropped if `drop_incomplete=True` |
| 7. Average computation | `Average_Marks` column is added; computed row-wise, skipping `NaN` values |
| 8. Category assignment | `Performance_Category` column is added based on `Average_Marks` thresholds |
| 9. Pass/Fail flag | `Pass_Fail` column is added: `Pass` if `Average_Marks >= pass_mark`, else `Fail` |
| 10. Needs Support flag | `Needs_Support` column is added based on configurable criteria |

**Performance category thresholds:**

| Category | Condition |
|----------|-----------|
| Excellent | Average >= 80 |
| Good | 65 <= Average < 80 |
| Average | 50 <= Average < 65 |
| Needs Improvement | 40 <= Average < 50 |
| Below Threshold | Average < 40 |
| No Data | All subject marks are NaN |

**Needs Support flag logic:**

A student is flagged (`Needs_Support = True`) if **any** of the following:
- `Average_Marks < pass_mark` (overall fail)
- Any individual subject mark < `pass_mark` (subject-level fail)
- `Attendance < attendance_threshold` (low attendance), if an attendance column is configured

---

### 2.4 `src/analytics.py` — Statistical Calculations

**Public functions:**

```python
compute_overall_stats(df, subject_cols, avg_col, pass_col, attendance_col) -> dict
```
Returns a dict with keys: `total_students`, `average_marks`, `median_marks`, `std_dev`, `pass_count`, `fail_count`, `pass_percentage`, `avg_attendance`, `support_count`.

```python
compute_subject_stats(df, subject_cols, pass_mark) -> pd.DataFrame
```
Returns a DataFrame indexed by Subject with columns: `Average`, `Median`, `Std_Dev`, `Min`, `Max`, `Pass_Count`, `Fail_Count`, `Pass_Pct`, `Missing`.

```python
rank_students(df, avg_col) -> pd.DataFrame
```
Sorts students descending by `avg_col`; adds a `Rank` column. Tied scores receive the same rank.

```python
compute_attendance_correlation(df, avg_col, attendance_col) -> float | None
```
Returns Pearson correlation coefficient, or `None` if fewer than 3 valid data points exist.

```python
compute_class_comparison(df, class_col, avg_col) -> pd.DataFrame
```
Returns a DataFrame with columns `Class` and `Average_Marks`, sorted descending.

```python
apply_filters(df, class_col, category_col, avg_col, attendance_col, ...) -> pd.DataFrame
```
Applies all active sidebar filters and returns the filtered DataFrame. Filters are additive (AND logic).

```python
get_students_below_threshold(df, avg_col, threshold) -> pd.DataFrame
```
Returns students whose `avg_col` value is below `threshold`.

---

### 2.5 `src/visualizations.py` — Plotly Chart Builders

All functions return a `plotly.graph_objects.Figure`. If the input data is insufficient, a `_safe_fig()` placeholder with an explanatory message is returned instead of raising an exception.

| Function | Chart Type | Key Input |
|----------|-----------|-----------|
| `subject_performance_bar(subject_stats)` | Horizontal bar | `subject_stats` DataFrame |
| `marks_distribution_histogram(df, avg_col)` | Histogram + mean line | Cleaned DataFrame |
| `top_students_bar(df, avg_col, name_col, id_col, top_n)` | Horizontal bar | Cleaned DataFrame |
| `pass_fail_donut(overall_stats)` | Donut chart | `overall_stats` dict |
| `subject_pass_fail_bar(subject_stats)` | Grouped bar | `subject_stats` DataFrame |
| `attendance_vs_marks_scatter(df, avg_col, attendance_col, ...)` | Scatter | Cleaned DataFrame |
| `class_comparison_bar(class_comparison_df)` | Vertical bar | Class comparison DataFrame |
| `performance_category_chart(df, category_col)` | Pie chart | Cleaned DataFrame |

---

### 2.6 `src/insights.py` — Insight Engine

**Public function:**

```python
generate_insights(
    df, overall_stats, subject_stats, avg_col,
    attendance_col, subject_cols
) -> list[str]
```

Returns a list of plain-English observation strings. Each string is derived from computed statistics — no hardcoded text, no language model.

---

## 3. Data Flow

```
User action: Load Sample Data
         |
         v
data_loader.load_sample_data()
         |  raw pd.DataFrame
         v
data_cleaning.clean_and_validate()
         |  cleaned pd.DataFrame + quality_report dict
         v
Stored in st.session_state["df"]
         |
         |<--- User changes a sidebar filter
         v
analytics.apply_filters()
         |  filtered pd.DataFrame
         v
+----------------------------------------+
|  analytics.compute_overall_stats()     |
|  analytics.compute_subject_stats()     |
|  analytics.rank_students()             |
|  analytics.compute_class_comparison()  |
|  analytics.compute_attendance_corr()   |
+----------------------------------------+
         |  stats dicts + DataFrames
         v
+-------------------------------+
|  visualizations.*()           |  -> Plotly figures -> st.plotly_chart()
|  insights.generate_insights() |  -> strings       -> st.markdown()
+-------------------------------+
```

---

## 4. Data Schema

### 4.1 Input CSV Requirements

The application accepts any CSV with a header row. There are no mandatory column name conventions — the user maps columns via the sidebar. However, the following columns must exist after mapping:

| Role | Required? | Notes |
|------|-----------|-------|
| Subject marks | **Yes** (>= 1) | Must contain numeric values in [0, 100] |
| Student ID | No | Used for display and search |
| Student Name | No | Used for labelling charts and search |
| Class / Group | No | Enables class-level filtering and comparison |
| Attendance | No | Enables attendance analysis and attendance-based support flagging |

### 4.2 Sample Dataset Schema (`data/sample_students.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `Student_ID` | string | Format: `STU001` to `STU120` |
| `Name` | string | Synthetic full name |
| `Class` | string | Values: `Class A`, `Class B`, `Class C` |
| `Mathematics` | float | Marks in [0, 100]; ~5% NaN by design |
| `Science` | float | Marks in [0, 100]; ~5% NaN by design |
| `English` | float | Marks in [0, 100]; ~5% NaN by design |
| `Computer Science` | float | Marks in [0, 100]; ~5% NaN by design |
| `Attendance` | float | Attendance percentage in [40, 100] |

### 4.3 Computed Columns Added After Cleaning

| Column | Type | Description |
|--------|------|-------------|
| `Average_Marks` | float | Row-wise mean of subject columns, NaN excluded |
| `Performance_Category` | string | One of five categories based on Average_Marks |
| `Pass_Fail` | string | `Pass` or `Fail` based on `pass_mark` threshold |
| `Needs_Support` | bool | `True` if student meets any support criterion |
| `Rank` | int | Rank by Average_Marks descending; ties share the same rank |

---

## 5. Analytics Pipeline

### 5.1 Overall Statistics

```
Overall Average  = mean(Average_Marks)
Median           = median(Average_Marks)
Std Dev          = std(Average_Marks)
Pass Count       = count(Pass_Fail == "Pass")
Pass Percentage  = (Pass Count / Total Students) x 100
Avg Attendance   = mean(attendance_col)   [if col exists]
Support Count    = count(Needs_Support == True)
```

### 5.2 Subject Statistics

For each subject column `s`:
```
Average     = mean(df[s].dropna())
Median      = median(df[s].dropna())
Std Dev     = std(df[s].dropna())
Min, Max    = min / max of non-NaN values
Pass Count  = count(df[s] >= pass_mark)
Fail Count  = count(df[s].notna() and df[s] < pass_mark)
Pass Pct    = (Pass Count / (Pass Count + Fail Count)) x 100
Missing     = count(df[s].isna())
```

### 5.3 Ranking

Students are ranked by `Average_Marks` descending using `method='min'` so that tied students receive the same (lower) rank number. Students with NaN average receive NaN rank.

### 5.4 Attendance Correlation

Uses Pearson correlation coefficient. A minimum of **3 non-NaN pairs** is required; otherwise `None` is returned and no correlation insight is generated.

### 5.5 Filter Logic

All filters are applied with **AND** semantics. An empty selection in a multi-select filter is treated as "no filter applied" (shows all values).

---

## 6. Visualisation Reference

| Chart | Type | Input | Edge Case Handling |
|-------|------|-------|-------------------|
| Subject Average | Horizontal bar | subject_stats | Placeholder if empty |
| Marks Distribution | Histogram | avg_col values | Placeholder if <2 points |
| Top N Students | Horizontal bar | avg_col, name/id cols | Placeholder if no data |
| Pass vs Fail | Donut | overall_stats dict | Placeholder if no students |
| Subject Pass/Fail | Grouped bar | subject_stats | Placeholder if empty |
| Attendance vs Marks | Scatter | avg_col, attendance_col | Placeholder if <2 pairs |
| Class Comparison | Vertical bar | class_comparison_df | Placeholder if empty |
| Category Distribution | Pie | category_col | Placeholder if empty |

**Shared colour palette:**

| Category | Hex Colour |
|----------|-----------|
| Excellent | `#1a9850` |
| Good | `#4575b4` |
| Average | `#fee090` |
| Needs Improvement | `#f46d43` |
| Below Threshold | `#d73027` |
| Pass | `#2ecc71` |
| Fail | `#e74c3c` |

---

## 7. Insight Engine

The insight engine generates observations using **conditional rule-based logic** applied to pre-computed statistics. No language model or external API is used.

### Insight Categories

| Category | Example Output |
|----------|---------------|
| Overall performance | "The overall class average is 58.9 out of 100." |
| Best/worst subject | "Computer Science is the strongest subject (avg 60.5)." |
| Pass rate | "83.3% of students passed overall." |
| Attendance correlation | "Attendance shows a moderate positive correlation with marks (r = 0.47)." |
| Support flagging | "12 students (10.0%) have been flagged as needing academic support." |
| Data quality | "24 mark cells are missing across the dataset." |
| Spread analysis | "Marks range from 21 to 97; standard deviation is 15.2." |

### Correlation Strength Labels

| Absolute r value | Label |
|-----------------|-------|
| < 0.2 | Weak |
| 0.2 – 0.5 | Moderate |
| > 0.5 | Strong |

---

## 8. Testing Strategy

### 8.1 Test Coverage Summary

| Test File | Module Tested | Tests | Status |
|-----------|--------------|-------|--------|
| `tests/test_analytics.py` | `src/analytics.py` | 16 | All Pass |
| `tests/test_data_cleaning.py` | `src/data_cleaning.py` | 13 | All Pass |
| `tests/test_insights.py` | `src/insights.py` | 9 | All Pass |
| **Total** | | **38** | **38/38 Passed** |

### 8.2 Test Approach

- **Unit tests only** — each test targets a single function with a small, self-contained DataFrame constructed inline.
- **No mocking** — the tested functions are pure; no external services are called.
- **No file fixtures** — tests do not read from `data/sample_students.csv` to avoid coupling to sample data content.
- **Edge cases explicitly tested:**
  - Empty DataFrames
  - All-NaN rows
  - Tied ranks
  - Datasets with no attendance column
  - Datasets with fewer than 3 rows (correlation edge case)

### 8.3 Running the Tests

```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Run all tests with verbose output
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_analytics.py -v

# Run with coverage (requires pytest-cov)
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## 9. Configuration & Constants

### 9.1 Default Values (set in `app.py` sidebar)

| Parameter | Default | Description |
|-----------|---------|-------------|
| Pass mark | 40 | Minimum average marks to classify as Pass |
| Attendance threshold | 75% | Minimum attendance to avoid support flagging |
| Top N students | 10 | Number of students in top students chart |
| Drop incomplete | False | Whether to remove rows with any missing subject mark |

### 9.2 `visualizations.py` Constants

```python
PLOTLY_TEMPLATE = "plotly_white"

CATEGORY_COLORS = {
    "Excellent":         "#1a9850",
    "Good":              "#4575b4",
    "Average":           "#fee090",
    "Needs Improvement": "#f46d43",
    "Below Threshold":   "#d73027",
    "No Data":           "#aaaaaa",
}

PASS_FAIL_COLORS = {
    "Pass": "#2ecc71",
    "Fail": "#e74c3c",
}
```

---

## 10. Known Limitations & Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| Dataset with 1 row | Analytics work; correlation returns None; histogram shows placeholder |
| All students pass | `fail_count = 0`; donut chart shows 100% Pass segment |
| All marks identical | `std_dev = 0`; spread insight is suppressed |
| No attendance column | Attendance KPI card hidden; scatter tab hidden; attendance-based flagging disabled |
| No class column | Class filter hidden; class comparison chart hidden |
| Non-UTF-8 CSV | Pandas attempts latin-1 fallback; error shown if unreadable |
| Excel with merged cells | Pandas may misread; user advised to flatten the sheet |
| Very large dataset (>50,000 rows) | Application works but chart rendering may be slower |
| Duplicate student IDs | Only exact duplicate rows (all columns equal) are removed |

---

*BTech Computer Science and Engineering — Mini Project | Academic Year: 2025–2026*
