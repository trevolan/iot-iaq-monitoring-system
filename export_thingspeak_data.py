import argparse
import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


TIMEZONE = timezone(timedelta(hours=2))
MAX_RESULTS = 8000

CSV_COLUMNS = [
    "created_at",
    "entry_id",
    "temperature_c",
    "humidity_percent",
    "pm1_ug_m3",
    "pm25_ug_m3",
    "pm10_ug_m3",
    "co2_ppm",
    "iaq_state",
    "alert_code",
]


def get_configuration():
    load_dotenv()

    channel_id = os.getenv("THINGSPEAK_CHANNEL_ID")
    api_key = os.getenv("THINGSPEAK_READ_API_KEY")

    if not channel_id or not api_key:
        raise RuntimeError(
            "ThingSpeak configuration is missing from .env."
        )

    return channel_id, api_key


def fetch_chunk(channel_id, api_key, start, end):
    url = (
        f"https://api.thingspeak.com/channels/"
        f"{channel_id}/feeds.json"
    )

    parameters = {
        "api_key": api_key,
        "start": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end": end.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Africa/Johannesburg",
        "results": MAX_RESULTS,
    }

    response = requests.get(
        url,
        params=parameters,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise RuntimeError(
            "ThingSpeak returned an unexpected response."
        )

    return payload.get("feeds", [])


def fetch_complete_range(channel_id, api_key, start, end):
    feeds = fetch_chunk(
        channel_id,
        api_key,
        start,
        end,
    )

    if len(feeds) < MAX_RESULTS:
        return feeds

    if end - start <= timedelta(minutes=1):
        raise RuntimeError(
            "Too many readings were returned for a one-minute "
            "period."
        )

    midpoint = start + ((end - start) / 2)

    print(
        "Large data range detected. "
        "Dividing the request..."
    )

    first_half = fetch_complete_range(
        channel_id,
        api_key,
        start,
        midpoint,
    )

    second_half = fetch_complete_range(
        channel_id,
        api_key,
        midpoint,
        end,
    )

    return first_half + second_half


def convert_feed(feed):
    return {
        "created_at": feed.get("created_at"),
        "entry_id": feed.get("entry_id"),
        "temperature_c": feed.get("field1"),
        "humidity_percent": feed.get("field2"),
        "pm1_ug_m3": feed.get("field3"),
        "pm25_ug_m3": feed.get("field4"),
        "pm10_ug_m3": feed.get("field5"),
        "co2_ppm": feed.get("field6"),
        "iaq_state": feed.get("field7"),
        "alert_code": feed.get("field8"),
    }


def remove_duplicates(feeds):
    unique_feeds = {}

    for feed in feeds:
        entry_id = feed.get("entry_id")

        if entry_id is not None:
            unique_feeds[entry_id] = feed

    return [
        unique_feeds[entry_id]
        for entry_id in sorted(unique_feeds)
    ]


def save_csv(rows):
    output_directory = Path("data")
    output_directory.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
        output_directory
        / f"thingspeak_export_{timestamp}.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS,
        )

        writer.writeheader()
        writer.writerows(rows)

    return output_path


def print_quality_summary(rows):
    print(f"\nTotal readings exported: {len(rows)}")

    for column in CSV_COLUMNS[2:]:
        missing = sum(
            row[column] in (None, "")
            for row in rows
        )

        print(
            f"Missing {column}: "
            f"{missing}"
        )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Export ThingSpeak research data."
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Collection start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end",
        help=(
            "Optional end date in YYYY-MM-DD format. "
            "Defaults to the current time."
        ),
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()

    start = datetime.strptime(
        arguments.start,
        "%Y-%m-%d",
    ).replace(tzinfo=TIMEZONE)

    if arguments.end:
        end = (
            datetime.strptime(
                arguments.end,
                "%Y-%m-%d",
            ).replace(tzinfo=TIMEZONE)
            + timedelta(days=1)
            - timedelta(seconds=1)
        )
    else:
        end = datetime.now(TIMEZONE)

    if start >= end:
        raise ValueError(
            "The start date must be before the end date."
        )

    channel_id, api_key = get_configuration()

    print(
        f"Downloading readings from {start} to {end}..."
    )

    feeds = fetch_complete_range(
        channel_id,
        api_key,
        start,
        end,
    )

    feeds = remove_duplicates(feeds)
    rows = [convert_feed(feed) for feed in feeds]

    output_path = save_csv(rows)

    print_quality_summary(rows)
    print(f"\nDataset saved to: {output_path}")


if __name__ == "__main__":
    main()