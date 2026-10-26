
import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_cleaning import (
    validate_and_clean,
    compute_average_marks,
    categorise_performance,
    flag_needs_support,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_df(**kwargs):
    base = {
        "Student_ID":   ["S001", "S002", "S003"],
        "Student_Name": ["Alice", "Bob", "Carol"],
        "Math":         [80.0, 45.0, 30.0],
        "Science":      [70.0, 40.0, 20.0],
    }
    base.update(kwargs)
    # Ensure all value lists have the same length
    return pd.DataFrame(base)

SUBJECT_COLS = ["Math", "Science"]

# ── Test 1: Loading a valid dataset ──────────────────────────────────────────

def test_valid_dataset_cleans_without_errors():
    df = _make_df()
    cleaned, report = validate_and_clean(df, SUBJECT_COLS)
    assert not report.has_critical_errors
    assert report.valid_student_rows == 3
    assert report.missing_values == 0

# ── Test 2: Empty dataset ─────────────────────────────────────────────────────

def test_empty_dataset_returns_critical_error():
    df = pd.DataFrame(columns=["Student_ID", "Math", "Science"])
    cleaned, report = validate_and_clean(df, SUBJECT_COLS)
    assert report.has_critical_errors
    assert any("no rows" in e.lower() for e in report.errors)

# ── Test 3: Missing values are detected ───────────────────────────────────────

def test_missing_values_are_counted():
    df = _make_df(Math=[80.0, float("nan"), 30.0])
    cleaned, report = validate_and_clean(df, SUBJECT_COLS)
    assert report.missing_values >= 1
    assert not report.has_critical_errors

# ── Test 4: Duplicate rows are detected ──────────────────────────────────────

def test_duplicate_rows_detected_and_removed():
    df = _make_df()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # duplicate first row
    cleaned, report = validate_and_clean(df, SUBJECT_COLS, drop_duplicates=True)
    assert report.duplicate_rows >= 1
    assert len(cleaned) < len(df)

# ── Test 5: Marks outside [0, 100] are invalidated ───────────────────────────

def test_marks_outside_range_set_to_nan():
    df = _make_df(Math=[80.0, 150.0, -5.0])  # 150 and -5 are invalid
    cleaned, report = validate_and_clean(df, SUBJECT_COLS)
    assert report.invalid_mark_cells >= 2
    assert cleaned["Math"].isna().sum() >= 2

# ── Test 6: Missing subject columns trigger a critical error ─────────────────

def test_missing_subject_column_triggers_error():
    df = _make_df()
    cleaned, report = validate_and_clean(df, ["Math", "NonExistentSubject"])
    assert report.has_critical_errors

# ── Test 7: Non-numeric values are coerced to NaN ────────────────────────────

def test_non_numeric_marks_coerced_to_nan():
    df = _make_df(Math=[80.0, "AB", 30.0])
    cleaned, report = validate_and_clean(df, SUBJECT_COLS)
    assert cleaned["Math"].isna().any()
    assert len(report.warnings) > 0

# ── Test 8: drop_incomplete removes rows with any missing subject ─────────────

def test_drop_incomplete_removes_partial_rows():
    df = _make_df(Math=[80.0, float("nan"), 30.0])
    cleaned, report = validate_and_clean(df, SUBJECT_COLS, drop_incomplete=True)
    # Row with NaN Math should be removed
    assert cleaned["Math"].isna().sum() == 0
    assert len(cleaned) == 2

# ── Test 9: Attendance values outside [0, 100] are set to NaN ────────────────

def test_invalid_attendance_set_to_nan():
    df = _make_df(Attendance=[101.0, 75.0, -1.0])
    cleaned, report = validate_and_clean(
        df, SUBJECT_COLS, attendance_col="Attendance"
    )
    assert report.invalid_attendance_cells >= 2
    assert cleaned["Attendance"].isna().sum() >= 2

# ── Test 10: Compute average marks handles NaN correctly ─────────────────────

def test_compute_average_marks_skips_nan():
    df = pd.DataFrame({
        "Math":    [80.0, float("nan"), 60.0],
        "Science": [60.0, 50.0,         float("nan")],
    })
    avgs = compute_average_marks(df, ["Math", "Science"])
    # Row 0: (80+60)/2 = 70
    assert abs(avgs.iloc[0] - 70.0) < 0.01
    # Row 1: only Science=50 → average = 50
    assert abs(avgs.iloc[1] - 50.0) < 0.01
    # Row 2: only Math=60 → average = 60
    assert abs(avgs.iloc[2] - 60.0) < 0.01

# ── Test 11: categorise_performance assigns correct categories ────────────────

def test_categorise_performance_boundaries():
    marks = pd.Series([95.0, 75.0, 60.0, 44.0, 35.0, float("nan")])
    cats  = categorise_performance(marks)
    assert cats.iloc[0] == "Excellent"
    assert cats.iloc[1] == "Good"
    assert cats.iloc[2] == "Average"
    assert cats.iloc[3] == "Needs Improvement"
    assert cats.iloc[4] == "Below Threshold"
    assert cats.iloc[5] == "No Data"

# ── Test 12: flag_needs_support flags correctly ───────────────────────────────

def test_flag_needs_support_flags_low_averages():
    df = _make_df(Math=[80.0, 45.0, 25.0], Science=[70.0, 35.0, 20.0])
    df["_avg"] = compute_average_marks(df, SUBJECT_COLS)
    flagged = flag_needs_support(
        df, SUBJECT_COLS, "_avg",
        passing_threshold=40.0, subject_pass_threshold=40.0
    )
    # Row 2: avg=(25+20)/2=22.5 → overall fail
    assert flagged.loc[2, "flag_overall_fail"] is True or flagged.loc[2, "flag_overall_fail"] == True
    # Row 0: avg=(80+70)/2=75 → should NOT be flagged
    assert not flagged.loc[0, "flag_any"]

# ── Test 13: All NaN subject rows are not valid ───────────────────────────────

def test_all_nan_row_gives_nan_average():
    df = pd.DataFrame({
        "Math":    [float("nan")],
        "Science": [float("nan")],
    })
    avg = compute_average_marks(df, ["Math", "Science"])
    assert pd.isna(avg.iloc[0])
