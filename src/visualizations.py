
from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Shared colour palette ─────────────────────────────────────────────────────
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

PLOTLY_TEMPLATE = "plotly_white"

def _safe_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#888"),
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        height=350,
    )
    return fig

# ── Chart 1: Subject Performance Bar Chart ───────────────────────────────────

def subject_performance_bar(subject_stats: pd.DataFrame) -> go.Figure:
    if subject_stats.empty or "Average" not in subject_stats.columns:
        return _safe_fig("No subject data available.")

    data = subject_stats["Average"].dropna().reset_index()
    data.columns = ["Subject", "Average"]

    if data.empty:
        return _safe_fig("No valid subject averages to display.")

    data = data.sort_values("Average", ascending=True)

    fig = px.bar(
        data,
        x="Average",
        y="Subject",
        orientation="h",
        text="Average",
        color="Average",
        color_continuous_scale=px.colors.sequential.Blues,
        labels={"Average": "Average Marks", "Subject": ""},
        title="Subject-wise Average Marks",
        template=PLOTLY_TEMPLATE,
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        xaxis_range=[0, 105],
        coloraxis_showscale=False,
        height=max(300, len(data) * 55 + 80),
        margin=dict(l=10, r=30, t=50, b=30),
        title_font_size=16,
    )
    return fig

# ── Chart 2: Marks Distribution Histogram ────────────────────────────────────

def marks_distribution_histogram(df: pd.DataFrame, avg_col: str) -> go.Figure:
    series = df[avg_col].dropna()
    if len(series) < 2:
        return _safe_fig("Not enough data for a distribution chart.")

    fig = px.histogram(
        series,
        nbins=20,
        labels={"value": "Average Marks", "count": "Number of Students"},
        title="Distribution of Student Average Marks",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=["#4575b4"],
    )
    fig.update_layout(
        bargap=0.05,
        xaxis_title="Average Marks",
        yaxis_title="Number of Students",
        showlegend=False,
        height=380,
        title_font_size=16,
        margin=dict(l=10, r=10, t=50, b=40),
    )
    # Add a vertical line for the mean
    mean_val = series.mean()
    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Mean: {mean_val:.1f}",
        annotation_position="top right",
    )
    return fig

# ── Chart 3: Top Students Bar Chart ──────────────────────────────────────────

def top_students_bar(
    df: pd.DataFrame,
    avg_col: str,
    name_col: Optional[str],
    id_col: Optional[str],
    top_n: int = 10,
) -> go.Figure:
    data = df[[c for c in [id_col, name_col, avg_col] if c and c in df.columns]].copy()
    data = data.dropna(subset=[avg_col])
    data = data.sort_values(avg_col, ascending=False).head(top_n)

    if data.empty:
        return _safe_fig("No student data available.")

    # Label: prefer name, fall back to ID, then row index
    if name_col and name_col in data.columns:
        label = data[name_col].astype(str)
    elif id_col and id_col in data.columns:
        label = data[id_col].astype(str)
    else:
        label = data.index.astype(str)

    data = data.copy()
    data["Label"] = label.values
    data = data.sort_values(avg_col, ascending=True)  # ascending for horizontal bar readability

    fig = px.bar(
        data,
        x=avg_col,
        y="Label",
        orientation="h",
        text=avg_col,
        color=avg_col,
        color_continuous_scale=px.colors.sequential.Teal,
        labels={avg_col: "Average Marks", "Label": ""},
        title=f"Top {top_n} Students by Average Marks",
        template=PLOTLY_TEMPLATE,
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        xaxis_range=[0, 108],
        coloraxis_showscale=False,
        height=max(300, top_n * 40 + 80),
        margin=dict(l=10, r=30, t=50, b=30),
        title_font_size=16,
    )
    return fig

# ── Chart 4: Pass vs Fail Donut Chart ────────────────────────────────────────

def pass_fail_donut(overall_stats: dict) -> go.Figure:
    pass_count = overall_stats.get("pass_count", 0)
    fail_count = overall_stats.get("fail_count", 0)

    if pass_count + fail_count == 0:
        return _safe_fig("No valid student data for pass/fail chart.")

    fig = go.Figure(
        go.Pie(
            labels=["Pass", "Fail"],
            values=[pass_count, fail_count],
            hole=0.55,
            marker_colors=[PASS_FAIL_COLORS["Pass"], PASS_FAIL_COLORS["Fail"]],
            textinfo="label+percent",
            textfont_size=13,
        )
    )
    fig.update_layout(
        title="Overall Pass vs. Fail",
        title_font_size=16,
        template=PLOTLY_TEMPLATE,
        height=370,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        annotations=[dict(
            text=f"{pass_count + fail_count}<br>Students",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False,
        )],
        margin=dict(l=10, r=10, t=50, b=50),
    )
    return fig

