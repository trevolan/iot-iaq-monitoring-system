import argparse
import csv
import statistics
from datetime import datetime
from pathlib import Path


NUMERIC_COLUMNS = {
    "temperature_c": (-10, 60),
    "humidity_percent": (0, 100),
    "pm1_ug_m3": (0, 1000),
    "pm25_ug_m3": (0, 1000),
    "pm10_ug_m3": (0, 1000),
    "co2_ppm": (250, 10000),
    "iaq_state": (1, 4),
    "alert_code": (0, 6),
}

ALLOWED_CATEGORY_VALUES = {
    "iaq_state": {1, 2, 3, 4},
    "alert_code": {0, 1, 2, 3, 4, 6},
}

REQUIRED_COLUMNS = {
    "created_at",
    "entry_id",
    *NUMERIC_COLUMNS.keys(),
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Validate an exported ThingSpeak dataset."
    )

    parser.add_argument(
        "csv_file",
        help="Path to the exported CSV dataset.",
    )

    return parser.parse_args()


def parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def parse_number(value):
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_dataset(csv_path):
    with csv_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        available_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            REQUIRED_COLUMNS - available_columns
        )

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                f"Required columns are missing: "
                f"{missing_text}"
            )

        return list(reader)


def check_entry_ids(rows):
    entry_ids = [
        row["entry_id"]
        for row in rows
        if row["entry_id"]
    ]

    duplicate_count = (
        len(entry_ids) - len(set(entry_ids))
    )

    print("\nENTRY ID CHECK")
    print(f"Duplicate entry IDs: {duplicate_count}")


def check_timestamps(rows):
    timestamps = [
        parse_timestamp(row["created_at"])
        for row in rows
    ]

    invalid_count = sum(
        timestamp is None
        for timestamp in timestamps
    )

    valid_timestamps = [
        timestamp
        for timestamp in timestamps
        if timestamp is not None
    ]

    print("\nTIMESTAMP CHECK")
    print(f"Invalid timestamps: {invalid_count}")

    if len(valid_timestamps) < 2:
        print("Not enough timestamps for gap analysis.")
        return

    out_of_order = sum(
        current < previous
        for previous, current in zip(
            valid_timestamps,
            valid_timestamps[1:],
        )
    )

    intervals = [
        (current - previous).total_seconds()
        for previous, current in zip(
            valid_timestamps,
            valid_timestamps[1:],
        )
        if current >= previous
    ]

    median_interval = statistics.median(intervals)
    largest_interval = max(intervals)

    gap_threshold = max(
        median_interval * 3,
        180,
    )

    large_gaps = [
        interval
        for interval in intervals
        if interval > gap_threshold
    ]

    duration = (
        valid_timestamps[-1]
        - valid_timestamps[0]
    )

    print(
        f"First timestamp: "
        f"{valid_timestamps[0]}"
    )
    print(
        f"Last timestamp: "
        f"{valid_timestamps[-1]}"
    )
    print(
        f"Collection duration: "
        f"{duration}"
    )
    print(
        f"Median sampling interval: "
        f"{median_interval:.1f} seconds"
    )
    print(
        f"Largest sampling gap: "
        f"{largest_interval:.1f} seconds"
    )
    print(
        f"Large gaps detected: "
        f"{len(large_gaps)}"
    )
    print(
        f"Out-of-order timestamps: "
        f"{out_of_order}"
    )


def check_numeric_columns(rows):
    print("\nSENSOR VALUE CHECK")

    for column, limits in NUMERIC_COLUMNS.items():
        minimum_allowed, maximum_allowed = limits

        raw_values = [
            row[column]
            for row in rows
        ]

        values = [
            parse_number(value)
            for value in raw_values
        ]

        missing_count = sum(
            value in (None, "")
            for value in raw_values
        )

        invalid_count = sum(
            raw not in (None, "")
            and parsed is None
            for raw, parsed in zip(
                raw_values,
                values,
            )
        )

        valid_values = [
            value
            for value in values
            if value is not None
        ]

        if column in ALLOWED_CATEGORY_VALUES:
            allowed_values = (
                ALLOWED_CATEGORY_VALUES[column]
            )

            flagged_values = [
                value
                for value in valid_values
                if value not in allowed_values
            ]
        else:
            flagged_values = [
                value
                for value in valid_values
                if (
                    value < minimum_allowed
                    or value > maximum_allowed
                )
            ]

        print(f"\n{column}")

        if valid_values:
            print(
                f"  Minimum: "
                f"{min(valid_values):.2f}"
            )
            print(
                f"  Average: "
                f"{statistics.fmean(valid_values):.2f}"
            )
            print(
                f"  Maximum: "
                f"{max(valid_values):.2f}"
            )
            print(
                f"  Unique values: "
                f"{len(set(valid_values))}"
            )

        print(f"  Missing values: {missing_count}")
        print(f"  Invalid values: {invalid_count}")
        print(
            f"  Values flagged for review: "
            f"{len(flagged_values)}"
        )


def print_class_distribution(rows, column):
    counts = {}

    for row in rows:
        value = row[column]

        counts[value] = counts.get(value, 0) + 1

    print(f"\n{column.upper()} DISTRIBUTION")

    for value, count in sorted(counts.items()):
        percentage = (
            count / len(rows)
        ) * 100

        print(
            f"Value {value}: "
            f"{count} readings "
            f"({percentage:.2f}%)"
        )


def main():
    arguments = parse_arguments()
    csv_path = Path(arguments.csv_file)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    rows = load_dataset(csv_path)

    print("THINGSPEAK DATASET VALIDATION")
    print(f"Dataset: {csv_path}")
    print(f"Total rows: {len(rows)}")

    if not rows:
        print("The dataset contains no readings.")
        return

    check_entry_ids(rows)
    check_timestamps(rows)
    check_numeric_columns(rows)
    print_class_distribution(rows, "iaq_state")
    print_class_distribution(rows, "alert_code")

    print(
        "\nValidation complete. Flagged values should "
        "be reviewed before cleaning or modelling."
    )


if __name__ == "__main__":
    main()