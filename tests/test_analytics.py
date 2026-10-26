
import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analytics import (
    compute_overall_stats,
    compute_subject_stats,
    build_student_ranking,
    compute_attendance_correlation,
    compute_class_comparison,
    apply_filters,
)
from src.data_cleaning import compute_average_marks, categorise_performance

# ── Fixtures ──────────────────────────────────────────────────────────────────

SUBJ = ["Math", "Science"]

def _base_df():
    data = {
        "ID":      ["S1", "S2", "S3", "S4", "S5"],
        "Name":    ["Alice", "Bob", "Carol", "Dan", "Eve"],
        "Class":   ["A", "A", "B", "B", "A"],
        "Math":    [90.0, 60.0, 40.0, 20.0, 80.0],
        "Science": [80.0, 55.0, 45.0, 25.0, 75.0],
        "Attend":  [95.0, 80.0, 60.0, 50.0, 90.0],
    }
    df = pd.DataFrame(data)
    df["_avg"] = compute_average_marks(df, SUBJ)
    df["_cat"] = categorise_performance(df["_avg"])
    return df

# ── Test 1: Overall average is calculated correctly ───────────────────────────

def test_overall_average_correct():
    df = _base_df()
    # Averages: (90+80)/2=85, (60+55)/2=57.5, (40+45)/2=42.5, (20+25)/2=22.5, (80+75)/2=77.5
    # Grand mean = (85+57.5+42.5+22.5+77.5)/5 = 285/5 = 57.0
    stats = compute_overall_stats(df, "_avg", passing_threshold=40.0)
    assert abs(stats["overall_average"] - 57.0) < 0.01

# ── Test 2: Pass count is correct ────────────────────────────────────────────

def test_pass_count_correct():
    df = _base_df()
    # avg>=40: Alice(85✓), Bob(57.5✓), Carol(42.5✓), Dan(22.5✗), Eve(77.5✓) → 4 pass
    stats = compute_overall_stats(df, "_avg", passing_threshold=40.0)
    assert stats["pass_count"] == 4
    assert stats["fail_count"] == 1

# ── Test 3: Pass percentage ───────────────────────────────────────────────────

def test_pass_percentage():
    df = _base_df()
    stats = compute_overall_stats(df, "_avg", passing_threshold=40.0)
    assert abs(stats["pass_percentage"] - 80.0) < 0.01

# ── Test 4: Subject averages ──────────────────────────────────────────────────

def test_subject_averages():
    df = _base_df()
    subj_stats = compute_subject_stats(df, SUBJ, passing_threshold=40.0)
    # Math average = (90+60+40+20+80)/5 = 290/5 = 58.0
    assert abs(subj_stats.loc["Math", "Average"] - 58.0) < 0.01
    # Science average = (80+55+45+25+75)/5 = 280/5 = 56.0
    assert abs(subj_stats.loc["Science", "Average"] - 56.0) < 0.01

# ── Test 5: Subject pass / fail counts ───────────────────────────────────────

def test_subject_pass_fail_counts():
    df = _base_df()
    subj_stats = compute_subject_stats(df, SUBJ, passing_threshold=40.0)
    # Math >=40: 90✓ 60✓ 40✓ 20✗ 80✓ → 4 pass, 1 fail
    assert subj_stats.loc["Math", "Pass_Count"] == 4
    assert subj_stats.loc["Math", "Fail_Count"] == 1
    # Science >=40: 80✓ 55✓ 45✓ 25✗ 75✓ → 4 pass, 1 fail
    assert subj_stats.loc["Science", "Pass_Count"] == 4
    assert subj_stats.loc["Science", "Fail_Count"] == 1

# ── Test 6: Subject handling missing values ───────────────────────────────────

def test_subject_stats_handles_nan():
    df = _base_df()
    df.loc[0, "Math"] = float("nan")  # One NaN
    df["_avg"] = compute_average_marks(df, SUBJ)
    subj_stats = compute_subject_stats(df, SUBJ, passing_threshold=40.0)
    # Only 4 valid Math entries now
    assert subj_stats.loc["Math", "Valid_Count"] == 4
    # Mean of remaining: (60+40+20+80)/4 = 200/4 = 50.0
    assert abs(subj_stats.loc["Math", "Average"] - 50.0) < 0.01

