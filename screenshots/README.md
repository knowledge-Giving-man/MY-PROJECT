# Screenshots

This directory contains screenshots of the running Student Performance Analysis Dashboard.

## Capturing Screenshots

Since automated browser capture was unavailable in this environment, screenshots should be
captured manually during the live demonstration:

1. Run: `python -m streamlit run app.py`
2. Open http://localhost:8501 in a browser
3. Load the sample dataset
4. Capture screenshots of each tab using Windows Snipping Tool (`Win + Shift + S`)

## Recommended Screenshots to Capture

| Filename | What to Capture |
| --- | --- |
| `01_initial_load.png` | The "Get started" page with empty sidebar |
| `02_kpi_cards.png` | Dashboard after loading sample data — 5 KPI cards visible |
| `03_overview_charts.png` | Overview tab — distribution histogram + pass/fail donut |
| `04_subjects_tab.png` | Subjects tab — bar chart + statistics table |
| `05_students_tab.png` | Students tab — ranked table with pass/fail highlighting |
| `06_needs_support.png` | Needs Support tab — flagged students list |
| `07_attendance_scatter.png` | Attendance tab — scatter plot with correlation |
| `08_insights_tab.png` | Insights tab — list of generated insights |
| `09_data_quality.png` | Data Quality tab — quality metrics |
| `10_export_tab.png` | Export tab — download buttons |
| `11_filter_applied.png` | Any tab with class filter applied |
| `12_upload_mode.png` | Upload mode with column mapping expander open |

## Verified Programmatic Results (Sample Dataset — 120 students)

The following results were computed and verified by running the analytics pipeline:

| Metric | Value |
| --- | --- |
| Total Records | 120 |
| Valid Records | 120 |
| Missing Mark Cells | 24 (5% by design) |
| Overall Average | 58.86 |
| Pass Percentage (threshold=40) | 83.33% |
| Average Attendance | 73.67% |
| Mathematics Average | 56.30 |
| Science Average | 57.82 |
| English Average | 59.65 |
| Computer Science Average | 60.46 |

*All values are computed from the synthetic sample dataset. Results will differ when using a real uploaded dataset.*
