
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

# ── Data quality report ───────────────────────────────────────────────────────

@dataclass
class DataQualityReport:

    total_rows: int = 0
    total_cols: int = 0
    missing_values: int = 0          # total NaN cells
    missing_by_column: dict = field(default_factory=dict)
    duplicate_rows: int = 0
    duplicate_id_rows: int = 0       # rows with repeated student IDs
    invalid_mark_cells: int = 0      # marks outside [0, 100]
    invalid_attendance_cells: int = 0
    valid_student_rows: int = 0      # rows usable for analysis
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_critical_errors(self) -> bool:
        return len(self.errors) > 0

# ── Main cleaning / validation functions ─────────────────────────────────────

def validate_and_clean(
    df: pd.DataFrame,
    subject_cols: list[str],
    attendance_col: Optional[str] = None,
    id_col: Optional[str] = None,
    drop_duplicates: bool = True,
    drop_incomplete: bool = False,
) -> tuple[pd.DataFrame, DataQualityReport]:
    report = DataQualityReport()
    cleaned = df.copy()

    report.total_rows = len(cleaned)
    report.total_cols = len(cleaned.columns)

    # ── 1. Empty dataset ──────────────────────────────────────────────────────
    if cleaned.empty:
        report.errors.append("The dataset contains no rows.")
        return cleaned, report

    # ── 2. Missing subject columns ────────────────────────────────────────────
    missing_cols = [c for c in subject_cols if c not in cleaned.columns]
    if missing_cols:
        report.errors.append(
            f"The following selected subject columns were not found in the dataset: "
            f"{missing_cols}"
        )
        return cleaned, report

    # ── 3. Count missing values ───────────────────────────────────────────────
    report.missing_values = int(cleaned.isnull().sum().sum())
    report.missing_by_column = cleaned.isnull().sum().to_dict()

    # ── 4. Coerce subject columns to numeric ──────────────────────────────────
    for col in subject_cols:
        original_non_null = cleaned[col].notna().sum()
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
        new_non_null = cleaned[col].notna().sum()
        coerced = int(original_non_null - new_non_null)
        if coerced > 0:
            report.warnings.append(
                f"Column '{col}': {coerced} non-numeric value(s) converted to NaN."
            )

    # ── 5. Detect marks outside [0, 100] ─────────────────────────────────────
    for col in subject_cols:
        out_of_range = cleaned[col].notna() & ~cleaned[col].between(0, 100)
        n_bad = int(out_of_range.sum())
        report.invalid_mark_cells += n_bad
        if n_bad > 0:
            report.warnings.append(
                f"Column '{col}': {n_bad} value(s) outside [0, 100] — set to NaN."
            )
            cleaned.loc[out_of_range, col] = np.nan

    # ── 6. Validate attendance ────────────────────────────────────────────────
    if attendance_col and attendance_col in cleaned.columns:
        cleaned[attendance_col] = pd.to_numeric(cleaned[attendance_col], errors="coerce")
        bad_att = cleaned[attendance_col].notna() & ~cleaned[attendance_col].between(0, 100)
        n_bad_att = int(bad_att.sum())
        report.invalid_attendance_cells = n_bad_att
        if n_bad_att > 0:
            report.warnings.append(
                f"Attendance column '{attendance_col}': {n_bad_att} value(s) outside "
                "[0, 100] — set to NaN."
            )
            cleaned.loc[bad_att, attendance_col] = np.nan

    # ── 7. Duplicate rows ─────────────────────────────────────────────────────
    dup_mask = cleaned.duplicated()
    report.duplicate_rows = int(dup_mask.sum())
    if report.duplicate_rows > 0:
        report.warnings.append(
            f"{report.duplicate_rows} exact duplicate row(s) detected."
        )
        if drop_duplicates:
            cleaned = cleaned[~dup_mask].reset_index(drop=True)

    # ── 8. Duplicate student IDs ──────────────────────────────────────────────
    if id_col and id_col in cleaned.columns:
        dup_ids = cleaned[id_col].duplicated(keep=False)
        report.duplicate_id_rows = int(dup_ids.sum())
        if report.duplicate_id_rows > 0:
            report.warnings.append(
                f"{report.duplicate_id_rows} row(s) share duplicate Student IDs."
            )

    # ── 9. Drop incomplete rows if requested ──────────────────────────────────
    if drop_incomplete:
        before = len(cleaned)
        cleaned = cleaned.dropna(subset=subject_cols).reset_index(drop=True)
        dropped = before - len(cleaned)
        if dropped > 0:
            report.warnings.append(
                f"{dropped} row(s) removed because one or more subject marks were missing."
            )

    # ── 10. Count valid rows ──────────────────────────────────────────────────
    # A row is "valid" if at least one subject column is non-NaN
    any_valid_mark = cleaned[subject_cols].notna().any(axis=1)
    report.valid_student_rows = int(any_valid_mark.sum())

    if report.valid_student_rows == 0:
        report.errors.append(
            "No valid student records remain after cleaning. "
            "Please check the selected subject columns."
        )

    return cleaned, report

def compute_average_marks(df: pd.DataFrame, subject_cols: list[str]) -> pd.Series:
    return df[subject_cols].mean(axis=1, skipna=True)

def categorise_performance(average_marks: pd.Series) -> pd.Series:
    def _cat(score):
        if pd.isna(score):
            return "No Data"
        if score >= 85:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 50:
            return "Average"
        if score >= 40:
            return "Needs Improvement"
        return "Below Threshold"

    return average_marks.map(_cat)

def flag_needs_support(
    df: pd.DataFrame,
    subject_cols: list[str],
    avg_col: str,
    passing_threshold: float = 40.0,
    subject_pass_threshold: float = 40.0,
    attendance_col: Optional[str] = None,
    attendance_threshold: float = 75.0,
) -> pd.DataFrame:
    out = df.copy()

    out["flag_overall_fail"] = out[avg_col] < passing_threshold

    # Subject-level: True if any subject mark < threshold (NaN is skipped)
    subject_fail = (out[subject_cols] < subject_pass_threshold).any(axis=1)
    # Students with all NaN subjects are not flagged as subject_fail
    all_nan_subjects = out[subject_cols].isna().all(axis=1)
    out["flag_subject_fail"] = subject_fail & ~all_nan_subjects

    if attendance_col and attendance_col in out.columns:
        out["flag_low_attendance"] = (
            out[attendance_col].notna() & (out[attendance_col] < attendance_threshold)
        )
    else:
        out["flag_low_attendance"] = False

    out["flag_any"] = (
        out["flag_overall_fail"]
        | out["flag_subject_fail"]
        | out["flag_low_attendance"]
    )

    return out
