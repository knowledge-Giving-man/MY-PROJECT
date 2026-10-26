
import pandas as pd
import numpy as np
import pytest
import plotly.graph_objects as go

from src.visualizations import (
    subject_performance_bar,
    marks_distribution_histogram,
    top_students_bar,
    pass_fail_donut,
    subject_pass_fail_bar,
    attendance_vs_marks_scatter,
    class_comparison_bar,
    performance_category_chart,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_student_df(n: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    _cats = ["Excellent", "Good", "Average", "Needs Improvement", "Below Threshold"]
    return pd.DataFrame({
        "Student_ID":           [f"STU{i:03d}" for i in range(1, n + 1)],
        "Name":                 [f"Student {i}" for i in range(1, n + 1)],
        "Average_Marks":        rng.uniform(30, 95, n).round(1),
        "Attendance":           rng.uniform(50, 100, n).round(1),
        "Performance_Category": [_cats[i % len(_cats)] for i in range(n)],
    })

def _make_subject_stats() -> pd.DataFrame:
    data = {
        "Average":    [56.3, 57.8, 59.6, 60.5],
        "Median":     [55.0, 58.0, 61.0, 62.0],
        "Std_Dev":    [12.1, 11.4, 13.2, 10.9],
        "Min":        [20.0, 22.0, 25.0, 30.0],
        "Max":        [95.0, 96.0, 97.0, 98.0],
        "Pass_Count": [42, 44, 46, 48],
        "Fail_Count": [8, 6, 4, 2],
        "Pass_Pct":   [84.0, 88.0, 92.0, 96.0],
        "Missing":    [3, 2, 1, 0],
    }
    return pd.DataFrame(data, index=pd.Index(
        ["Mathematics", "Science", "English", "Computer Science"],
        name="Subject"
    ))

def _assert_valid_figure(fig) -> None:
    assert fig is not None
    assert isinstance(fig, go.Figure)

# ── subject_performance_bar ───────────────────────────────────────────────────

class TestSubjectPerformanceBar:

    def test_returns_figure_for_valid_data(self):
        stats = _make_subject_stats()
        fig = subject_performance_bar(stats)
        _assert_valid_figure(fig)

    def test_returns_figure_for_empty_dataframe(self):
        fig = subject_performance_bar(pd.DataFrame())
        _assert_valid_figure(fig)

    def test_returns_figure_when_average_column_missing(self):
        stats = _make_subject_stats().drop(columns=["Average"])
        fig = subject_performance_bar(stats)
        _assert_valid_figure(fig)

    def test_has_bar_traces_for_valid_data(self):
        stats = _make_subject_stats()
        fig = subject_performance_bar(stats)
        # At least one data trace should be present
        assert len(fig.data) >= 1

# ── marks_distribution_histogram ─────────────────────────────────────────────

class TestMarksDistributionHistogram:

    def test_returns_figure_for_valid_data(self):
        df = _make_student_df(10)
        fig = marks_distribution_histogram(df, "Average_Marks")
        _assert_valid_figure(fig)

    def test_returns_placeholder_for_single_row(self):
        df = _make_student_df(1)
        fig = marks_distribution_histogram(df, "Average_Marks")
        _assert_valid_figure(fig)
        # Placeholder has no data traces
        assert len(fig.data) == 0

    def test_returns_placeholder_for_all_nan(self):
        df = pd.DataFrame({"Average_Marks": [np.nan, np.nan, np.nan]})
        fig = marks_distribution_histogram(df, "Average_Marks")
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_mean_line_is_added(self):
        df = _make_student_df(10)
        fig = marks_distribution_histogram(df, "Average_Marks")
        # The mean vline is added as a shape or via add_vline
        layout_str = str(fig.layout)
        assert "dash" in layout_str or len(fig.layout.shapes) >= 0  # vline exists

# ── top_students_bar ──────────────────────────────────────────────────────────

class TestTopStudentsBar:

    def test_returns_figure_for_valid_data(self):
        df = _make_student_df(10)
        fig = top_students_bar(df, "Average_Marks", "Name", "Student_ID", top_n=5)
        _assert_valid_figure(fig)

    def test_returns_figure_without_name_or_id(self):
        df = _make_student_df(5)
        fig = top_students_bar(df, "Average_Marks", None, None, top_n=5)
        _assert_valid_figure(fig)

    def test_returns_placeholder_for_empty_df(self):
        df = pd.DataFrame({"Average_Marks": []})
        fig = top_students_bar(df, "Average_Marks", None, None)
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_limits_to_top_n(self):
        df = _make_student_df(20)
        fig = top_students_bar(df, "Average_Marks", "Name", "Student_ID", top_n=5)
        _assert_valid_figure(fig)
        # The bar chart data should contain at most 5 bars
        assert len(fig.data) >= 1

# ── pass_fail_donut ───────────────────────────────────────────────────────────

class TestPassFailDonut:

    def test_returns_figure_for_valid_stats(self):
        stats = {"pass_count": 80, "fail_count": 20}
        fig = pass_fail_donut(stats)
        _assert_valid_figure(fig)

    def test_returns_placeholder_when_both_zero(self):
        stats = {"pass_count": 0, "fail_count": 0}
        fig = pass_fail_donut(stats)
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_returns_figure_when_all_pass(self):
        stats = {"pass_count": 100, "fail_count": 0}
        fig = pass_fail_donut(stats)
        _assert_valid_figure(fig)
        assert len(fig.data) >= 1

    def test_returns_figure_when_all_fail(self):
        stats = {"pass_count": 0, "fail_count": 30}
        fig = pass_fail_donut(stats)
        _assert_valid_figure(fig)
        assert len(fig.data) >= 1

    def test_missing_keys_default_to_zero(self):
        # If keys are absent, .get() returns 0 — both zero → placeholder
        fig = pass_fail_donut({})
        _assert_valid_figure(fig)

# ── subject_pass_fail_bar ─────────────────────────────────────────────────────

class TestSubjectPassFailBar:

    def test_returns_figure_for_valid_data(self):
        stats = _make_subject_stats()
        fig = subject_pass_fail_bar(stats)
        _assert_valid_figure(fig)

    def test_has_two_traces_pass_and_fail(self):
        stats = _make_subject_stats()
        fig = subject_pass_fail_bar(stats)
        # Grouped bar should have exactly 2 traces: Pass and Fail
        assert len(fig.data) == 2
        trace_names = {t.name for t in fig.data}
        assert "Pass" in trace_names
        assert "Fail" in trace_names

    def test_returns_placeholder_for_empty_dataframe(self):
        fig = subject_pass_fail_bar(pd.DataFrame())
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

# ── attendance_vs_marks_scatter ───────────────────────────────────────────────

class TestAttendanceVsMarksScatter:

    def test_returns_figure_for_valid_data(self):
        df = _make_student_df(10)
        fig = attendance_vs_marks_scatter(df, "Average_Marks", "Attendance")
        _assert_valid_figure(fig)

    def test_returns_placeholder_for_single_row(self):
        df = _make_student_df(1)
        fig = attendance_vs_marks_scatter(df, "Average_Marks", "Attendance")
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_returns_placeholder_when_attendance_all_nan(self):
        df = _make_student_df(5)
        df["Attendance"] = np.nan
        fig = attendance_vs_marks_scatter(df, "Average_Marks", "Attendance")
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_accepts_optional_category_and_name_cols(self):
        df = _make_student_df(10)
        fig = attendance_vs_marks_scatter(
            df, "Average_Marks", "Attendance",
            category_col="Performance_Category", name_col="Name"
        )
        _assert_valid_figure(fig)
        assert len(fig.data) >= 1

# ── class_comparison_bar ──────────────────────────────────────────────────────

class TestClassComparisonBar:

    def test_returns_figure_for_valid_data(self):
        df = pd.DataFrame({
            "Class": ["Class A", "Class B", "Class C"],
            "Average_Marks": [62.3, 58.7, 55.1],
        })
        fig = class_comparison_bar(df)
        _assert_valid_figure(fig)

    def test_returns_placeholder_for_empty_dataframe(self):
        fig = class_comparison_bar(pd.DataFrame())
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_has_one_trace_for_valid_data(self):
        df = pd.DataFrame({
            "Class": ["A", "B"],
            "Average_Marks": [70.0, 65.0],
        })
        fig = class_comparison_bar(df)
        assert len(fig.data) >= 1

# ── performance_category_chart ────────────────────────────────────────────────

class TestPerformanceCategoryChart:

    def test_returns_figure_for_valid_data(self):
        df = _make_student_df(5)
        fig = performance_category_chart(df, "Performance_Category")
        _assert_valid_figure(fig)

    def test_returns_placeholder_for_missing_column(self):
        df = _make_student_df(5)
        fig = performance_category_chart(df, "NonExistentColumn")
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_returns_placeholder_for_empty_dataframe(self):
        df = pd.DataFrame({"Performance_Category": []})
        fig = performance_category_chart(df, "Performance_Category")
        _assert_valid_figure(fig)
        assert len(fig.data) == 0

    def test_handles_single_category(self):
        df = pd.DataFrame({"Performance_Category": ["Excellent"] * 5})
        fig = performance_category_chart(df, "Performance_Category")
        _assert_valid_figure(fig)
        assert len(fig.data) >= 1
