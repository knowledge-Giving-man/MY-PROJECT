
from __future__ import annotations

import io
import sys
import os
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

# ── Ensure src/ is importable when running from the project root ──────────────
sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import (
    load_sample_dataset,
    load_uploaded_file,
    auto_detect_columns,
)
from src.data_cleaning import (
    validate_and_clean,
    compute_average_marks,
    categorise_performance,
    flag_needs_support,
)
from src.analytics import (
    compute_overall_stats,
    compute_subject_stats,
    build_student_ranking,
    compute_attendance_correlation,
    compute_class_comparison,
    apply_filters,
)
from src.insights import generate_insights, generate_attention_insights
from src import visualizations as viz

# ─────────────────────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Student Performance Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — minimal, professional polish only
# ─────────────────────────────────────────────────────────────────────────────

_CSS = (
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');"
    "html,body,[class*='css']{font-family:'Inter',sans-serif;}"
    ":root{"
    "--accent:#3b82f6;--accent-light:rgba(59,130,246,0.12);--accent-text:#2563eb;"
    "--success:#16a34a;--success-light:rgba(22,163,74,0.12);--danger:#dc2626;"
    "--bg-card:light-dark(#f8fafc,#1e293b);"
    "--border-card:light-dark(#e2e8f0,#334155);"
    "--shadow-card:light-dark(0 1px 4px rgba(0,0,0,0.06),0 1px 4px rgba(0,0,0,0.4));"
    "}"
    "[data-testid='stSidebar']{background:linear-gradient(180deg,#0f172a 0%,#1e293b 100%) !important;}"
    "[data-testid='stSidebar'],[data-testid='stSidebar'] *{color:#e2e8f0 !important;}"
    "[data-testid='stSidebar'] .stSelectbox label,"
    "[data-testid='stSidebar'] .stMultiSelect label,"
    "[data-testid='stSidebar'] .stSlider label,"
    "[data-testid='stSidebar'] .stNumberInput label,"
    "[data-testid='stSidebar'] .stTextInput label,"
    "[data-testid='stSidebar'] .stCheckbox label{"
    "color:#94a3b8 !important;font-size:0.78rem;font-weight:600;"
    "text-transform:uppercase;letter-spacing:0.05em;}"
    "[data-testid='stSidebar'] h2,[data-testid='stSidebar'] h3{color:#f1f5f9 !important;}"
    "[data-testid='stSidebar'] .stRadio label{color:#cbd5e1 !important;font-size:0.9rem;}"
    "[data-testid='stSidebar'] .stRadio > div > label{color:#cbd5e1 !important;}"
    "[data-testid='stSidebar'] hr{border-color:#334155 !important;}"
    "[data-testid='stSidebar'] .stButton > button{background:#3b82f6;color:#ffffff !important;border:none;font-weight:600;}"
    "[data-testid='stSidebar'] .stButton > button:hover{background:#2563eb;}"
    ".kpi-card{"
    "background:rgba(125,125,125,0.06);background:var(--bg-card);"
    "border-radius:14px;padding:20px 24px;"
    "border:1px solid rgba(125,125,125,0.15);border:1px solid var(--border-card);"
    "box-shadow:var(--shadow-card);text-align:center;height:100%;"
    "}"
    ".kpi-label{font-size:0.72rem;font-weight:700;color:inherit;opacity:0.65;"
    "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;}"
    ".kpi-value{font-size:2.1rem;font-weight:800;color:inherit;line-height:1.1;}"
    ".kpi-sub{font-size:0.75rem;color:inherit;opacity:0.65;margin-top:4px;}"
    ".section-header{font-size:1.1rem;font-weight:700;color:inherit;"
    "padding:4px 0 10px 0;border-bottom:2px solid var(--accent);margin-bottom:18px;}"
    ".badge-sample{background:var(--accent-light);color:var(--accent-text);"
    "padding:4px 12px;border-radius:999px;font-size:0.73rem;font-weight:700;}"
    ".badge-uploaded{background:var(--success-light);color:var(--success);"
    "padding:4px 12px;border-radius:999px;font-size:0.73rem;font-weight:700;}"
    ".insight-box{background:rgba(59,130,246,0.08);border-left:4px solid var(--accent);"
    "border-radius:8px;padding:12px 16px;margin-bottom:10px;"
    "font-size:0.91rem;color:inherit;line-height:1.6;}"
    ".page-title{font-size:1.9rem;font-weight:800;color:inherit;margin-bottom:2px;}"
    ".page-subtitle{color:inherit;opacity:0.75;font-size:0.95rem;margin-top:0;}"
    ".legend-item{display:inline-flex;align-items:center;gap:6px;"
    "margin-right:14px;font-size:0.8rem;color:inherit;opacity:0.85;}"
    ".legend-dot{width:12px;height:12px;border-radius:50%;display:inline-block;flex-shrink:0;}"
    ".attention-metric{color:var(--danger) !important;font-weight:700;}"
    "[data-testid='stTabs'] [role='tab']{font-weight:500;}"
    "[data-testid='stTabs'] [role='tab'][aria-selected='true']"
    "{color:var(--accent) !important;font-weight:700;border-bottom-color:var(--accent) !important;}"
    "[data-testid='stExpander'] summary{font-weight:600;}"
    "</style>"
)

