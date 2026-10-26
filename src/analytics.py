
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

# ── Overall statistics ────────────────────────────────────────────────────────

def compute_overall_stats(
    df: pd.DataFrame,
    avg_col: str,
    passing_threshold: float = 40.0,
    attendance_col: Optional[str] = None,
) -> dict:
    valid = df[avg_col].dropna()
    total = len(df)
    valid_count = len(valid)

    if valid_count == 0:
        return _empty_overall_stats(total)

    pass_mask = valid >= passing_threshold
    pass_count = int(pass_mask.sum())
    fail_count = valid_count - pass_count

    result = {
        "total_students":   total,
        "valid_students":   valid_count,
        "overall_average":  round(float(valid.mean()), 2),
        "median_marks":     round(float(valid.median()), 2),
        "highest_marks":    round(float(valid.max()), 2),
        "lowest_marks":     round(float(valid.min()), 2),
        "std_dev":          round(float(valid.std()), 2),
        "pass_count":       pass_count,
        "fail_count":       fail_count,
        "pass_percentage":  round(pass_count / valid_count * 100, 2),
        "fail_percentage":  round(fail_count / valid_count * 100, 2),
        "avg_attendance":   None,
    }

    if attendance_col and attendance_col in df.columns:
        att_valid = df[attendance_col].dropna()
        if len(att_valid) > 0:
            result["avg_attendance"] = round(float(att_valid.mean()), 2)

    return result

def _empty_overall_stats(total: int) -> dict:
    return {
        "total_students":   total,
        "valid_students":   0,
        "overall_average":  None,
        "median_marks":     None,
        "highest_marks":    None,
        "lowest_marks":     None,
        "std_dev":          None,
        "pass_count":       0,
        "fail_count":       0,
        "pass_percentage":  None,
        "fail_percentage":  None,
        "avg_attendance":   None,
    }

# ── Subject-wise statistics ───────────────────────────────────────────────────

def compute_subject_stats(
    df: pd.DataFrame,
    subject_cols: list[str],
    passing_threshold: float = 40.0,
) -> pd.DataFrame:
    if not subject_cols:
        empty = pd.DataFrame(columns=[
            "Subject", "Average", "Median", "Highest", "Lowest",
            "Std_Dev", "Pass_Count", "Fail_Count", "Pass_Percentage", "Valid_Count",
        ])
        return empty.set_index("Subject")

    rows = []
    for col in subject_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        n = len(series)
        if n == 0:
            rows.append({
                "Subject":         col,
                "Average":         None,
                "Median":          None,
                "Highest":         None,
                "Lowest":          None,
                "Std_Dev":         None,
                "Pass_Count":      0,
                "Fail_Count":      0,
                "Pass_Percentage": None,
                "Valid_Count":     0,
            })
            continue

        pass_count = int((series >= passing_threshold).sum())
        rows.append({
            "Subject":         col,
            "Average":         round(float(series.mean()), 2),
            "Median":          round(float(series.median()), 2),
            "Highest":         round(float(series.max()), 2),
            "Lowest":          round(float(series.min()), 2),
            "Std_Dev":         round(float(series.std()), 2),
            "Pass_Count":      pass_count,
            "Fail_Count":      n - pass_count,
            "Pass_Percentage": round(pass_count / n * 100, 2),
            "Valid_Count":     n,
        })

    return pd.DataFrame(rows).set_index("Subject")

# ── Student ranking ───────────────────────────────────────────────────────────

