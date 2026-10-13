
from pathlib import Path
import pandas as pd
import numpy as np

# =========================================================
# 1. CONFIGURATION
# =========================================================

BASE_DIR = Path(r"G:\Git Projects\Project 2")
OUTPUT_DIR = BASE_DIR / "cyclistic_output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_FILE = OUTPUT_DIR / "cyclistic_2025_cleaned.csv"
CHUNK_SIZE = 100_000

EXPECTED_COLUMNS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_name",
    "start_station_id",
    "end_station_name",
    "end_station_id",
    "start_lat",
    "start_lng",
    "end_lat",
    "end_lng",
    "member_casual",
]

# Only match the monthly 2025 CSV files.
csv_files = sorted(
    BASE_DIR.glob("2025??-divvy-tripdata.csv")
)

if len(csv_files) != 12:
    raise FileNotFoundError(
        f"Expected 12 monthly CSV files, found {len(csv_files)}.\n"
        "Check the filenames and BASE_DIR path."
    )

print(f"Found {len(csv_files)} monthly files.")

# Remove an old output file so repeated runs don't append duplicates.
if CLEANED_FILE.exists():
    CLEANED_FILE.unlink()


# =========================================================
# 2. HELPER FUNCTIONS
# =========================================================

def add_analysis_columns(df):
    """Clean one chunk and add columns needed for Question 1 analysis."""

    # Parse timestamps and coordinates.
    df["started_at"] = pd.to_datetime(
        df["started_at"], errors="coerce"
    )
    # Keep only rides that started during calendar year 2025
    df = df[
        (df["started_at"] >= "2025-01-01") &
        (df["started_at"] < "2026-01-01")
    ].copy()
    
    df["ended_at"] = pd.to_datetime(
        df["ended_at"], errors="coerce"
    )

    coordinate_columns = [
        "start_lat", "start_lng",
        "end_lat", "end_lng"
    ]

    for col in coordinate_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize text fields.
    for col in [
        "ride_id", "rideable_type",
        "member_casual", "start_station_name",
        "end_station_name"
    ]:
        df[col] = df[col].astype("string").str.strip()

    df["member_casual"] = df["member_casual"].str.lower()
    df["rideable_type"] = df["rideable_type"].str.lower()

    # Remove records without a usable ride ID.
    df = df[
        df["ride_id"].notna()
        & df["ride_id"].ne("")
        & df["ride_id"].ne("<NA>")
    ].copy()

    # Calculate ride duration.
    duration = (
        df["ended_at"] - df["started_at"]
    ).dt.total_seconds() / 60

    df["ride_length_minutes"] = duration.round(2)
    df["ride_length_hours"] = (
        df["ride_length_minutes"] / 60
    ).round(3)

    # Flag questionable durations; retain these records for auditing.
    df["duration_flag"] = np.select(
        [
            df["started_at"].isna() | df["ended_at"].isna(),
            df["ride_length_minutes"] <= 0,
            df["ride_length_minutes"] > 1440,
        ],
        [
            "invalid_timestamp",
            "zero_or_negative",
            "over_24_hours",
        ],
        default="valid",
    )

    # Calendar and time features.
    df["day_of_week"] = df["started_at"].dt.day_name()
    df["day_of_week_num"] = df["started_at"].dt.dayofweek + 1
    df["month"] = df["started_at"].dt.month
    df["month_name"] = df["started_at"].dt.month_name()

    df["weekday_weekend"] = np.where(
        df["day_of_week_num"].isin([6, 7]),
        "Weekend",
        "Weekday",
    )

    return df


# =========================================================
# 3. PROCESS ALL 12 MONTHS IN CHUNKS
# =========================================================

total_rows_read = 0
total_rows_written = 0
header_written = False

for file_number, file_path in enumerate(csv_files, start=1):

    print(f"\n[{file_number}/12] Processing: {file_path.name}")

    file_rows = 0

    for chunk in pd.read_csv(
        file_path,
        chunksize=CHUNK_SIZE,
        dtype={
            "ride_id": "string",
            "rideable_type": "string",
            "start_station_id": "string",
            "end_station_id": "string",
            "member_casual": "string",
        },
        usecols=EXPECTED_COLUMNS,
        encoding="utf-8-sig",
        low_memory=False,
    ):
        total_rows_read += len(chunk)
        file_rows += len(chunk)

        cleaned = add_analysis_columns(chunk)

        # Append processed chunks to the combined output.
        cleaned.to_csv(
            CLEANED_FILE,
            mode="a",
            index=False,
            header=not header_written,
            encoding="utf-8-sig",
        )

        header_written = True
        total_rows_written += len(cleaned)

    print(f"Rows read from file: {file_rows:,}")

print("\n" + "=" * 55)
print("PROCESSING COMPLETED")
print("=" * 55)
print(f"Rows read:       {total_rows_read:,}")
print(f"Rows written:    {total_rows_written:,}")
print(f"Cleaned dataset: {CLEANED_FILE}")


# =========================================================
# 4. GENERATE SUMMARY TABLES IN CHUNKS
# =========================================================

print("\nGenerating summary tables...")