# ── Test 7: Student ranking sorted correctly ──────────────────────────────────

def test_student_ranking_sorted_descending():
    df = _base_df()
    ranking = build_student_ranking(
        df, SUBJ, "_avg", "_cat", id_col="ID", name_col="Name",
        passing_threshold=40.0
    )
    avgs = ranking["Average_Marks"].dropna().tolist()
    assert avgs == sorted(avgs, reverse=True)

# ── Test 8: Tied scores share the same rank ───────────────────────────────────

def test_tied_scores_same_rank():
    df = pd.DataFrame({
        "ID":   ["S1", "S2", "S3"],
        "Math": [75.0, 75.0, 60.0],
        "Sci":  [75.0, 75.0, 50.0],
        "_cat": ["Good", "Good", "Average"],
    })
    df["_avg"] = compute_average_marks(df, ["Math", "Sci"])
    ranking = build_student_ranking(df, ["Math", "Sci"], "_avg", "_cat", id_col="ID",
                                    passing_threshold=40.0)
    top_ranks = ranking[ranking["Average_Marks"] == 75.0]["Rank"].unique()
    assert len(top_ranks) == 1  # Both tied students share rank 1

# ── Test 9: Attendance correlation handles insufficient data ──────────────────

def test_attendance_correlation_insufficient_data():
    df = pd.DataFrame({
        "_avg":   [80.0, 70.0],
        "Attend": [90.0, 85.0],
    })
    corr = compute_attendance_correlation(df, "_avg", "Attend")
    assert corr is None  # < 3 observations

# ── Test 10: Attendance correlation computed correctly ────────────────────────

def test_attendance_correlation_valid():
    df = _base_df()
    corr = compute_attendance_correlation(df, "_avg", "Attend")
    assert corr is not None
    assert -1.0 <= corr <= 1.0

# ── Test 11: No attendance column does not crash overall stats ────────────────

def test_overall_stats_no_attendance():
    df = _base_df()
    stats = compute_overall_stats(df, "_avg", passing_threshold=40.0, attendance_col=None)
    assert stats["avg_attendance"] is None

# ── Test 12: Class comparison computes per-class averages ─────────────────────

def test_class_comparison():
    df = _base_df()
    comp = compute_class_comparison(df, "Class", "_avg")
    # Class A: Alice(85), Bob(57.5), Eve(77.5) → mean = 220/3 ≈ 73.33
    # Class B: Carol(42.5), Dan(22.5) → mean = 65/2 = 32.5
    class_a_avg = comp.loc[comp["Class"] == "A", "Average_Marks"].values[0]
    class_b_avg = comp.loc[comp["Class"] == "B", "Average_Marks"].values[0]
    assert abs(class_a_avg - (85.0 + 57.5 + 77.5) / 3) < 0.1
    assert abs(class_b_avg - (42.5 + 22.5) / 2) < 0.1

# ── Test 13: apply_filters — class filter ────────────────────────────────────

def test_apply_filters_class():
    df = _base_df()
    filtered = apply_filters(df, "_avg", class_col="Class", selected_classes=["A"])
    assert set(filtered["Class"].unique()) == {"A"}
    assert len(filtered) == 3  # Alice, Bob, Eve

# ── Test 14: apply_filters — empty result when no match ──────────────────────

def test_apply_filters_empty_result():
    df = _base_df()
    filtered = apply_filters(df, "_avg", min_avg=99.0, max_avg=100.0)
    assert filtered.empty

# ── Test 15: apply_filters — search by name ──────────────────────────────────

def test_apply_filters_search_by_name():
    df = _base_df()
    filtered = apply_filters(df, "_avg", name_col="Name", search_term="alice")
    assert len(filtered) == 1
    assert filtered.iloc[0]["Name"] == "Alice"

# ── Test 16: Students below passing threshold identified ─────────────────────

def test_students_below_threshold():
    df = _base_df()
    below = df[df["_avg"] < 40.0]
    assert len(below) == 1
    assert below.iloc[0]["ID"] == "S4"  # Dan with avg=22.5
