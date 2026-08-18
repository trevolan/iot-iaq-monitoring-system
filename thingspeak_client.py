import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv


load_dotenv()


def convert_reading(value, field_name):
    """Convert a ThingSpeak field to a numeric value."""

    if value is None or value == "":
        raise ValueError(f"{field_name} does not contain a reading.")

    return float(value)


def fetch_latest_readings():
    """Retrieve the most recent reading from ThingSpeak."""

    channel_id = os.getenv("THINGSPEAK_CHANNEL_ID")
    read_api_key = os.getenv("THINGSPEAK_READ_API_KEY")

    if not channel_id or not read_api_key:
        raise ValueError(
            "ThingSpeak Channel ID or Read API Key is missing."
        )

    url = (
        f"https://api.thingspeak.com/channels/"
        f"{channel_id}/feeds/last.json"
    )

    response = requests.get(
        url,
        params={"api_key": read_api_key},
        timeout=10,
    )

    response.raise_for_status()
    data = response.json()

    recorded_at = datetime.fromisoformat(
        data["created_at"].replace("Z", "+00:00")
    )

    reading_age = datetime.now(timezone.utc) - recorded_at

    if reading_age <= timedelta(minutes=10):
        device_status = "Online"
    else:
        device_status = "Offline"

    local_recorded_at = recorded_at.astimezone()

    return {
        "entry_id": data.get("entry_id"),
        "temperature": convert_reading(
            data.get("field1"), "Temperature"
        ),
        "humidity": convert_reading(
            data.get("field2"), "Humidity"
        ),
        "pm1": convert_reading(
            data.get("field3"), "PM1.0"
        ),
        "pm25": convert_reading(
            data.get("field4"), "PM2.5"
        ),
        "pm10": convert_reading(
            data.get("field5"), "PM10"
        ),
        "co2": convert_reading(
            data.get("field6"), "CO2"
        ),
        "device_status": device_status,
        "last_updated": local_recorded_at.strftime(
            "%d %B %Y, %H:%M:%S"
        ),
    }
def fetch_recent_readings(results=30):
    """Retrieve recent ThingSpeak readings for dashboard charts."""

    channel_id = os.getenv("THINGSPEAK_CHANNEL_ID")
    read_api_key = os.getenv("THINGSPEAK_READ_API_KEY")

    if not channel_id or not read_api_key:
        raise ValueError(
            "ThingSpeak Channel ID or Read API Key is missing."
        )

    results = max(1, min(int(results), 100))

    url = (
        f"https://api.thingspeak.com/channels/"
        f"{channel_id}/feeds.json"
    )

    response = requests.get(
        url,
        params={
            "api_key": read_api_key,
            "results": results,
        },
        timeout=10,
    )

    response.raise_for_status()

    feeds = response.json().get("feeds", [])
    history = []

    for feed in feeds:
        try:
            recorded_at = datetime.fromisoformat(
                feed["created_at"].replace("Z", "+00:00")
            ).astimezone()

            history.append(
                {
                    "time": recorded_at.strftime("%H:%M"),
                    "temperature": convert_reading(
                        feed.get("field1"),
                        "Temperature",
                    ),
                    "humidity": convert_reading(
                        feed.get("field2"),
                        "Humidity",
                    ),
                    "pm25": convert_reading(
                        feed.get("field4"),
                        "PM2.5",
                    ),
                    "co2": convert_reading(
                        feed.get("field6"),
                        "CO2",
                    ),
                }
            )

        except (ValueError, KeyError):
            # Skip incomplete records instead of breaking the chart.
            continue

    return history