summary_specs = {
    "rider_type_summary": ["member_casual"],
    "monthly_summary": ["month", "month_name", "member_casual"],
    "weekday_summary": ["day_of_week_num", "day_of_week", "member_casual"],
    "weekday_weekend_summary": ["weekday_weekend", "member_casual"],
    "bike_type_summary": ["rideable_type", "member_casual"],
}

# Each group tracks ride counts and duration statistics.
accumulators = {
    name: {} for name in summary_specs
}

valid_duration_total = 0
invalid_duration_total = 0
duplicate_ids_within_chunks = 0
seen_ids = set()

# This set is useful for auditing duplicates, but uses memory.
# For very large datasets, use a disk-backed deduplication method instead.
for chunk in pd.read_csv(
    CLEANED_FILE,
    chunksize=CHUNK_SIZE,
    usecols=[
        "ride_id", "ride_length_minutes", "duration_flag",
        "member_casual", "month", "month_name",
        "day_of_week_num", "day_of_week", "weekday_weekend",
        "rideable_type",
    ],
    dtype={"ride_id": "string"},
    low_memory=False,
):
    valid = (
        chunk["duration_flag"].eq("valid")
        & chunk["ride_length_minutes"].notna()
    )

    valid_duration_total += int(valid.sum())
    invalid_duration_total += int((~valid).sum())

    # Detect repeated ride IDs across the entire combined dataset.
    current_ids = chunk["ride_id"].dropna()
    duplicate_ids_within_chunks += int(
        current_ids.duplicated().sum()
    )

    # Cross-chunk duplicate detection.
    for ride_id in current_ids:
        if ride_id in seen_ids:
            duplicate_ids_within_chunks += 1
        else:
            seen_ids.add(ride_id)

    # Only valid positive durations contribute to duration statistics.
    chunk["duration_for_summary"] = chunk[
        "ride_length_minutes"
    ].where(valid)

    for name, keys in summary_specs.items():
        grouped = chunk.groupby(
            keys, dropna=False
        ).agg(
            ride_count=("ride_id", "size"),
            valid_duration_count=("duration_for_summary", "count"),
            duration_sum=("duration_for_summary", "sum"),
        )

        store = accumulators[name]

        for group_key, row in grouped.iterrows():
            if not isinstance(group_key, tuple):
                group_key = (group_key,)

            group_key = tuple(
                "<NA>" if pd.isna(v) else v
                for v in group_key
            )

            if group_key not in store:
                store[group_key] = [
                    0,  # ride count
                    0,  # valid duration count
                    0.0,  # sum of valid durations
                ]

            store[group_key][0] += int(row["ride_count"])
            store[group_key][1] += int(row["valid_duration_count"])

            if pd.notna(row["duration_sum"]):
                store[group_key][2] += float(row["duration_sum"])


# Save the summaries.
for name, keys in summary_specs.items():
    records = []

    for group_key, values in accumulators[name].items():
        record = dict(zip(keys, group_key))

        ride_count, duration_count, duration_sum = values

        record["ride_count"] = ride_count
        record["valid_duration_count"] = duration_count
        record["average_ride_length_minutes"] = (
            round(duration_sum / duration_count, 2)
            if duration_count else np.nan
        )

        records.append(record)

    summary_df = pd.DataFrame(records)

    if not summary_df.empty:
        summary_df = summary_df.sort_values(keys)

    summary_path = OUTPUT_DIR / f"{name}.csv"
    summary_df.to_csv(
        summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Saved: {summary_path.name}")

print("\n" + "=" * 55)
print("DATA QUALITY CHECKS")
print("=" * 55)
print(f"Rows with valid durations:   {valid_duration_total:,}")
print(f"Rows with flagged durations: {invalid_duration_total:,}")
print(f"Repeated ride IDs detected:  {duplicate_ids_within_chunks:,}")
print(f"\nAll output files are in:\n{OUTPUT_DIR}")



# =========================================================
# 5. FINAL VALIDATION
# =========================================================

print("\n========== FINAL VALIDATION ==========")

# Check that all 12 monthly files were processed
print(f"Monthly CSV files found: {len(csv_files)}")

# Check cleaned dataset size and columns
print(f"Cleaned dataset exists: {CLEANED_FILE.exists()}")

if CLEANED_FILE.exists():
    print(
        f"Cleaned dataset size: "
        f"{CLEANED_FILE.stat().st_size / (1024 ** 3):.2f} GB"
    )

    # Read a small sample only
    sample = pd.read_csv(
        CLEANED_FILE,
        nrows=5,
        encoding="utf-8-sig"
    )

    print("\nSample records:")
    print(sample.head())

    print("\nColumns:")
    print(sample.columns.tolist())

    # Count rides separately for each rider type
    print("\nRides by rider type:")

    rider_counts = pd.read_csv(
        CLEANED_FILE,
        usecols=["member_casual"],
        encoding="utf-8-sig"
    )["member_casual"].value_counts()

    print(rider_counts.to_string())

# Display total rows processed during the original run
print(f"\nRows read from source files: {total_rows_read:,}")
print(f"Rows written to cleaned file: {total_rows_written:,}")
print("======================================")
