import numpy as np
import pandas as pd
import os

SEED = 42
N_STUDENTS = 120

def generate_sample_dataset(seed: int = SEED, n: int = N_STUDENTS) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Realistic first names and last names pools
    first_names = [
        "Aarav", "Aisha", "Arjun", "Ananya", "Bhavya", "Chetan", "Deepa",
        "Dev", "Divya", "Farhan", "Gauri", "Harsh", "Ishaan", "Jaya",
        "Kabir", "Kavita", "Kiran", "Lakshmi", "Manish", "Meera",
        "Mihir", "Naina", "Nikhil", "Pallavi", "Pranav", "Priya",
        "Rahul", "Riya", "Rohan", "Sakshi", "Samir", "Shreya",
        "Siddharth", "Sneha", "Suresh", "Tanvi", "Uday", "Vandana",
        "Varun", "Vidya", "Vikram", "Yash", "Zara", "Akash", "Amrita",
        "Chirag", "Dhruv", "Esha", "Gaurav", "Harsha", "Ila", "Jai",
        "Kriti", "Lalit", "Madhuri", "Nitin", "Ojasvi", "Pooja",
        "Ranjit", "Sonal", "Tarun", "Uma", "Vishal", "Waqar", "Yamini",
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta", "Reddy",
        "Nair", "Iyer", "Joshi", "Mehta", "Malhotra", "Kapoor", "Agarwal",
        "Chauhan", "Bose", "Das", "Pillai", "Rao", "Sinha",
        "Banerjee", "Chatterjee", "Dubey", "Ghosh", "Hegde",
        "Mishra", "Naik", "Pandey", "Rathore", "Saxena",
    ]

    rng_fn = rng.integers(0, len(first_names), n)
    rng_ln = rng.integers(0, len(last_names), n)
    names = [f"{first_names[f]} {last_names[l]}" for f, l in zip(rng_fn, rng_ln)]

    student_ids = [f"STU{str(i+1).zfill(4)}" for i in range(n)]

    # Assign classes
    classes = rng.choice(["10-A", "10-B", "10-C", "11-A", "11-B"], n)

    # Assign gender
    genders = rng.choice(["Male", "Female"], n, p=[0.52, 0.48])

    # Score generation: mix of performance tiers
    # ~15% struggling, ~25% below average, ~40% average, ~20% high
    tier = rng.choice(
        ["struggling", "below_avg", "average", "good", "excellent"],
        n,
        p=[0.12, 0.18, 0.38, 0.22, 0.10],
    )

    def score_for_tier(t, subject_difficulty=0):
        ranges = {
            "struggling":  (10, 38),
            "below_avg":   (30, 55),
            "average":     (45, 72),
            "good":        (65, 85),
            "excellent":   (82, 100),
        }
        lo, hi = ranges[t]
        lo = max(0, lo - subject_difficulty)
        hi = max(lo + 2, hi - subject_difficulty)
        return int(rng.integers(lo, hi + 1))

    maths       = [score_for_tier(t, subject_difficulty=3) for t in tier]
    science     = [score_for_tier(t, subject_difficulty=2) for t in tier]
    english     = [score_for_tier(t, subject_difficulty=0) for t in tier]
    cs          = [score_for_tier(t, subject_difficulty=1) for t in tier]

    # Attendance loosely correlated with performance tier
    attendance_base = {
        "struggling": 55, "below_avg": 65, "average": 75,
        "good": 83, "excellent": 91,
    }
    attendance = [
        int(np.clip(attendance_base[t] + rng.normal(0, 8), 0, 100))
        for t in tier
    ]

    # Introduce ~5% missing values in marks columns
    def add_missing(values, missing_rate=0.05):
        arr = [float(v) for v in values]
        missing_indices = rng.choice(len(arr), int(len(arr) * missing_rate), replace=False)
        for idx in missing_indices:
            arr[idx] = float("nan")
        return arr

    df = pd.DataFrame(
        {
            "Student_ID":            student_ids,
            "Student_Name":          names,
            "Class":                 classes,
            "Gender":                genders,
            "Mathematics":           add_missing(maths),
            "Science":               add_missing(science),
            "English":               add_missing(english),
            "Computer_Science":      add_missing(cs),
            "Attendance_Percentage": attendance,
        }
    )

    return df

if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "data", "sample_students.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df = generate_sample_dataset()
    df.to_csv(out_path, index=False)
    print(f"Sample dataset saved to: {out_path}")
    print(f"Records: {len(df)}, Columns: {list(df.columns)}")
