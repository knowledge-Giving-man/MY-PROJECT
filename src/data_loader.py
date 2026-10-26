
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

import pandas as pd

# ── Built-in sample dataset path ─────────────────────────────────────────────
SAMPLE_DATA_PATH = Path(__file__).parent.parent / "data" / "sample_students.csv"

# ── Standard column name variants (lower-case) ───────────────────────────────
_ID_VARIANTS       = {"student_id", "id", "roll_no", "roll", "rollno", "studentid"}
_NAME_VARIANTS     = {"student_name", "name", "student", "studentname", "full_name"}
_CLASS_VARIANTS    = {"class", "grade", "section", "group", "division", "batch"}
_GENDER_VARIANTS   = {"gender", "sex"}
_ATTEND_VARIANTS   = {
    "attendance_percentage", "attendance", "attend", "attendance%",
    "attendance_pct", "attendance_%",
}
_SUBJECT_HINTS     = {
    "mathematics", "math", "maths", "science", "physics", "chemistry",
    "biology", "english", "hindi", "social", "social_science", "geography",
    "history", "computer_science", "computer", "cs", "it", "economics",
    "accounts", "accountancy", "business",
}

# ── Loaders ──────────────────────────────────────────────────────────────────

def load_sample_dataset() -> pd.DataFrame:
    if not SAMPLE_DATA_PATH.exists():
        # Try to generate it on the fly
        try:
            from generate_sample_data import generate_sample_dataset
            df = generate_sample_dataset()
            SAMPLE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(SAMPLE_DATA_PATH, index=False)
            return df
        except ImportError:
            raise FileNotFoundError(
                f"Sample dataset not found at {SAMPLE_DATA_PATH}. "
                "Run generate_sample_data.py first."
            )
    return pd.read_csv(SAMPLE_DATA_PATH)

def load_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, str]:
    filename: str = uploaded_file.name.lower()
    raw_bytes = uploaded_file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw_bytes))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(raw_bytes), engine="openpyxl")
        else:
            return pd.DataFrame(), (
                f"Unsupported file type: '{uploaded_file.name}'. "
                "Please upload a .csv or .xlsx file."
            )
    except Exception as exc:
        return pd.DataFrame(), f"Could not parse file: {exc}"

    if df.empty:
        return pd.DataFrame(), "The uploaded file contains no data rows."

    return df, ""

# ── Column detection ─────────────────────────────────────────────────────────

def _normalise(col: str) -> str:
    return col.strip().lower().replace(" ", "_").replace("-", "_")

def auto_detect_columns(df: pd.DataFrame) -> dict[str, Optional[str]]:
    cols = df.columns.tolist()
    norm_map = {_normalise(c): c for c in cols}

    def find_first(variants: set) -> Optional[str]:
        for key in variants:
            if key in norm_map:
                return norm_map[key]
        return None

    id_col         = find_first(_ID_VARIANTS)
    name_col       = find_first(_NAME_VARIANTS)
    class_col      = find_first(_CLASS_VARIANTS)
    gender_col     = find_first(_GENDER_VARIANTS)
    attendance_col = find_first(_ATTEND_VARIANTS)

    # Numeric columns that are *not* already mapped to special roles
    special_cols = {c for c in [id_col, name_col, class_col, gender_col, attendance_col] if c}

    numeric_cols = [
        c for c in cols
        if c not in special_cols and pd.api.types.is_numeric_dtype(df[c])
    ]

    # Prefer columns whose normalised name matches known subject keywords
    subject_cols = [
        c for c in numeric_cols if _normalise(c) in _SUBJECT_HINTS
    ]
    # Fall back: if no subject names matched, offer all remaining numeric cols
    if not subject_cols:
        subject_cols = numeric_cols

    return {
        "id_col":         id_col,
        "name_col":       name_col,
        "class_col":      class_col,
        "gender_col":     gender_col,
        "attendance_col": attendance_col,
        "subject_cols":   subject_cols,
    }

def get_column_mapping_defaults(df: pd.DataFrame) -> dict:
    return auto_detect_columns(df)