def build_student_ranking(
    df: pd.DataFrame,
    subject_cols: list[str],
    avg_col: str,
    category_col: str,
    id_col: Optional[str] = None,
    name_col: Optional[str] = None,
    attendance_col: Optional[str] = None,
    passing_threshold: float = 40.0,
) -> pd.DataFrame:
    keep = []
    if id_col and id_col in df.columns:
        keep.append(id_col)
    if name_col and name_col in df.columns:
        keep.append(name_col)
    keep.extend(subject_cols)
    keep.append(avg_col)
    if attendance_col and attendance_col in df.columns:
        keep.append(attendance_col)
    keep.append(category_col)

    out = df[keep].copy()
    out = out.rename(columns={
        avg_col:      "Average_Marks",
        category_col: "Performance_Category",
    })
    if attendance_col and attendance_col in df.columns:
        out = out.rename(columns={attendance_col: "Attendance_%"})

    out["Pass_Fail"] = out["Average_Marks"].apply(
        lambda x: "Pass" if (pd.notna(x) and x >= passing_threshold) else "Fail"
    )

    out = out.sort_values("Average_Marks", ascending=False, na_position="last")
    out["Rank"] = out["Average_Marks"].rank(method="min", ascending=False).astype("Int64")

    cols_order = ["Rank"]
    if id_col and id_col in df.columns:
        cols_order.append(id_col)
    if name_col and name_col in df.columns:
        cols_order.append(name_col)
    cols_order.extend(subject_cols)
    cols_order.append("Average_Marks")
    if attendance_col and attendance_col in df.columns:
        cols_order.append("Attendance_%")
    cols_order.extend(["Pass_Fail", "Performance_Category"])

    return out[cols_order].reset_index(drop=True)

# ── Attendance correlation ────────────────────────────────────────────────────

def compute_attendance_correlation(
    df: pd.DataFrame,
    avg_col: str,
    attendance_col: str,
) -> Optional[float]:
    paired = df[[avg_col, attendance_col]].dropna()
    if len(paired) < 3:
        return None

    if paired[avg_col].std() == 0 or paired[attendance_col].std() == 0:
        return None

    corr = paired[avg_col].corr(paired[attendance_col])
    return round(float(corr), 4) if pd.notna(corr) else None

# ── Class / group comparison ──────────────────────────────────────────────────

def compute_class_comparison(
    df: pd.DataFrame,
    class_col: str,
    avg_col: str,
) -> pd.DataFrame:
    grouped = (
        df.groupby(class_col)[avg_col]
        .agg(Average_Marks="mean", Student_Count="count")
        .reset_index()
        .rename(columns={class_col: "Class"})
    )
    grouped["Average_Marks"] = grouped["Average_Marks"].round(2)
    return grouped.sort_values("Average_Marks", ascending=False).reset_index(drop=True)

# ── Filter application ────────────────────────────────────────────────────────

def apply_filters(
    df: pd.DataFrame,
    avg_col: str,
    category_col: Optional[str] = None,
    class_col: Optional[str] = None,
    attendance_col: Optional[str] = None,
    id_col: Optional[str] = None,
    name_col: Optional[str] = None,
    selected_classes: Optional[list] = None,
    selected_categories: Optional[list] = None,
    min_avg: Optional[float] = None,
    max_avg: Optional[float] = None,
    min_attendance: Optional[float] = None,
    search_term: Optional[str] = None,
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    if selected_classes and class_col and class_col in df.columns:
        mask &= df[class_col].isin(selected_classes)

    if selected_categories and category_col and category_col in df.columns:
        mask &= df[category_col].isin(selected_categories)

    if min_avg is not None:
        mask &= df[avg_col].fillna(-1) >= min_avg

    if max_avg is not None:
        mask &= df[avg_col].fillna(101) <= max_avg

    if min_attendance is not None and attendance_col and attendance_col in df.columns:
        mask &= df[attendance_col].fillna(-1) >= min_attendance

    if search_term and search_term.strip():
        term = search_term.strip().lower()
        text_mask = pd.Series(False, index=df.index)
        if name_col and name_col in df.columns:
            text_mask |= df[name_col].astype(str).str.lower().str.contains(term, na=False)
        if id_col and id_col in df.columns:
            text_mask |= df[id_col].astype(str).str.lower().str.contains(term, na=False)
        mask &= text_mask

    return df[mask].copy()
