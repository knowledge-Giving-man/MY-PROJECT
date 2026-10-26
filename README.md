# 🎓 Student Performance Analysis Dashboard

**A Python-based academic data analytics and visualization system built with Streamlit.**

---

## 📋 Project Overview

The Student Performance Analysis Dashboard is an interactive web application that helps educators and academic administrators analyse student performance data. Upload a CSV file or explore the included synthetic dataset to instantly generate performance statistics, interactive charts, and actionable insights.

---

## 🎯 Objectives

- Visualise student academic performance across multiple subjects.
- Identify high-performing and low-performing students.
- Detect students who may benefit from additional academic support.
- Analyse the relationship between attendance and academic performance.
- Export cleaned data and analysis summaries.

---

## ✨ Features

| Feature | Description |
| --- | --- |
| CSV / Excel Upload | Upload any student marks file and map its columns |
| Sample Dataset | 120 synthetic student records, included out of the box |
| KPI Cards | Total students, average marks, pass %, students needing support, attendance |
| Subject Analysis | Per-subject averages, medians, pass/fail counts |
| Student Rankings | Sorted table with performance categories and pass/fail status |
| Needs Support | Flags students by overall fail, subject fail, or low attendance |
| Attendance Analysis | Scatter plot, correlation coefficient, attendance metrics |
| Interactive Charts | 8 Plotly charts — all update with filters |
| Key Insights | Algorithmic, factual observations from the data |
| Data Quality Report | Missing values, duplicates, invalid marks |
| Filters | By class, category, marks range, attendance, name/ID search |
| CSV Downloads | Cleaned dataset, performance report, subject summary, Markdown summary |

---

## 🛠️ Technology Stack

| Technology | Purpose |
| --- | --- |
| Python 3.11+ | Programming language |
| Streamlit | Web application framework |
| Pandas | Data loading, cleaning, and analysis |
| NumPy | Numerical operations |
| Plotly | Interactive visualizations |
| openpyxl | Excel file support |
| pytest | Automated testing |

---

## 📁 Directory Structure

```
Student_Performance_Analyser/
│
├── app.py                         ← Main Streamlit application
├── generate_sample_data.py        ← Script to regenerate the sample CSV
├── requirements.txt               ← Python dependencies
├── README.md                      ← This file
├── .gitignore
│
├── data/
│   └── sample_students.csv        ← Synthetic sample dataset (120 records)
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py             ← File loading + column auto-detection
│   ├── data_cleaning.py           ← Validation, cleaning, flagging
│   ├── analytics.py               ← Statistical calculations
│   ├── visualizations.py          ← Plotly chart builders
│   └── insights.py                ← Algorithmic insight generation
│
├── tests/
│   ├── __init__.py
│   ├── test_data_cleaning.py
│   ├── test_analytics.py
│   └── test_insights.py
│
└── docs/
    ├── project_documentation.md  ← Technical architecture & module reference
    ├── report_content.md          ← Full written project report
    └── presentation_outline.md   ← Presentation slide outline
```

---

## 🚀 Installation (Windows PowerShell)

### Step 1 — Open PowerShell

Press `Win + X` → select **Windows PowerShell** or **Terminal**.

### Step 2 — Navigate to the project directory

```powershell
cd "D:\college project 2026\Student Performance Analyser"
```

### Step 3 — Create a virtual environment

```powershell
python -m venv .venv
```

This creates an isolated Python environment inside `.venv/` so that project packages do not affect the rest of your system.

### Step 4 — Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

> **If PowerShell blocks activation** (execution policy error), run this one-time fix for the current session only:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then retry the activation command.

Your terminal prompt will show `(.venv)` when the environment is active.

### Step 5 — Install dependencies

```powershell
python -m pip install -r requirements.txt
```

This installs Streamlit, Pandas, Plotly, and all other required libraries.

### Step 6 — Generate the sample dataset (first run only)

```powershell
python generate_sample_data.py
```

This creates `data/sample_students.csv` with 120 synthetic student records.

### Step 7 — Launch the application

```powershell
python -m streamlit run app.py
```

### Step 8 — Open the dashboard

Streamlit will print a local URL such as:
```
Local URL: http://localhost:8501
```
Open that URL in any web browser.

---

## 📖 Using the Dashboard

### Loading Data