# ── Chart 5: Subject-Level Pass/Fail Grouped Bar ─────────────────────────────

def subject_pass_fail_bar(subject_stats: pd.DataFrame) -> go.Figure:
    if subject_stats.empty:
        return _safe_fig("No subject data available.")

    data = subject_stats[["Pass_Count", "Fail_Count"]].reset_index()
    if data.empty:
        return _safe_fig("No subject pass/fail data available.")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Pass",
        x=data["Subject"],
        y=data["Pass_Count"],
        marker_color=PASS_FAIL_COLORS["Pass"],
        text=data["Pass_Count"],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Fail",
        x=data["Subject"],
        y=data["Fail_Count"],
        marker_color=PASS_FAIL_COLORS["Fail"],
        text=data["Fail_Count"],
        textposition="outside",
    ))
    fig.update_layout(
        barmode="group",
        title="Pass and Fail Counts per Subject",
        title_font_size=16,
        xaxis_title="Subject",
        yaxis_title="Number of Students",
        template=PLOTLY_TEMPLATE,
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(l=10, r=10, t=50, b=60),
    )
    return fig

# ── Chart 6: Attendance vs. Marks Scatter Plot ───────────────────────────────

def attendance_vs_marks_scatter(
    df: pd.DataFrame,
    avg_col: str,
    attendance_col: str,
    category_col: Optional[str] = None,
    name_col: Optional[str] = None,
) -> go.Figure:
    plot_df = df[[c for c in [avg_col, attendance_col, category_col, name_col]
                  if c and c in df.columns]].dropna(subset=[avg_col, attendance_col])

    if len(plot_df) < 2:
        return _safe_fig("Not enough data for an attendance vs. marks scatter plot.")

    hover_data = {}
    if name_col and name_col in plot_df.columns:
        hover_data[name_col] = True

    color_col = category_col if (category_col and category_col in plot_df.columns) else None

    fig = px.scatter(
        plot_df,
        x=attendance_col,
        y=avg_col,
        color=color_col,
        color_discrete_map=CATEGORY_COLORS if color_col else None,
        hover_name=name_col if (name_col and name_col in plot_df.columns) else None,
        labels={
            attendance_col: "Attendance (%)",
            avg_col:        "Average Marks",
        },
        title="Attendance vs. Average Marks",
        template=PLOTLY_TEMPLATE,
        opacity=0.8,
    )
    fig.update_traces(marker_size=8)
    fig.update_layout(
        height=420,
        title_font_size=16,
        margin=dict(l=10, r=10, t=50, b=50),
        legend_title_text="Category" if color_col else "",
    )
    return fig

# ── Chart 7: Class Comparison Bar Chart ──────────────────────────────────────

def class_comparison_bar(class_comparison_df: pd.DataFrame) -> go.Figure:
    if class_comparison_df.empty:
        return _safe_fig("No class data available for comparison.")

    fig = px.bar(
        class_comparison_df,
        x="Class",
        y="Average_Marks",
        color="Average_Marks",
        color_continuous_scale=px.colors.sequential.Purp,
        text="Average_Marks",
        labels={"Average_Marks": "Average Marks", "Class": "Class / Group"},
        title="Average Marks by Class / Group",
        template=PLOTLY_TEMPLATE,
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        height=380,
        title_font_size=16,
        yaxis_range=[0, 105],
        margin=dict(l=10, r=10, t=50, b=40),
    )
    return fig

# ── Chart 8: Performance Category Pie / Bar ───────────────────────────────────

def performance_category_chart(df: pd.DataFrame, category_col: str) -> go.Figure:
    if category_col not in df.columns:
        return _safe_fig("Performance category data not available.")

    counts = df[category_col].value_counts().reset_index()
    counts.columns = ["Category", "Count"]

    if counts.empty:
        return _safe_fig("No category data available.")

    colors = [CATEGORY_COLORS.get(cat, "#aaaaaa") for cat in counts["Category"]]

    fig = px.pie(
        counts,
        names="Category",
        values="Count",
        color="Category",
        color_discrete_map=CATEGORY_COLORS,
        title="Performance Category Distribution",
        template=PLOTLY_TEMPLATE,
    )
    fig.update_traces(textinfo="label+percent", textfont_size=12)
    fig.update_layout(
        height=380,
        title_font_size=16,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(l=10, r=10, t=50, b=60),
    )
    return fig
