
from __future__ import annotations

from typing import Optional

import pandas as pd

def generate_insights(
    overall_stats: dict,
    subject_stats: pd.DataFrame,
    passing_threshold: float,
    attendance_threshold: float,
    quality_warnings: list[str],
    attendance_col: Optional[str] = None,
) -> list[str]:
    insights: list[str] = []

    # ── 1. Dataset size ───────────────────────────────────────────────────────
    total = overall_stats.get("total_students", 0)
    valid = overall_stats.get("valid_students", 0)
    if total > 0:
        insights.append(f"📊 The dataset contains **{total}** student records, "
                         f"of which **{valid}** have valid marks for analysis.")

    # ── 2. Overall average ────────────────────────────────────────────────────
    avg = overall_stats.get("overall_average")
    if avg is not None:
        insights.append(f"📈 The overall average marks across all selected subjects "
                         f"is **{avg:.1f}** out of 100.")

    # ── 3. Pass / fail ────────────────────────────────────────────────────────
    pass_pct = overall_stats.get("pass_percentage")
    fail_count = overall_stats.get("fail_count", 0)
    if pass_pct is not None:
        insights.append(
            f"✅ **{pass_pct:.1f}%** of students meet the overall passing threshold "
            f"of {passing_threshold:.0f} marks. "
            f"**{fail_count}** student(s) are below this threshold."
        )

    # ── 4. Best and weakest subjects ──────────────────────────────────────────
    if not subject_stats.empty and "Average" in subject_stats.columns:
        valid_subjects = subject_stats["Average"].dropna()
        if len(valid_subjects) >= 2:
            best_subj = valid_subjects.idxmax()
            worst_subj = valid_subjects.idxmin()
            best_avg = valid_subjects.max()
            worst_avg = valid_subjects.min()
            insights.append(
                f"🏆 **{best_subj}** has the highest subject average "
                f"(**{best_avg:.1f}** marks)."
            )
            if worst_subj != best_subj:
                insights.append(
                    f"⚠️ **{worst_subj}** has the lowest subject average "
                    f"(**{worst_avg:.1f}** marks) — students in this subject may need "
                    "additional support."
                )
        elif len(valid_subjects) == 1:
            best_subj = valid_subjects.idxmax()
            insights.append(f"Only one subject has valid data: **{best_subj}**.")

    # ── 5. Subject with most failures ─────────────────────────────────────────
    if not subject_stats.empty and "Fail_Count" in subject_stats.columns:
        fail_counts = subject_stats["Fail_Count"].dropna()
        if len(fail_counts) > 0 and fail_counts.max() > 0:
            most_fail_subj = fail_counts.idxmax()
            most_fail_n = int(fail_counts.max())
            insights.append(
                f"📉 **{most_fail_subj}** has the highest failure count with "
                f"**{most_fail_n}** student(s) below the passing threshold."
            )

    # ── 6. Attendance ─────────────────────────────────────────────────────────
    avg_att = overall_stats.get("avg_attendance")
    if attendance_col and avg_att is not None:
        insights.append(
            f"🗓️ Average class attendance is **{avg_att:.1f}%**."
        )
        if avg_att < attendance_threshold:
            insights.append(
                f"⚠️ Average attendance ({avg_att:.1f}%) is below the configured "
                f"threshold of {attendance_threshold:.0f}%. This may indicate a "
                "systemic attendance issue."
            )
    elif not attendance_col:
        insights.append(
            "ℹ️ Attendance data was not supplied — attendance analysis is unavailable."
        )

    # ── 7. Score spread ───────────────────────────────────────────────────────
    std_dev = overall_stats.get("std_dev")
    if std_dev is not None:
        if std_dev > 20:
            insights.append(
                f"📊 The standard deviation of average marks is **{std_dev:.1f}**, "
                "indicating a wide spread of performance levels."
            )
        elif std_dev < 5:
            insights.append(
                f"📊 The standard deviation of average marks is **{std_dev:.1f}**, "
                "suggesting most students have very similar performance levels."
            )

    # ── 8. Data quality ───────────────────────────────────────────────────────
    if quality_warnings:
        insights.append(
            f"🔍 **{len(quality_warnings)}** data quality warning(s) were detected "
            "during validation — see the Data Quality tab for details."
        )

    return insights

def generate_attention_insights(
    flagged_df: pd.DataFrame,
    total_students: int,
) -> list[str]:
    insights: list[str] = []
    n_flagged = len(flagged_df)

    if total_students == 0:
        return ["No student data available."]

    if n_flagged == 0:
        insights.append(
            "✅ No students are currently flagged for additional academic support "
            "under the active criteria."
        )
        return insights

    pct = round(n_flagged / total_students * 100, 1)
    insights.append(
        f"🔴 **{n_flagged}** student(s) (**{pct}%** of the dataset) are flagged for "
        "possible academic support."
    )

    if "flag_overall_fail" in flagged_df.columns:
        n_overall = int(flagged_df["flag_overall_fail"].sum())
        if n_overall > 0:
            insights.append(
                f"  • **{n_overall}** student(s) have an average below the passing threshold."
            )

    if "flag_subject_fail" in flagged_df.columns:
        n_subj = int(flagged_df["flag_subject_fail"].sum())
        if n_subj > 0:
            insights.append(
                f"  • **{n_subj}** student(s) failed at least one subject."
            )

    if "flag_low_attendance" in flagged_df.columns:
        n_att = int(flagged_df["flag_low_attendance"].sum())
        if n_att > 0:
            insights.append(
                f"  • **{n_att}** student(s) have attendance below the configured threshold."
            )

    return insights