**Sample Dataset:**
1. In the sidebar, select **Sample Dataset**.
2. Click **Load Sample Dataset**.
3. The dashboard loads 120 synthetic records automatically.

**Upload Your Own File:**
1. Select **Upload CSV / Excel** in the sidebar.
2. Click **Browse files** and choose your file.
3. After upload, open **Configure columns** and map your columns correctly.
4. Select your subject (marks) columns from the multi-select list.

### Column Mapping

After uploading, expand **Configure columns** in the sidebar to specify:
- Student ID column
- Student Name column
- Class / Group column
- Attendance column
- Subject / marks columns (required — select at least one)

### Reading the Charts

| Chart | What it shows |
| --- | --- |
| Marks Distribution | Spread of student average marks; dashed line = mean |
| Pass vs. Fail Donut | Overall pass/fail ratio |
| Subject Bar Chart | Average marks per subject |
| Top Students | Highest-scoring students by average |
| Attendance Scatter | Each dot = one student; position shows attendance vs marks |
| Class Comparison | Average marks per class/group |
| Category Pie | Proportion of Excellent / Good / Average / etc. |
| Subject Pass/Fail | Side-by-side pass and fail counts per subject |

### Using Filters

Filters in the sidebar work together:
- **Class filter**: shows only selected classes.
- **Category filter**: shows only students in selected categories.
- **Mark range**: min/max average marks slider.
- **Attendance filter**: minimum attendance percentage.
- **Search**: type part of a student name or ID.

Click **↩️ Reset Filters** to restore defaults.

### Interpreting Key Insights

The **💡 Insights** tab shows automatically generated observations. Every statement is derived from calculated statistics — no AI service is used.

### Exporting Results

The **📥 Export** tab provides four download buttons:
1. **Cleaned Dataset** — cleaned CSV with data quality fixes applied.
2. **Performance Report** — ranked student table with pass/fail status.
3. **Subject Summary** — per-subject statistics table.
4. **Analysis Summary** — Markdown report of the full analysis.

---

## 🧪 Running Tests

Make sure the virtual environment is active, then run:

```powershell
python -m pytest tests/ -v
```

This runs all 38 unit tests across three test files.

To run a specific test file:

```powershell
python -m pytest tests/test_analytics.py -v
```

---

## 🔧 Troubleshooting

| Problem | Solution |
| --- | --- |
| `ModuleNotFoundError: No module named 'streamlit'` | Make sure `.venv` is activated and `pip install -r requirements.txt` was run |
| PowerShell execution policy error | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `FileNotFoundError: sample_students.csv` | Run `python generate_sample_data.py` first |
| Charts do not appear | Ensure at least one subject column is selected in sidebar → Configure columns |
| Upload fails | Check that the file is a valid `.csv` or `.xlsx` and is not password-protected |
| Port already in use | Run `python -m streamlit run app.py --server.port 8502` |

---

## 📊 Demonstration Walkthrough

Use this sequence for a live demonstration:

1. **Launch** the app with `python -m streamlit run app.py`.
2. **Load** the sample dataset from the sidebar.
3. **Review** the five KPI cards at the top of the dashboard.
4. **Navigate** to the **📚 Subjects** tab to compare subject averages.
5. **Apply** the Class filter to view a specific class.
6. **Navigate** to **🆘 Needs Support** to see flagged students.
7. **Navigate** to **🗓️ Attendance** to view the attendance scatter plot.
8. **Navigate** to **💡 Insights** to review generated observations.
9. **Navigate** to **📥 Export** and download the performance report.
10. **Switch** to **Upload CSV / Excel** and upload a custom file.

---

## ⚠️ Important Notes

- All data remains local — no data is sent to any external server.
- The sample dataset is entirely synthetic. All names, IDs, and marks are fictional.
- Missing marks are **not** replaced with zero. They are excluded from calculations.
- The dashboard requires an internet connection only on first load to fetch the Google Inter font from Google Fonts. All analysis works offline.

---

## 📚 References

- [Streamlit Documentation](https://docs.streamlit.io)
- [Pandas Documentation](https://pandas.pydata.org/docs)
- [Plotly Python Documentation](https://plotly.com/python)
- [NumPy Documentation](https://numpy.org/doc)
- [pytest Documentation](https://docs.pytest.org)

---

*BTech Computer Science and Engineering — Mini Project | Academic Year: 2025–2026*
