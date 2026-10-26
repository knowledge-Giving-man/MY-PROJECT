
import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.insights import generate_insights, generate_attention_insights
from src.analytics import compute_subject_stats, compute_overall_stats
from src.data_cleaning import compute_average_marks, categorise_performance

# ── Helpers ───────────────────────────────────────────────────────────────────

SUBJ = ["Math", "Science"]

def _make_base_df():
    data = {
        "Math":    [90.0, 60.0, 30.0, 80.0, 50.0],
        "Science": [85.0, 55.0, 25.0, 75.0, 45.0],
        "Attend":  [95.0, 80.0, 50.0, 90.0, 70.0],
    }
    df = pd.DataFrame(data)
    df["_avg"] = compute_average_marks(df, SUBJ)
    df["_cat"] = categorise_performance(df["_avg"])
    return df

# ── Test 1: Insights list is non-empty for valid data ─────────────────────────

def test_insights_non_empty_for_valid_data():
    df = _make_base_df()
    stats  = compute_overall_stats(df, "_avg", 40.0, "Attend")
    s_stats = compute_subject_stats(df, SUBJ, 40.0)
    ins = generate_insights(stats, s_stats, 40.0, 75.0, [], "Attend")
    assert len(ins) > 0

# ── Test 2: Best subject identified correctly ─────────────────────────────────

def test_best_subject_in_insights():
    df = _make_base_df()
    stats   = compute_overall_stats(df, "_avg", 40.0)
    s_stats = compute_subject_stats(df, SUBJ, 40.0)
    # Math avg = (90+60+30+80+50)/5 = 310/5 = 62.0
    # Science avg = (85+55+25+75+45)/5 = 285/5 = 57.0
    # Math should be identified as best
    ins = generate_insights(stats, s_stats, 40.0, 75.0, [], None)
    combined = " ".join(ins)
    assert "Math" in combined
    assert "highest" in combined.lower()

# ── Test 3: Worst subject identified correctly ────────────────────────────────

def test_worst_subject_in_insights():
    df = _make_base_df()
    stats   = compute_overall_stats(df, "_avg", 40.0)
    s_stats = compute_subject_stats(df, SUBJ, 40.0)
    ins = generate_insights(stats, s_stats, 40.0, 75.0, [], None)
    combined = " ".join(ins)
    # Science is the weakest
    assert "Science" in combined
    assert "lowest" in combined.lower()

# ── Test 4: No attendance note when no attendance col ────────────────────────

def test_no_attendance_insight_when_no_col():
    df = _make_base_df()
    stats   = compute_overall_stats(df, "_avg", 40.0)
    s_stats = compute_subject_stats(df, SUBJ, 40.0)
    ins = generate_insights(stats, s_stats, 40.0, 75.0, [], attendance_col=None)
    combined = " ".join(ins)
    assert "not supplied" in combined.lower() or "not available" in combined.lower() or "unavailable" in combined.lower()

# ── Test 5: Data quality warnings count appears in insights ───────────────────

def test_data_quality_warnings_appear():
    df = _make_base_df()
    stats   = compute_overall_stats(df, "_avg", 40.0)
    s_stats = compute_subject_stats(df, SUBJ, 40.0)
    warnings = ["Some marks were invalid.", "Duplicate found."]
    ins = generate_insights(stats, s_stats, 40.0, 75.0, warnings, None)
    combined = " ".join(ins)
    assert "2" in combined and "warning" in combined.lower()

# ── Test 6: generate_attention_insights — all passing ────────────────────────

def test_attention_insights_no_flagged():
    empty_flagged = pd.DataFrame(columns=["flag_overall_fail"])
    ins = generate_attention_insights(empty_flagged, total_students=5)
    combined = " ".join(ins)
    assert "no students" in combined.lower() or "0" in combined

# ── Test 7: generate_attention_insights — some flagged ───────────────────────

def test_attention_insights_with_flagged():
    flagged = pd.DataFrame({
        "flag_overall_fail":   [True, True],
        "flag_subject_fail":   [False, True],
        "flag_low_attendance": [False, False],
    })
    ins = generate_attention_insights(flagged, total_students=5)
    combined = " ".join(ins)
    assert "2" in combined  # 2 students flagged

# ── Test 8: Insights handle tied subject averages without crash ───────────────

def test_insights_tied_subject_averages():
    df = pd.DataFrame({
        "Math":    [50.0, 50.0],
        "Science": [50.0, 50.0],
    })
    df["_avg"] = compute_average_marks(df, SUBJ)
    stats   = compute_overall_stats(df, "_avg", 40.0)
    s_stats = compute_subject_stats(df, SUBJ, 40.0)
    # Should not raise
    ins = generate_insights(stats, s_stats, 40.0, 75.0, [], None)
    assert isinstance(ins, list)

# ── Test 9: Insights for empty DataFrame produce no crash ─────────────────────

def test_insights_empty_dataframe():
    empty_df = pd.DataFrame({"_avg": pd.Series([], dtype=float)})
    stats = compute_overall_stats(empty_df, "_avg", 40.0)
    s_stats = compute_subject_stats(empty_df, [], 40.0)
    ins = generate_insights(stats, s_stats, 40.0, 75.0, [], None)
    assert isinstance(ins, list)