st.markdown(_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session-state initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_session_state():
    defaults = {
        "raw_df":            None,
        "clean_df":          None,
        "quality_report":    None,
        "col_map":           {},
        "subject_cols":      [],
        "passing_threshold": 40.0,
        "attend_threshold":  75.0,
        "top_n":             10,
        "drop_incomplete":   False,
        "data_source":       "Sample Dataset",
        "dataset_name":      "",
        "filters_reset":     False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session_state()

# ─────────────────────────────────────────────────────────────────────────────
# Helper: load and process dataset
# ─────────────────────────────────────────────────────────────────────────────

def process_dataset(
    raw_df: pd.DataFrame,
    col_map: dict,
    subject_cols: list[str],
    passing_threshold: float,
    attend_threshold: float,
    drop_incomplete: bool,
) -> tuple[pd.DataFrame, object]:
    attendance_col = col_map.get("attendance_col")
    id_col         = col_map.get("id_col")

    cleaned, report = validate_and_clean(
        raw_df,
        subject_cols=subject_cols,
        attendance_col=attendance_col,
        id_col=id_col,
        drop_duplicates=True,
        drop_incomplete=drop_incomplete,
    )

    if report.has_critical_errors or cleaned.empty or not subject_cols:
        return cleaned, report

    # Add computed columns
    cleaned["_avg_marks"]    = compute_average_marks(cleaned, subject_cols)
    cleaned["_category"]     = categorise_performance(cleaned["_avg_marks"])
    cleaned = flag_needs_support(
        cleaned,
        subject_cols=subject_cols,
        avg_col="_avg_marks",
        passing_threshold=passing_threshold,
        subject_pass_threshold=passing_threshold,
        attendance_col=attendance_col,
        attendance_threshold=attend_threshold,
    )
    return cleaned, report

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 Student Performance\nAnalyser")
    st.markdown("---")

    # ── Dataset source selection ──────────────────────────────────────────────
    st.markdown("### 📂 Data Source")
    data_source = st.radio(
        "Choose data source",
        ["Sample Dataset", "Upload CSV / Excel"],
        index=0 if st.session_state["data_source"] == "Sample Dataset" else 1,
        key="data_source_radio",
        label_visibility="collapsed",
    )
    st.session_state["data_source"] = data_source

    if data_source == "Sample Dataset":
        if st.button("📥 Load Sample Dataset", use_container_width=True):
            with st.spinner("Loading sample dataset…"):
                try:
                    raw = load_sample_dataset()
                    detected = auto_detect_columns(raw)
                    subj = detected.get("subject_cols", [])
                    st.session_state.update({
                        "raw_df":        raw,
                        "col_map":       detected,
                        "subject_cols":  subj,
                        "dataset_name":  "sample_students.csv (Synthetic Data)",
                    })
                    st.success(f"✅ Loaded {len(raw)} records")
                except Exception as e:
                    st.error(f"Failed to load sample data: {e}")

    else:
        uploaded = st.file_uploader(
            "Upload student CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="file_uploader",
        )
        if uploaded:
            with st.spinner("Reading file…"):
                raw, err = load_uploaded_file(uploaded)
            if err:
                st.error(err)
            else:
                detected = auto_detect_columns(raw)
                subj = detected.get("subject_cols", [])
                st.session_state.update({
                    "raw_df":        raw,
                    "col_map":       detected,
                    "subject_cols":  subj,
                    "dataset_name":  uploaded.name,
                })
                st.success(f"✅ Loaded {len(raw)} records")

    st.markdown("---")

    # ── Column mapping (shown after data is loaded) ───────────────────────────
    if st.session_state["raw_df"] is not None:
        raw_df = st.session_state["raw_df"]
        col_map = st.session_state["col_map"]
        all_cols = raw_df.columns.tolist()
        numeric_cols = [c for c in all_cols if pd.api.types.is_numeric_dtype(raw_df[c])]

        st.markdown("### 🗂️ Column Mapping")
        with st.expander("Configure columns", expanded=(data_source == "Upload CSV / Excel")):
            col_map["id_col"] = st.selectbox(
                "Student ID column",
                [None] + all_cols,
                index=([None] + all_cols).index(col_map.get("id_col"))
                      if col_map.get("id_col") in all_cols else 0,
                format_func=lambda x: "(none)" if x is None else x,
            )
            col_map["name_col"] = st.selectbox(
                "Student Name column",
                [None] + all_cols,
                index=([None] + all_cols).index(col_map.get("name_col"))
                      if col_map.get("name_col") in all_cols else 0,
                format_func=lambda x: "(none)" if x is None else x,
            )
            col_map["class_col"] = st.selectbox(
                "Class / Group column",
                [None] + all_cols,
                index=([None] + all_cols).index(col_map.get("class_col"))
                      if col_map.get("class_col") in all_cols else 0,
                format_func=lambda x: "(none)" if x is None else x,
            )
            col_map["attendance_col"] = st.selectbox(
                "Attendance column",
                [None] + all_cols,
                index=([None] + all_cols).index(col_map.get("attendance_col"))
                      if col_map.get("attendance_col") in all_cols else 0,
                format_func=lambda x: "(none)" if x is None else x,
            )
            # Subject columns — multi-select from numeric columns
            default_subjects = [
                c for c in col_map.get("subject_cols", []) if c in numeric_cols
            ]
            selected_subjects = st.multiselect(
                "Subject columns (marks)",
                options=numeric_cols,
                default=default_subjects,
            )
            st.session_state["subject_cols"] = selected_subjects
            st.session_state["col_map"] = col_map

        # ── Thresholds ────────────────────────────────────────────────────────
        st.markdown("### ⚙️ Thresholds")
        passing_threshold = st.slider(
            "Passing threshold (marks)",
            min_value=1, max_value=80,
            value=int(st.session_state["passing_threshold"]),
            step=1,
        )
        st.session_state["passing_threshold"] = float(passing_threshold)

        attend_threshold = st.slider(
            "Attendance threshold (%)",
            min_value=1, max_value=100,
            value=int(st.session_state["attend_threshold"]),
            step=1,
        )
        st.session_state["attend_threshold"] = float(attend_threshold)

        top_n = st.slider(
            "Top students to show",
            min_value=3, max_value=min(50, len(raw_df)),
            value=min(10, len(raw_df)),
            step=1,
        )
        st.session_state["top_n"] = top_n

        drop_incomplete = st.checkbox(
            "Exclude rows with any missing marks",
            value=st.session_state["drop_incomplete"],
        )
        st.session_state["drop_incomplete"] = drop_incomplete

        st.markdown("---")

        # ── Filters ───────────────────────────────────────────────────────────
        st.markdown("### 🔍 Filters")
        class_col = col_map.get("class_col")
        selected_classes = None
        if class_col and class_col in raw_df.columns:
            class_options = sorted(raw_df[class_col].dropna().unique().tolist())
            selected_classes = st.multiselect(
                "Class / Group",
                options=class_options,
                default=class_options,
            )

        category_options = [
            "Excellent", "Good", "Average", "Needs Improvement",
            "Below Threshold", "No Data",
        ]
        selected_categories = st.multiselect(
            "Performance category",
            options=category_options,
            default=category_options,
        )

        avg_min = st.number_input("Min average marks", min_value=0.0, max_value=100.0,
                                   value=0.0, step=1.0)
        avg_max = st.number_input("Max average marks", min_value=0.0, max_value=100.0,
                                   value=100.0, step=1.0)

        min_attendance_filter = None
        attendance_col = col_map.get("attendance_col")
        if attendance_col and attendance_col in raw_df.columns:
            min_attendance_filter = st.slider(
                "Min attendance (%)", min_value=0, max_value=100, value=0, step=1
            )

        search_term = st.text_input("🔎 Search student (name or ID)", value="")

        if st.button("↩️ Reset Filters", use_container_width=True):
            st.rerun()

        st.markdown("---")
        st.markdown(
            f"<div style='font-size:0.75rem;color:#94a3b8;'>Dataset: "
            f"{st.session_state.get('dataset_name','—')}</div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# Main content area
# ─────────────────────────────────────────────────────────────────────────────

# ── Page header ───────────────────────────────────────────────────────────────
header_col, badge_col = st.columns([3, 1])
with header_col:
    st.markdown(
        "<h1 class='page-title'>🎓 Student Performance Analysis Dashboard</h1>"
        "<p class='page-subtitle'>Transforming academic data into meaningful insights.</p>",
        unsafe_allow_html=True,
    )
with badge_col:
    src = st.session_state.get("data_source", "Sample Dataset")
    badge_class = "badge-sample" if src == "Sample Dataset" else "badge-uploaded"
    badge_text  = "📋 Sample Data" if src == "Sample Dataset" else "📤 Uploaded Data"
    st.markdown(
        f"<div style='text-align:right;padding-top:16px;'>"
        f"<span class='{badge_class}'>{badge_text}</span></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# No data loaded state
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state["raw_df"] is None:
    st.info(
        "👈 **Get started:** Select a data source in the sidebar and click "
        "**Load Sample Dataset**, or upload your own CSV / Excel file.",
        icon="ℹ️",
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Data processing
# ─────────────────────────────────────────────────────────────────────────────

raw_df            = st.session_state["raw_df"]
col_map           = st.session_state["col_map"]
subject_cols      = st.session_state["subject_cols"]
passing_threshold = st.session_state["passing_threshold"]
attend_threshold  = st.session_state["attend_threshold"]
top_n             = st.session_state["top_n"]
drop_incomplete   = st.session_state["drop_incomplete"]

if not subject_cols:
    st.warning(
        "⚠️ No subject columns selected. "
        "Please open **Configure columns** in the sidebar and select at least one "
        "subject column (marks column).",
        icon="⚠️",
    )
    st.stop()

# Clean / validate
with st.spinner("Processing dataset…"):
    clean_df, quality_report = process_dataset(
        raw_df, col_map, subject_cols,
        passing_threshold, attend_threshold, drop_incomplete,
    )

# Halt on critical error
if quality_report.has_critical_errors:
    for err in quality_report.errors:
        st.error(f"❌ {err}")
    st.stop()

# Apply filters
attendance_col = col_map.get("attendance_col")
id_col         = col_map.get("id_col")
name_col       = col_map.get("name_col")
class_col      = col_map.get("class_col")

filtered_df = apply_filters(
    clean_df,
    avg_col            = "_avg_marks",
    category_col       = "_category",
    class_col          = class_col,
    attendance_col     = attendance_col,
    id_col             = id_col,
    name_col           = name_col,
    selected_classes   = selected_classes if "selected_classes" in dir() else None,
    selected_categories= selected_categories if "selected_categories" in dir() else None,
    min_avg            = avg_min if "avg_min" in dir() else None,
    max_avg            = avg_max if "avg_max" in dir() else None,
    min_attendance     = min_attendance_filter if "min_attendance_filter" in dir() else None,
    search_term        = search_term if "search_term" in dir() else None,
)

n_filtered = len(filtered_df)

# ─────────────────────────────────────────────────────────────────────────────
# Overall statistics (on filtered data)
# ─────────────────────────────────────────────────────────────────────────────

overall_stats  = compute_overall_stats(
    filtered_df, "_avg_marks", passing_threshold, attendance_col
)
subject_stats  = compute_subject_stats(filtered_df, subject_cols, passing_threshold)

# ─────────────────────────────────────────────────────────────────────────────
# KPI Cards
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    f"<p style='color:inherit;opacity:0.65;font-size:0.85rem;margin-bottom:12px;'>"
    f"Showing <b>{n_filtered}</b> of <b>{len(clean_df)}</b> records after filters</p>",
    unsafe_allow_html=True,
)

kpi_cols = st.columns(5)

def _kpi(col, label, value, sub="", value_color=None):
    val_style = f" style='color:{value_color};'" if value_color else ""
    col.markdown(
        f"<div class='kpi-card'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'{val_style}>{value}</div>"
        f"<div class='kpi-sub'>{sub}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

total_students = overall_stats["total_students"]
overall_avg    = overall_stats["overall_average"]
pass_pct       = overall_stats["pass_percentage"]
avg_att        = overall_stats["avg_attendance"]

# Attention count (on filtered_df)
attention_count = int(filtered_df["flag_any"].sum()) if "flag_any" in filtered_df.columns else 0

_kpi(kpi_cols[0], "Total Students",       str(total_students),
     f"{overall_stats['valid_students']} with valid marks")
_kpi(kpi_cols[1], "Overall Average",
     f"{overall_avg:.1f}" if overall_avg is not None else "—",
     "marks out of 100")
_kpi(kpi_cols[2], "Pass Percentage",
     f"{pass_pct:.1f}%" if pass_pct is not None else "—",
     f"threshold: {passing_threshold:.0f} marks",
     value_color="var(--success)" if (pass_pct or 0) >= 60 else "var(--danger)")
_kpi(kpi_cols[3], "Need Support",
     str(attention_count),
     "students flagged",
     value_color="var(--danger)" if attention_count > 0 else "var(--success)")
_kpi(kpi_cols[4], "Avg Attendance",
     f"{avg_att:.1f}%" if avg_att is not None else "—",
     "when data available" if avg_att is None else
     ("✅ above threshold" if avg_att >= attend_threshold else "⚠️ below threshold"),
     value_color="var(--success)" if (avg_att or 0) >= attend_threshold else "var(--danger)")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Main tabs
# ─────────────────────────────────────────────────────────────────────────────

tab_overview, tab_subjects, tab_students, tab_attention, tab_attendance, \
    tab_insights, tab_quality, tab_export = st.tabs([
    " Overview",
    " Subjects",
    " Students",
    " Needs Support",
    " Attendance",
    " Insights",
    " Data Quality",
    " Export",
])

# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: Overview
# ─────────────────────────────────────────────────────────────────────────────

with tab_overview:
    if filtered_df.empty:
        st.warning("No records match the current filters.")
    else:
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("<div class='section-header'>Marks Distribution</div>",
                        unsafe_allow_html=True)
            st.plotly_chart(
                viz.marks_distribution_histogram(filtered_df, "_avg_marks"),
                use_container_width=True,
            )
        with row1_col2:
            st.markdown("<div class='section-header'>Pass vs. Fail</div>",
                        unsafe_allow_html=True)
            st.plotly_chart(
                viz.pass_fail_donut(overall_stats),
                use_container_width=True,
            )

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("<div class='section-header'>Performance Categories</div>",
                        unsafe_allow_html=True)
            st.plotly_chart(
                viz.performance_category_chart(filtered_df, "_category"),
                use_container_width=True,
            )
        with row2_col2:
            if class_col and class_col in filtered_df.columns:
                class_comp = compute_class_comparison(filtered_df, class_col, "_avg_marks")
                st.markdown("<div class='section-header'>Class Comparison</div>",
                            unsafe_allow_html=True)
                st.plotly_chart(
                    viz.class_comparison_bar(class_comp),
                    use_container_width=True,
                )
            else:
                st.markdown("<div class='section-header'>Class Comparison</div>",
                            unsafe_allow_html=True)
                st.info("No class/group column configured. Set it in sidebar → Configure columns.")

        # ── Top students ──────────────────────────────────────────────────────
        st.markdown("<div class='section-header'>Top Students</div>",
                    unsafe_allow_html=True)
        st.plotly_chart(
            viz.top_students_bar(filtered_df, "_avg_marks", name_col, id_col, top_n),
            use_container_width=True,
        )

        # ── Performance category legend ───────────────────────────────────────
        from src.visualizations import CATEGORY_COLORS
        legend_html = "<div style='margin-top:8px;'>"
        for cat, color in CATEGORY_COLORS.items():
            legend_html += (
                f"<span class='legend-item'>"
                f"<span class='legend-dot' style='background:{color};'></span>"
                f"{cat}</span>"
            )
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tab 2: Subjects
# ─────────────────────────────────────────────────────────────────────────────

with tab_subjects:
    if filtered_df.empty:
        st.warning("No records match the current filters.")
    else:
        st.markdown("<div class='section-header'>Subject Performance Comparison</div>",
                    unsafe_allow_html=True)
        st.plotly_chart(
            viz.subject_performance_bar(subject_stats),
            use_container_width=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<div class='section-header'>Subject Pass / Fail Counts</div>",
                        unsafe_allow_html=True)
            st.plotly_chart(
                viz.subject_pass_fail_bar(subject_stats),
                use_container_width=True,
            )
        with col_b:
            st.markdown("<div class='section-header'>Subject Statistics Table</div>",
                        unsafe_allow_html=True)
            display_stats = subject_stats.reset_index().rename(columns={
                "Average":         "Avg",
                "Median":          "Median",
                "Highest":         "Max",
                "Lowest":          "Min",
                "Std_Dev":         "Std Dev",
                "Pass_Count":      "Pass",
                "Fail_Count":      "Fail",
                "Pass_Percentage": "Pass %",
                "Valid_Count":     "N",
            })
            st.dataframe(display_stats, use_container_width=True, hide_index=True)

        # Best / worst subject callout
        valid_avgs = subject_stats["Average"].dropna()
        if len(valid_avgs) >= 2:
            best  = valid_avgs.idxmax()
            worst = valid_avgs.idxmin()
            c1, c2 = st.columns(2)
            c1.success(f"🏆 **Best Subject:** {best} ({valid_avgs.max():.1f} avg)")
            c2.error(f"⚠️ **Weakest Subject:** {worst} ({valid_avgs.min():.1f} avg)")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: Students
# ─────────────────────────────────────────────────────────────────────────────

with tab_students:
    if filtered_df.empty:
        st.warning("No records match the current filters.")
    else:
        ranking_df = build_student_ranking(
            filtered_df,
            subject_cols=subject_cols,
            avg_col="_avg_marks",
            category_col="_category",
            id_col=id_col,
            name_col=name_col,
            attendance_col=attendance_col,
            passing_threshold=passing_threshold,
        )

        st.markdown(
            f"<div class='section-header'>Student Rankings "
            f"<span style='font-weight:400;color:inherit;opacity:0.65;font-size:0.85rem;'>"
            f"— {len(ranking_df)} records</span></div>",
            unsafe_allow_html=True,
        )

        # Highlight pass/fail
        def _highlight_pass_fail(row):
            if row.get("Pass_Fail") == "Pass":
                return ["background-color:rgba(34, 197, 94, 0.15)"] * len(row)
            if row.get("Pass_Fail") == "Fail":
                return ["background-color:rgba(239, 68, 68, 0.15)"] * len(row)
            return [""] * len(row)

        styled = ranking_df.style.apply(_highlight_pass_fail, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True, height=460)

# ─────────────────────────────────────────────────────────────────────────────
# Tab 4: Needs Support
# ─────────────────────────────────────────────────────────────────────────────

with tab_attention:
    st.markdown(
        "<div class='section-header'>Students Who May Need Academic Support</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "These are indicators for further review — not judgments about a student's ability. "
        "Multiple criteria may flag the same student."
    )

    if "flag_any" not in filtered_df.columns:
        st.info("Run analysis first.")
    else:
        flagged_all = filtered_df[filtered_df["flag_any"]].copy()
        attention_insights = generate_attention_insights(flagged_all, len(filtered_df))
        for ins in attention_insights:
            st.markdown(f"<div class='insight-box'>{ins}</div>", unsafe_allow_html=True)

        # Separate tabs per criterion
        at1, at2, at3 = st.tabs([
            "Below Overall Threshold",
            "Failing a Subject",
            "Low Attendance",
        ])

        cols_to_show = []
        if id_col and id_col in filtered_df.columns:     cols_to_show.append(id_col)
        if name_col and name_col in filtered_df.columns: cols_to_show.append(name_col)
        if class_col and class_col in filtered_df.columns: cols_to_show.append(class_col)
        cols_to_show.extend(subject_cols)
        cols_to_show.append("_avg_marks")
        cols_to_show.append("_category")
        if attendance_col and attendance_col in filtered_df.columns:
            cols_to_show.append(attendance_col)

        def _show_table(df_sub, flag_col):
            df_show = df_sub[df_sub[flag_col]][cols_to_show].copy()
            df_show = df_show.rename(columns={"_avg_marks": "Average", "_category": "Category"})
            df_show = df_show.sort_values("Average", ascending=True)
            if df_show.empty:
                st.success("✅ No students flagged under this criterion.")
            else:
                st.dataframe(df_show, use_container_width=True, hide_index=True)
                st.caption(f"{len(df_show)} student(s) listed above.")

        with at1:
            _show_table(filtered_df, "flag_overall_fail")
        with at2:
            _show_table(filtered_df, "flag_subject_fail")
        with at3:
            if attendance_col and attendance_col in filtered_df.columns:
                _show_table(filtered_df, "flag_low_attendance")
            else:
                st.info("Attendance data was not supplied — low-attendance flagging is unavailable.")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 5: Attendance
# ─────────────────────────────────────────────────────────────────────────────

with tab_attendance:
    if not attendance_col or attendance_col not in filtered_df.columns:
        st.info(
            "📋 Attendance data is not available in the current dataset. "
            "Select the attendance column in **Sidebar → Configure columns** "
            "to enable this section.",
            icon="ℹ️",
        )
    elif filtered_df.empty:
        st.warning("No records match the current filters.")
    else:
        corr = compute_attendance_correlation(filtered_df, "_avg_marks", attendance_col)
        c1, c2, c3 = st.columns(3)

        att_series = filtered_df[attendance_col].dropna()
        avg_att_filtered = att_series.mean() if len(att_series) > 0 else None
        low_att = (att_series < attend_threshold).sum() if len(att_series) > 0 else 0

        with c1:
            st.metric("Average Attendance",
                       f"{avg_att_filtered:.1f}%" if avg_att_filtered is not None else "—")
        with c2:
            st.metric("Below Threshold",
                       str(int(low_att)),
                       delta=f"< {attend_threshold:.0f}%",
                       delta_color="inverse")
        with c3:
            if corr is not None:
                st.metric("Corr. with Marks",
                           f"{corr:.3f}",
                           help="Pearson correlation between attendance and average marks.")
            else:
                st.metric("Corr. with Marks", "—",
                           help="Insufficient data to calculate correlation.")

        st.markdown("<div class='section-header'>Attendance vs. Average Marks</div>",
                    unsafe_allow_html=True)
        st.plotly_chart(
            viz.attendance_vs_marks_scatter(
                filtered_df, "_avg_marks", attendance_col, "_category", name_col
            ),
            use_container_width=True,
        )
        if corr is not None:
            direction = "positive" if corr > 0 else "negative"
            strength  = "strong" if abs(corr) > 0.6 else ("moderate" if abs(corr) > 0.3 else "weak")
            st.caption(
                f"ℹ️ The Pearson correlation between attendance and average marks is "
                f"**{corr:.3f}** ({strength} {direction} relationship). "
                "Correlation does not imply causation."
            )

# ─────────────────────────────────────────────────────────────────────────────
# Tab 6: Insights
# ─────────────────────────────────────────────────────────────────────────────

with tab_insights:
    st.markdown("<div class='section-header'>Key Insights</div>",
                unsafe_allow_html=True)
    st.caption(
        "All observations below are derived algorithmically from the current dataset. "
        "No AI service is used."
    )

    if filtered_df.empty:
        st.warning("No records match the current filters — no insights available.")
    else:
        insights_list = generate_insights(
            overall_stats=overall_stats,
            subject_stats=subject_stats,
            passing_threshold=passing_threshold,
            attendance_threshold=attend_threshold,
            quality_warnings=quality_report.warnings,
            attendance_col=attendance_col,
        )
        for ins in insights_list:
            st.markdown(f"<div class='insight-box'>{ins}</div>",
                        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tab 7: Data Quality
# ─────────────────────────────────────────────────────────────────────────────

with tab_quality:
    st.markdown("<div class='section-header'>Data Quality Report</div>",
                unsafe_allow_html=True)
    q = quality_report

    qc1, qc2, qc3, qc4 = st.columns(4)
    qc1.metric("Total Rows",        q.total_rows)
    qc2.metric("Total Columns",     q.total_cols)
    qc3.metric("Missing Values",    q.missing_values)
    qc4.metric("Duplicate Rows",    q.duplicate_rows)

    qc5, qc6, qc7, qc8 = st.columns(4)
    qc5.metric("Invalid Marks",     q.invalid_mark_cells)
    qc6.metric("Invalid Attendance",q.invalid_attendance_cells)
    qc7.metric("Duplicate IDs",     q.duplicate_id_rows)
    qc8.metric("Valid Records",     q.valid_student_rows)

    if q.warnings:
        st.markdown("**⚠️ Warnings**")
        for w in q.warnings:
            st.warning(w)
    if q.errors:
        st.markdown("**❌ Errors**")
        for e in q.errors:
            st.error(e)
    if not q.warnings and not q.errors:
        st.success("✅ No data quality issues detected.")

    # Missing values per column
    if q.missing_by_column:
        missing_data = {k: v for k, v in q.missing_by_column.items() if v > 0}
        if missing_data:
            st.markdown("**Missing Values by Column**")
            missing_df = pd.DataFrame(
                list(missing_data.items()), columns=["Column", "Missing Count"]
            ).sort_values("Missing Count", ascending=False)
            st.dataframe(missing_df, use_container_width=True, hide_index=True)

    # Raw data preview
    with st.expander("📋 Raw Data Preview (first 50 rows)"):
        st.dataframe(raw_df.head(50), use_container_width=True)

    # Cleaned data preview
    with st.expander("✅ Cleaned Data Preview (first 50 rows)"):
        preview_cols = [c for c in clean_df.columns if not c.startswith("flag_")]
        st.dataframe(clean_df[preview_cols].head(50), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tab 8: Export
# ─────────────────────────────────────────────────────────────────────────────

with tab_export:
    st.markdown("<div class='section-header'>Download Results</div>",
                unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("No records match the current filters.")
    else:
        # ── A. Cleaned dataset ────────────────────────────────────────────────
        st.markdown("**A. Cleaned Dataset**")
        clean_export = clean_df[[c for c in clean_df.columns if not c.startswith("flag_")]].copy()
        clean_csv = clean_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Cleaned Dataset (CSV)",
            data=clean_csv,
            file_name="cleaned_students.csv",
            mime="text/csv",
        )

        st.divider()

        # ── B. Student Performance Report ────────────────────────────────────
        st.markdown("**B. Student Performance Report**")
        ranking_export = build_student_ranking(
            filtered_df, subject_cols, "_avg_marks", "_category",
            id_col, name_col, attendance_col, passing_threshold
        )
        ranking_csv = ranking_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Performance Report (CSV)",
            data=ranking_csv,
            file_name="student_performance_report.csv",
            mime="text/csv",
        )

        st.divider()

        # ── C. Subject Summary ───────────────────────────────────────────────
        st.markdown("**C. Subject Summary**")
        subj_export = subject_stats.reset_index()
        subj_csv    = subj_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Subject Summary (CSV)",
            data=subj_csv,
            file_name="subject_summary.csv",
            mime="text/csv",
        )

        st.divider()

        # ── D. Analysis Summary (Markdown) ───────────────────────────────────
        st.markdown("**D. Analysis Summary (Markdown)**")

        now_str    = datetime.now().strftime("%Y-%m-%d %H:%M")
        dataset_nm = st.session_state.get("dataset_name", "Unknown")

        summary_lines = [
            f"# Student Performance Analysis Summary",
            f"",
            f"**Generated:** {now_str}",
            f"**Dataset:** {dataset_nm}",
            f"**Records Analysed:** {overall_stats['valid_students']} "
            f"(of {overall_stats['total_students']} total)",
            f"**Selected Subjects:** {', '.join(subject_cols)}",
            f"**Passing Threshold:** {passing_threshold:.0f} marks",
            f"",
            f"---",
            f"",
            f"## Overall Statistics",
            f"",
            f"| Metric | Value |",
            f"| --- | --- |",
            f"| Overall Average | {overall_stats['overall_average']:.2f} |" if overall_stats['overall_average'] else "| Overall Average | — |",
            f"| Median Marks | {overall_stats['median_marks']:.2f} |" if overall_stats['median_marks'] else "| Median Marks | — |",
            f"| Highest Marks | {overall_stats['highest_marks']:.2f} |" if overall_stats['highest_marks'] else "| Highest Marks | — |",
            f"| Lowest Marks | {overall_stats['lowest_marks']:.2f} |" if overall_stats['lowest_marks'] else "| Lowest Marks | — |",
            f"| Std. Deviation | {overall_stats['std_dev']:.2f} |" if overall_stats['std_dev'] else "| Std. Deviation | — |",
            f"| Pass Percentage | {overall_stats['pass_percentage']:.1f}% |" if overall_stats['pass_percentage'] else "| Pass Percentage | — |",
            f"| Fail Percentage | {overall_stats['fail_percentage']:.1f}% |" if overall_stats['fail_percentage'] else "| Fail Percentage | — |",
        ]
        if overall_stats.get("avg_attendance") is not None:
            summary_lines.append(
                f"| Avg Attendance | {overall_stats['avg_attendance']:.1f}% |"
            )

        summary_lines += [
            f"",
            f"---",
            f"",
            f"## Subject-wise Averages",
            f"",
            f"| Subject | Avg | Pass % |",
            f"| --- | --- | --- |",
        ]
        for subj in subject_stats.index:
            avg_s = subject_stats.loc[subj, "Average"]
            pct_s = subject_stats.loc[subj, "Pass_Percentage"]
            summary_lines.append(
                f"| {subj} | "
                f"{'—' if pd.isna(avg_s) else f'{avg_s:.1f}'} | "
                f"{'—' if pd.isna(pct_s) else f'{pct_s:.1f}%'} |"
            )

        summary_lines += [
            f"",
            f"---",
            f"",
            f"## Data Quality",
            f"",
            f"- Missing values: {quality_report.missing_values}",
            f"- Duplicate rows: {quality_report.duplicate_rows}",
            f"- Invalid marks: {quality_report.invalid_mark_cells}",
        ]
        if quality_report.warnings:
            summary_lines.append("")
            summary_lines.append("**Warnings:**")
            for w in quality_report.warnings:
                summary_lines.append(f"- {w}")

        summary_md = "\n".join(summary_lines)
        st.download_button(
            "📥 Download Analysis Summary (Markdown)",
            data=summary_md.encode("utf-8"),
            file_name="analysis_summary.md",
            mime="text/markdown",
        )

        # Preview
        with st.expander("Preview Summary"):
            st.markdown(summary_md)

