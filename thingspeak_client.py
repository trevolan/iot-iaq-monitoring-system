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